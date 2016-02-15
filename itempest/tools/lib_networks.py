import netaddr

from tempest_lib.common.utils import data_utils
from tempest.common import waiters
from tempest.common.utils.linux import remote_client


def create_security_group_loginable(cmgr, name, **kwargs):
    filters = dict(name=name)
    tenant_id = kwargs.pop('tenant_id', None)
    if tenant_id:
        filters['tenant_id'] = tenant_id
    try:
        sg = cmgr.qsvc('security-group-list', **filters)[0]
    except Exception:
        sg = cmgr.qsvc('security-group-create', name, tenant_id=tenant_id)
        create_security_group_ssh_rule(cmgr, sg['id'], tenant_id=tenant_id)
        create_security_group_icmp_rule(cmgr, sg['id'], tenant_id=tenant_id)
    return cmgr.qsvc('security-group-show', sg['id'])


def create_security_group_ssh_rule(cmgr, security_group_id, tenant_id=None):
    ssh_rule = dict(direction='ingress',
                    ethertype='IPv4', protocol='tcp',
                    port_range_min=22, port_range_max=22)
    return cmgr.qsvc('security-group-rule-create',
                     security_group_id,
                     tenant_id=tenant_id, **ssh_rule)


def create_security_group_icmp_rule(cmgr, security_group_id,
                                    tenant_id=None):
    icmp_rule = dict(direction='ingress',
                     ethertype='IPv4', protocol='icmp')
    return cmgr.qsvc('security-group-rule-create',
                     security_group_id,
                     tenant_id=tenant_id, **icmp_rule)


def create_router_and_add_interfaces(cmgr, name, net_list, **kwargs):
    tenant_id = kwargs.pop('tenant_id', None)
    name = name or data_utils.rand_name('itempz-r')
    router = cmgr.qsvc('router-create', name, tenant_id=tenant_id)
    cmgr.qsvc('router-gateway-set', router['id'],
              get_public_network_id(cmgr))
    for network, subnet in net_list:
        cmgr.qsvc('router-interface-add', router['id'], subnet['id'])
    return router


# for security_group_name_or_id, better using id
# server_craete does not honor tenant_id, so you need to use the cmgr that
# will be the owner of the server
def create_server_on_network(cmgr, network_id, server_name=None,
                             image_id=None, flavor_id=1,
                             security_group_name_or_id=None,
                             wait_on_boot=False, **kwargs):
    server_name = server_name or data_utils.rand_name('itempz-sv')
    security_group_name_or_id = security_group_name_or_id or 'default'
    network = cmgr.qsvc('net-show', network_id)
    create_kwargs = {
        'networks': [{'uuid': network['id']}],
        'security_groups': [{'name': security_group_name_or_id}],
    }
    image_id = get_image_id(cmgr, image_id)
    flavor_id = get_flavor_id(cmgr, flavor_id)
    create_kwargs.update(**kwargs)
    return cmgr.nova('server_create', server_name, image_id=image_id,
                     flavor_id=flavor_id, wait_on_boot=wait_on_boot,
                     **create_kwargs)


def create_floatingip_for_server(cmgr, server,
                                 public_network_id=None,
                                 port_id=None,
                                 **kwargs):
    if type(server) is not dict:
        server = cmgr.nova('server-show', server)
    server_id = server['id']
    public_network_id = public_network_id or get_public_network_id(cmgr)
    if port_id:
        ip4 = None
    else:
        port_id, ip4 = get_port_id_ipv4_of_server(cmgr, server_id)
    floatingip = cmgr.qsvc('floatingip-create', public_network_id,
                           port_id=port_id, fixed_ip_address=ip4,
                           **kwargs)
    return floatingip


def create_ssh_client(public_ip,
                      username='cirros', password='cubswin:)',
                      **kwargs):
    ssh_client = remote_client.RemoteClient(public_ip,
                                            username, password)
    return ssh_client


def get_port_id_ipv4_of_server(cmgr, server_id,
                               ip_addr=None, **kwargs):
    ports = cmgr.qsvc('port-list',
                      device_id=server_id, fixed_ip=ip_addr)
    # TODO(akang): assume only ONE from ports match server_id
    #              need to handle server given 1+ network.
    port0 = ports[0]
    for ip4 in port0['fixed_ips']:
        ip = ip4['ip_address']
        if netaddr.valid_ipv4(ip):
            return (port0['id'], ip)


