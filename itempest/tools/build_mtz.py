import exceptions
import netaddr

from tempest.common import waiters
from tempest_lib.common.utils import data_utils
import lib_networks as LN


# scope_id_list=[None, 'vdnscope-1', 'vdnscope-2', 'vdnscope-3']
# mtz = build_mtz.setup_mtz_simple(sun, 'mtz-s',
#       for_tenant=mars, scope_id_list=scop_id_list,
#       dns_nameservers=['10.34.35.11'], dns_search_domain='vmware.com')
def setup_mtz_simple(cmgr, x_name, **kwargs):
    x_name = x_name or data_utils.rand_name('mtz-i')
    wait4server_active = kwargs.pop('wait4servers', True)
    tenant_cmgr = kwargs.pop('for_tenant', None)
    if tenant_cmgr:
        tenant_id = tenant_cmgr.manager.credentials.tenant_id
    else:
        tenant_cmgr = cmgr
        tenant_id = kwargs.pop('tenant_id', None)
        if tenant_id:
            msg = "tenant_id not supported, use for_tenant=tenant_cmgr"
            raise exceptions.NotImplementedError(msg)
    scope_id_list = kwargs.pop('scope_id_list', [])
    mtz_ip = netaddr.IPNetwork(kwargs.pop('cidr', '10.199.1.0/24'))
    mask_bits = kwargs.pop('mask_bits', (mtz_ip.prefixlen + 3))
    cidr_list = [x for x in mtz_ip.subnet(mask_bits)]
    net_list = []
    for ix, scope_id in enumerate(scope_id_list):
        subnet_cidr = str(cidr_list[ix])
        name = x_name + ("-%d" % (ix + 1))
        network_subnet = create_mtz_networks(cmgr, scope_id, subnet_cidr,
                                             name=name, tenant_id=tenant_id,
                                             **kwargs)
        net_list.append(network_subnet)
    # server_create does not accept tenant_id, always use tenant_cmgr
    router = LN.create_router_and_add_interfaces(tenant_cmgr,
                                                 x_name + "-router",
                                                 net_list,
                                                 tenant_id=tenant_id)
    sg = LN.create_security_group_loginable(tenant_cmgr, x_name,
                                            tenant_id=tenant_id)
    security_group_id = sg['id']
    net_id_servers = {}
    for ix, (network, subnet) in enumerate(net_list):
        net_id = network['id']
        vm = LN.create_server_on_network(
            tenant_cmgr, net_id,
            security_group_name_or_id=security_group_id,
            server_name=network['name'])
        net_id_servers[net_id] = dict(server=vm,
                                      network=network, subnet=subnet)
    if wait4server_active:
        wait_for_servers_active(cmgr, net_id_servers)
    return (router, net_id_servers, sg)


def wait_for_servers_active(cmgr, net_id_servers):
    server_id_list = [v['server']['id'] for k, v in net_id_servers.items()]
    for server_id in server_id_list:
        waiters.wait_for_server_status(
            cmgr.manager.servers_client, server_id, 'ACTIVE')


def wait_for_servers_terminated(cmgr, net_id_servers):
    server_id_list = [v['server']['id'] for k, v in net_id_servers.items()]
    for server_id in server_id_list:
        waiters.wait_for_server_termination(
            cmgr.manager.servers_client, server_id)


def teardown_mtz_simple(cmgr, router, net_id_servers, sg):
    server_list = []
    for net_id, server in net_id_servers.items():
        server_id = server['server']['id']
        cmgr.nova('server-delete', server_id)
        server_list.append(server_id)
    # wait for all servers go away
    for server_id in server_list:
        waiters.wait_for_server_termination(cmgr.manager.servers_client,
                                            server_id)
    LN.delete_this_router(cmgr.manager, router)
    cmgr.qsvc('security-group-delete', sg['id'])


def create_mtz_networks(cmgr, scope_id, cidr, name=None, **kwargs):
    network_name = name or data_utils.rand_name('mtz-n')
    tenant_id = kwargs.get('tenant_id', None)
    if type(scope_id) in (str, unicode):
        network_cfg = {
            'provider:network_type': 'vxlan',
            'provider:physical_network': scope_id,
        }
    else:
        network_cfg = {}
    if tenant_id:
        network_cfg['tenant_id'] = tenant_id
    network = cmgr.qsvc('net-create', network_name, **network_cfg)
    subnet = cmgr.qsvc('subnet-create', network['id'], cidr,
                       name=network_name, **kwargs)
    network = cmgr.qsvc('net-show', network['id'])
    return (network, subnet)
