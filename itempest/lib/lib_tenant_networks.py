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
#    distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See
#  the
#    License for the specific language governing permissions and limitations
#    under the License.


def create_networks(cli_mgr, networks_cfg,
                    prefix_name=None, suffix_name=None):
    networks = {}
    subnets = {}
    for network in networks_cfg:
        name = _adjust_name(network.pop('name'),
                           prefix_name, suffix_name)
        subnets_cfg = _pop_config(['subnet', 'subnets'], network)
        nets = cli_mgr.qsvc('net-list', name=name)
        if len(nets) < 1:
            net = cli_mgr.qsvc('net-create', name, **network)
        else:
            net = nets[0]
        networks[name] = cli_mgr.qsvc('net-show', net['id'])
        subnets.update(
            create_subnets(cli_mgr.qsvc, networks[name]['id'], subnets_cfg,
                           prefix_name=prefix_name,
                           suffix_name=suffix_name))
    return (networks, subnets)


def create_subnets(cli_mgr, network_id, subnets_cfg,
                   prefix_name=None, suffix_name=None):
    subnets = {}
    for subnet in subnets_cfg:
        name = _adjust_name(subnet['name'],
                           prefix_name, suffix_name)
        cidr = subnet.pop('cidr')
        subnet['name'] = name
        snets = cli_mgr.qsvc('subnet-list', name=name)
        if len(snets) < 1:
            snet = cli_mgr.qsvc('subnet-create', network_id, cidr, **subnet)
        else:
            snet = snets[0]
        subnets[name] = cli_mgr.qsvc('subnet-show', snet['id'])
    return subnets


def create_router(cli_mgr, router_cfg, prefix_name=None, suffix_name=None):
    name = _adjust_name(router_cfg.pop('name'), prefix_name, suffix_name)
    rtrs = cli_mgr.qsvc('router-list', name=name)
    if len(rtrs) > 0:
        return cli_mgr.qsvc('router-show', rtrs[0]['id'])
    else:
        if_names = router_cfg.pop('interfaces', [])
        gw_if = router_cfg.pop('gateway', None)
        gw_kwargs = {}
        if 'enable_snat' in router_cfg:
            gw_kwargs['enable_snat'] = router_cfg.pop('enable_snat')
        rtr = cli_mgr.qsvc('router-create', name, **router_cfg)
        set_router_gateway(cli_mgr.qsvc, rtr['id'],
                           gateway_if=gw_if, **gw_kwargs)
        rtr = add_router_interfaces_by_name(cli_mgr.qsvc, rtr['id'],
                                            if_names,
                                            prefix_name=prefix_name,
                                            suffix_name=suffix_name)
        return rtr


def set_router_gateway(cli_mgr, rtr_id, gateway_if=None):
    if gateway_if:
        xnet = cli_mgr.qsvc('net-external-list', name=gateway_if)[0]
    else:
        xnet = cli_mgr.qsvc('net-external-list')[0]
    cli_mgr.qsvc('router-gateway-set', rtr_id, xnet['id'])
    return cli_mgr.qsvc('router-show', rtr_id)


def set_router_gateway_snat(cli_mgr, rtr_id, gateway_if, enable_snat):
    cli_mgr.qsvc('router-gateway-set', rtr_id, gateway_if,
         enable_snat=enable_snat)
    return cli_mgr.qsvc('router-show', rtr_id)


def add_router_interfaces_by_name(cli_mgr, rtr_id, if_names,
                                  prefix_name=None, suffix_name=None):
    for if_name in if_names:
        if_name = _adjust_name(if_name, prefix_name, suffix_name)
        networks = cli_mgr.qsvc('net-list', name=if_name)
        subnet_id = networks[0]['subnets'][0]
        cli_mgr.qsvc('router-interface-add', rtr_id, subnet_id)
    return cli_mgr.qsvc('router-show', rtr_id)


def add_router_interfaces(cli_mgr, rtr_id, networks):
    for net_name in networks.keys():
        network = cli_mgr.qsvc('network-list', name=net_name)
        subnet_id = network[0]['subnets'][0]
        cli_mgr.qsvc('router-interface-add', rtr_id, subnet_id)
    return cli_mgr.qsvc('router-show', rtr_id)


def create_security_groups(cli_mgr, security_groups_cfg):
    security_groups = {}
    for sg_name, sg_rules_cfg in security_groups_cfg.items():
        sgs = cli_mgr.qsvc('security-group-list', name=sg_name)
        if len(sgs) < 1:
            # create this security-group only it does not exist
            sg = cli_mgr.qsvc('security-group-create', sg_name)
            for rule_cfg in sg_rules_cfg:
                cli_mgr.qsvc('security-group-rule-create', sg['id'],
                             **rule_cfg)
        else:
            sg = sgs[0]
        security_groups[sg_name] = cli_mgr.qsvc('security-group-show',
                                                sg['id'])
    return security_groups