def get_server_fixedips(cmgr, server):
    fip_list = []
    if type(server) is not dict:
        server = cmgr.nova('server-show', server)
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                        addr['OS-EXT-IPS:type'] == 'fixed'):
                fip_list.append(addr['addr'])
    return fip_list


def get_server_floatingips(cmgr, server):
    fips_list = []
    if type(server) is not dict:
        server = cmgr.nova('server-show', server)
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                        addr['OS-EXT-IPS:type'] == 'floating'):
                fips = cmgr.qsvc('floatingip-list',
                                 floating_ip_address=addr['addr'])
                if len(fips) > 0:
                    fips_list.append(fips)
    return fips_list


def delete_server_floatingips(cmgr, server):
    if type(server) is not dict:
        server = cmgr.nova('server-show', server)
    for fips in get_server_floatingips(cmgr, server):
        for fip in fips:
            cmgr.qsvc('floatingip_disassociate', fip['id'])
            cmgr.qsvc('floatingip-delete', fip['id'])


def delete_tenant_servers(cmgr, tenant_id=None, wait_for_termination=True,
                          **kwargs):
    server_id_list = []
    for server in cmgr.nova('server-list', detail=True):
        if tenant_id and server['tenant_id'] != tenant_id:
            # this works only cmgr as admin priveledge
            continue
        delete_server_floatingips(cmgr, server)
        cmgr.nova('server-delete', server['id'])
        server_id_list.append(server['id'])
    if wait_for_termination:
        for server_id in server_id_list:
            waiters.wait_for_server_termination(
                cmgr.manager.servers_client, server_id)
    else:
        return server_id_list


def delete_router_by_id(cmgr, router_id, **kwargs):
    routers = cmgr.qscv('router-list', id=router_id)
    if len(routers) != 1:
        return None
    return delete_this_router(cmgr, routers[0])


def delete_this_router(cmgr, router):
    router_id = router['id']
    cmgr.qsvc('router-delete-extra-routes', router_id)
    cmgr.qsvc('router-gateway-clear', router_id)
    ports = cmgr.qsvc('router-port-list', router_id)
    for port in ports:
        if port['device_owner'].find(':router_interface') > 0:
            if 'fixed_ips' in port:
                for fixed_ips in port['fixed_ips']:
                    if 'subnet_id' in fixed_ips:
                        cmgr.qsvc('router-interface-delete',
                                  router_id,
                                  fixed_ips['subnet_id'])
    return cmgr.qsvc('router-delete', router_id)


# cmgr with admin privilege may cause resources deleted you may not want!
def destroy_all_resources(cmgr, **kwargs):
    this_tenant_id = cmgr.manager.credentials.tenant_id
    tenant_id = kwargs.pop('tenant_id', this_tenant_id)
    filters = {'tenant_id': tenant_id}
    delete_tenant_servers(cmgr, **filters)
    # rm routers
    routers = cmgr.qsvc('router-list', **filters)
    for router in routers:
        if router['tenant_id']:
            delete_this_router(cmgr, router)
    # rm networks/subnets
    for network in cmgr.qsvc('net-list', **filters):
        cmgr.qsvc('net-delete', network['id'])
    # rm security-groups
    for sg in cmgr.qsvc('security-group-list', **filters):
        if sg['name'] != 'default':
            cmgr.qsvc('security-group-delete', sg['id'])


def get_public_network_id(cmgr, net_name=None):
    pub_net_list = cmgr.qsvc('net-external-list')
    if net_name:
        for pub_net in pub_net_list:
            if pub_net['name'] == net_name:
                return pub_net['id']
    else:
        return pub_net_list[0]['id']


def get_flavor_id(cmgr, flavor=None, image_name=None):
    if type(flavor) is int:
        return flavor
    if type(flavor) in (str, unicode):
        if flavor.isdigit():
            return int(flavor)
        for f in cmgr.nova('flavor-list'):
            if f['name'].find(flavor) >= 0:
                return int(f['id'])
    if image_name and image_name.find('cirros') >= 0:
        return 1
    return 2


def get_image_id(cmgr, image_name=None):
    image_list = cmgr.nova('image-list')
    image_name = image_name or 'cirros'
    for image in image_list:
        if image['name'] == image_name:
            return image['id']
    for image in image_list:
        if image['name'].find(image_name) >= 0:
            return image['id']
    return None