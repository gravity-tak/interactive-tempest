
import netaddr

from itempest.commands import cmd_neutron_u1 as UQ
from tempest.common import waiters
from tempest_lib.common.utils import data_utils
import lib_networks as LN


# scope_id_list=['vdnscope-1', 'vdnscope-2', 'vdnscope-3']
# mtz = build_mtz.setup_mtz_simple(sun, 'mtz-s', scope_id_list=scop_id_list)
def setup_mtz_simple(cmgr, x_name, **kwargs):
    x_name = x_name or data_utils.rand_name('mtz-i')
    scope_id_list = kwargs.pop('scope_id_list', [])
    mtz_ip = netaddr.IPNetwork(kwargs.pop('cidr', '10.199.1.0/24'))
    mask_bits = kwargs.pop('mask_bits', (mtz_ip.prefixlen + 3))
    cidr_list = [x for x in mtz_ip.subnet(mask_bits)]
    net_list = []
    for ix, scope_id in enumerate(scope_id_list):
        subnet_cidr = str(cidr_list[ix])
        name = x_name + ("-%d" % (ix + 1))
        network_subnet = create_mtz_networks(cmgr, scope_id, subnet_cidr,
                                             name=name)
        net_list.append(network_subnet)
    router = LN.create_router_and_add_interfaces(cmgr, x_name+"-router",
                                              net_list)
    sg = UQ.create_security_group_loginable(cmgr.manager, x_name)
    servers = {}
    for ix, (network, subnet) in enumerate(net_list):
        net_id = network['id']
        vm = LN.create_server_on_network(
            cmgr, net_id, security_group_name_or_id=sg['name'],
            server_name=x_name+("-%d" % ix))
        servers[net_id] = dict(server=vm,
                               network=network, subnet=subnet)
    return (router, servers, sg)


def teardown_mtz_simple(cmgr, router, servers, sg):
    server_list = []
    for net_id, server in servers.items():
        server_id = server['server']['id']
        cmgr.nova('server-delete', server_id)
        server_list.append(server_id)
    # wait for all servers go away
    for server_id in server_list:
        waiters.wait_for_server_termination(cmgr.manager.servers_client,
                                            server_id)
    UQ.delete_this_router(cmgr.manager, router)
    cmgr.qsvc('security-group-delete', sg['id'])


def create_mtz_networks(cmgr, scope_id, cidr, **kwargs):
    network_name = (kwargs.pop('name', None) or
                    data_utils.rand_name('mtz-n'))
    tenant_id = kwargs.get('tenant_id', None)
    network_cfg = {
        'name': network_name,
        'provider:network_type': 'vxlan',
        'provider:physical_network': scope_id,
    }
    if tenant_id:
        network_cfg['tenant_id'] = tenant_id
    network = cmgr.qsvc('net-create', **network_cfg)
    subnet = cmgr.qsvc('subnet-create', network['id'], cidr,
                       name=network_name, **kwargs)
    network = cmgr.qsvc('net-show', network['id'])
    return (network, subnet)