def create_servers(cli_mgr, servers_cfg,
                   prefix_name=None, suffix_name=None,
                   security_groups=None, wait_on_boot=False):
    from_images = cli_mgr.nova('image-list')
    from_flavors = cli_mgr.nova('flavor-list')
    servers = {}
    for serv_cfg in servers_cfg:
        server = boot_server(cli_mgr, serv_cfg,
                             from_images, from_flavors,
                             prefix_name=prefix_name,
                             security_groups=security_groups,
                             wait_on_boot=wait_on_boot)
        servers[server['name']] = server
    return servers


def boot_server(cli_mgr, server_cfg,
                from_images=None, from_flavors=None,
                prefix_name=None, suffix_name=None,
                security_groups=None, wait_on_boot=False):
    sv_name = _adjust_name(server_cfg.pop('name'), prefix_name, suffix_name)
    sg_names = server_cfg.pop('security_groups', None)
    if sg_names:
        security_groups = [{'name': x} for x in sg_names]
    servs = cli_mgr.nova('server-list-with-detail', name=sv_name)
    # cli_mgr.nova name match is regexp,
    # potentially you get more than you request
    for sv in servs:
        if sv_name == sv['name']:
            return sv
    from_images = from_images or cli_mgr.nova('image-list')
    from_flavors = from_flavors or cli_mgr.nova('flavor-list')
    sv_interfaces = _pop_config(['interface', 'interfaces'], server_cfg)
    networks = find_server_interfaces(cli_mgr, sv_interfaces,
                                      prefix_name, suffix_name)
    image_id = _get_image_id(server_cfg.pop('image'), from_images)
    flavor_id = _get_flavor_id(server_cfg.pop('flavor'), from_flavors)
    return cli_mgr.nova('create-server-on-interface', networks, image_id,
                name=sv_name, flavor=flavor_id,
                security_groups=security_groups,
                wait_on_boot=wait_on_boot, **server_cfg)


def find_server_interfaces(cli_mgr, interface_names,
                           prefix_name, suffix_name):
    if type(interface_names) in (str, unicode):
        interface_names = [interface_names]
    networks = []
    for if_name in interface_names:
        if_name = _adjust_name(if_name, prefix_name, suffix_name)
        svs = cli_mgr.qsvc('net-list', name=if_name)
        networks.extend(svs)
    return networks


def create_floatingip_to_server(cli_mgr, server_id,
                                public_id=None, security_group_id=None,
                                **kwargs):
    public_network_id = public_id or cli_mgr.qsvc('net-external-list')[0]
    action = kwargs.pop('action', 'add')
    floatingip = cli_mgr.qsvc('create-floatingip-for-server',
                      public_network_id['id'], server_id)
    if security_group_id:
        cli_mgr.qsvc('update-port-security-group', floatingip['port_id'],
             security_group_id, action=action)
    return floatingip


def create_floatingip_on_interface(cli_mgr, server_id, net_id,
                                   public_id=None):
    pass


def delete_server(cli_mgr, server_id):
    try:
        sv = cli_mgr.nova('server-show', server_id)
        delete_server_floatingip(cli_mgr, sv)
        return cli_mgr.nova('server-delete', server_id)
    except Exception:
        pass


def delete_server_floatingip(cli_mgr, server):
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                    addr['OS-EXT-IPS:type'] == u'floating'):
                fip = cli_mgr.qsvc('floatingip-list',
                           floating_network_address=addr['addr'])
                cli_mgr.qsvc('floatingip_disassociate', fip[0]['id'])
                cli_mgr.qsvc('floatingip-delete', fip[0]['id'])


# utilities
def _adjust_name(name, prefix_name=None, suffix_name=None):
    if prefix_name:
        name = prefix_name + "-" + name
    if suffix_name:
        name = name + "-" + suffix_name
    return name

def _get_image_id(image_name, from_images, use_any_ifnot_exist=True):
    for m in from_images:
        if m['name'] == image_name:
            return m['id']
    if use_any_ifnot_exist:
        return from_images[0]['id']
    else:
        return None


def _get_flavor_id(flavor, from_flavors):
    if type(flavor) is int:
        return flavor
    if type(flavor) is str and flavor.is_digit():
        return int(flavor)
    for f in from_flavors:
        if f['name'] == flavor:
            return int(f['id'])
    return 1


def _get_subnet_name(network_name):
    ix = network_name.find("-network")
    if ix > 1:
        subname = network_name[:ix]
        return subname + "-subnet"
    return network_name + "-sub"


def _pop_config(otypes, from_topo_cfg):
    for otype in otypes:
        if otype in from_topo_cfg:
            # the reason to pop is to remove attributes that should not be
            # in the config as we just pass whatever defined in the conf.
            cfg = from_topo_cfg.pop(otype)
            if type(cfg) is dict:
                return [cfg]
            return cfg
    return []
