# Copyright 2015 OpenStack Foundation
# Copyright 2015 VMware Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from itempest.lib import cmd_neutron as N

# user defined commands
def c_external_network(mgr_or_client,
                       name=None,
                       shared=True, **kwargs):
    kwargs['shared'] = shared
    kwargs['router:external'] = True
    return N.net_create(mgr_or_client,
                        name=name,
                        **kwargs)


def c_vlan_network(mgr_or_client,
                   vlan_id=888, name=None,
                   shared=True, **kwargs):
    kwargs.update({
        'shared': shared,
        'provider:network_type': 'vlan',
        'provider:segmentation_id': vlan_id})
    name = name or N.data_utils.rand_name('vlan-%s-network' % vlan_id)
    return N.net_create(mgr_or_client,
                        name=name,
                        **kwargs)


def c_flat_network(mgr_or_client,
                   name=None,
                   shared=True, **kwargs):
    kwargs.update({
        'shared': shared,
        'provider:network_type': 'flat'})
    name = name or N.data_utils.rand_name('flat-network')
    return N.net_create(mgr_or_client,
                        name=name,
                        **kwargs)


def c_security_group_loginable(mgr_or_client, name, **kwargs):
    sg = security_group_create(mgr_or_client, name)
    c_security_group_ssh_rule(mgr_or_client, sg['id'])
    c_security_group_icmp_rule(mgr_or_client, sg['id'])
    return security_group_show(mgr_or_client, sg['id'])


def c_security_group_ssh_rule(mgr_or_client, security_group_id):
    ssh_rule = dict(direction='ingress', ethertype='IPv4', protocol='tcp',
                    port_range_min=22, port_range_max=22)
    return N.security_group_rule_create(mgr_or_client,
                                        security_group_id, **ssh_rule)


def c_security_group_icmp_rule(mgr_or_client, security_group_id):
    icmp_rule = dict(direction='ingress', ethertype='IPv4', protocol='icmp')
    return N.security_group_rule_create(mgr_or_client,
                                        security_group_id, **icmp_rule)


# delete router after clearing gateway and deleting sub-interfaces
def d_router(mgr_or_client, router_id, **kwargs):
    routers = N.router_list(mgr_or_client, id=router_id)
    if len(routers) != 1:
        return None
    return d_this_router(mgr_or_client, routers[0])


# NOTE: if attributes can only be manipulated by ADMIN, then
#       mgr_or_client needs to have admin-priv.
def d_this_router(mgr_or_client, router):
    router_id = router['id']
    N.router_delete_extra_routes(mgr_or_client, router_id)
    N.router_gateway_clear(mgr_or_client, router_id)
    ports = N.router_port_list(mgr_or_client, router_id)
    for port in ports:
        if port['device_owner'].find(':router_interface') > 0:
            if 'fixed_ips' in port:
                for fixed_ips in port['fixed_ips']:
                    if 'subnet_id' in fixed_ips:
                        N.router_interface_delete(mgr_or_client,
                                                  router_id,
                                                  fixed_ips['subnet_id'])
    return N.router_delete(mgr_or_client, router_id)


# qsvc('destroy-myself', name_startswith='page2-')
# To delete network resources of tenant=Mars:
# mars = utils.fgrep(keyAdmin('tenant-list'), name='Mars')[0]
# qsvcAdmin('destroy-myself', tenant_id=mars['id'])
def destroy_myself(mgr_or_client, **kwargs):
    return d_myself(mgr_or_client, **kwargs)


# client's tenant_id used to search for resources to be deleted.
def d_myself(mgr_or_client, **kwargs):
    skip_fip = kwargs.pop('skip_fip',
                          kwargs.pop('skip_floatingip', False))
    force_rm_fip = kwargs.pop('force_rm_fip', False)
    if force_rm_fip:
        skip_fip = False
    spattern = N.mdata.get_name_search_pattern(**kwargs)
    net_client = N._g_net_client(mgr_or_client)
    tenant_id = kwargs.pop('tenant_id', net_client.tenant_id)
    # rm floatingips: be aware that VMs' might have FIP attached
    # if fail, caller of d_myself should sleep then retry again
    if not skip_fip:
        # TODO(akang): no name attributes in floatingip
        # for now, delete fip if it is not ACTIVE status
        for fip in N.floatingip_list(mgr_or_client, tenant_id=tenant_id):
            if force_rm_fip or fip['status'] != 'ACTIVE':
                N.floatingip_delete(mgr_or_client, fip['id'])
    # rm routers
    routers = N.router_list(mgr_or_client, tenant_id=tenant_id)
    for router in routers:
        if N.mdata.is_in_spattern(router['name'], spattern):
            d_this_router(mgr_or_client, router)
    # rm networks/subnets
    for network in N.network_list(mgr_or_client, tenant_id=tenant_id):
        if N.mdata.is_in_spattern(network['name'], spattern):
            N.network_delete(mgr_or_client, network['id'])

    for sg in N.security_group_list(mgr_or_client, tenant_id=tenant_id):
        if (N.mdata.is_in_spattern(sg['name'], spattern) and
                sg['name'] not in ['default']):
            N.security_group_delete(mgr_or_client, sg['id'])


def g_port_id_ipv4_of_server(mgr_or_client, server_id,
                             ip_addr=None, **kwargs):
    ports = N.port_list(mgr_or_client,
                        device_id=server_id, fixed_ip=ip_addr)
    # TODO(akang): assume only ONE from ports match server_id
    #              need to handle server given 1+ network.
    port0 = ports[0]
    for ip4 in port0['fixed_ips']:
        ip = ip4['ip_address']
        if N.netaddr.valid_ipv4(ip):
            return (port0['id'], ip)


def g_ports_of_server(mgr_or_client, server_id, **kwargs):
    ports = N.port_list(mgr_or_client, device_id=server_id)
    return ports


# nova has method to add security-group to server
# nova('server-add-security-group', server_id, name_of_security_group)
def u_server_security_group(mgr_or_client, server_id, security_group_ids,
                            port_ids=None, fixed_ip=None, action=None):
    if port_ids:
        if type(port_ids) in (unicode, str):
            port_ids = [port_ids]
    else:
        port_ids = [p['id'] for p in g_ports_of_server(
            mgr_or_client, server_id, fixed_ip=fixed_ip)]
    if not type(security_group_ids) in [list, tuple]:
        security_group_ids = [security_group_ids]
    ports = []
    sg_key = 'security_groups'
    for port_id in port_ids:
        if action:
            port_info = N.port_show(mgr_or_client, port_id)
            orig_sgs = port_info[sg_key] if sg_key in port_info else []
            if action in (1, 'add'):
                new_security_group_ids = list(
                    set(orig_sgs) | set(security_group_ids))
            elif action in (2, 'del', 'delete'):
                new_security_group_ids = list(
                    set(orig_sgs) - set(security_group_ids))
        else:
            new_security_group_ids = security_group_ids
        ports.append(N.port_update(
            mgr_or_client, port_id,
            security_groups=new_security_group_ids))
    return ports
