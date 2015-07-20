# Copyright 2015 OpenStack Foundation
# Copyright 2015 VMware.
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

import base64
import copy
import json
import os
import sys
import time
import traceback

from itempest.lib import cmd_neutron as Neutron
from itempest.lib import cmd_nova as Nova
from itempest.lib import utils as U


# e1 = SimpleTenantNetwork(earth_mgr, 'earth_topo.json', prefix=True)
# e2 = SimpleTenantNetwork(earth_mgr, 'earth_topo.json', prefix='earth2')
# e3 = SimpleTenantNetwork(earth_mgr, 'earth_topo.json', prefix='earth3')
class SimpleTenantNetworks(object):
    def __init__(self, client_mgr, json_file, **kwargs):
        self._client_mgr = client_mgr
        self._cfg_file = json_file
        self.load_tenant_topo(json_file)
        verbose = kwargs.pop('verbose', True)
        self.get_cfg_options(kwargs)
        self.qsvc = U.command_wrapper(self._client_mgr, Neutron,
                                      log_cmd="OS-Neutron",
                                      verbose=verbose)
        self.nova = U.command_wrapper(self._client_mgr, Nova,
                                      nova_flavor=True,
                                      log_cmd="OS-Nova",
                                      verbose=verbose)
        self.security_groups = {}
        self.networks = {}
        self.routers = {}
        self.servers = {}

    def get_cfg_options(self, kwargs):
        self.prepare_prefix_name(
            kwargs.pop('prefix_name', kwargs.pop("prefix", None)))
        self.prepare_suffix_name(
            kwargs.pop('suffix_name', kwargs.pop("suffix", None)))
        self.no_servers =  kwargs.pop('no_server',
                                      kwargs.pop('no_servers', False))
        self.router_cfg_options = kwargs.pop("router_options", None)

    def prepare_prefix_name(self, with_name=None):
        self.prefix_name = with_name
        if self.prefix_name and type(self.prefix_name) is not str:
            self.prefix_name = self._client_mgr.credentials.tenant_name

    def prepare_suffix_name(self, with_name=None):
        self.suffix_name = with_name
        if self.suffix_name and type(self.suffix_name) is not str:
            self.suffix_name = self._client_mgr.credentials.username

    def load_tenant_topo(self, json_file=None):
        json_file = json_file or self._cfg_file
        self._tenant_topo = json.loads(open(json_file, 'r').read())
        self.dirname_json_file = os.path.dirname(json_file)


    def build(self):
        t0 = time.time()
        self.b_security_groups()
        self.b_networks()
        self.b_routers()
        self.b_servers()
        return (time.time() - t0)

    def unbuild(self):
        t0 = time.time()
        self.d_servers()
        self.d_routers()
        self.d_networks()
        self.d_security_groups()
        return (time.time() - t0)

    # wipeout all resources belog to this tenant!
    def wipeout(self, tenant_id=None, force_rm_fip=True):
        t0 = time.time()
        kwargs = {}
        if tenant_id:
            kwargs['tenant_id'] = tenant_id
        # delete servers
        # self.nova('destroy-my-servers', **kwargs)
        for server in self.nova('server-list'):
            d_server(self.nova, server['id'], self.qsvc)
        time.sleep(3.0)
        # detroy tenant networks+routers
        self.qsvc('destroy-myself',
                  force_rm_fip=force_rm_fip,
                  **kwargs)
        return (time.time() - t0)

    def _g_config(self, otypes):
        return pop_config(otypes, self._tenant_topo)

    # build resources
    def b_networks(self, networks_cfg=None):
        self.networks = {}
        self.subnets = {}
        networks_cfg = networks_cfg or self.g_networks_cfg()
        self.networks, self.subnets = c_networks(
            self.qsvc, networks_cfg, self.prefix_name, self.suffix_name)

    def b_routers(self, routers=None):
        self.routers = {}
        routers_cfg = self.g_routers_cfg()
        for router in routers_cfg:
            if self.router_cfg_options:
                router.update(self.router_cfg_options)
            rtr = c_router(self.qsvc, router,
                           prefix_name=self.prefix_name,
                           suffix_name=self.suffix_name)
            self.routers[rtr['name']] = rtr

    def b_servers(self, servers_cfg=None):
        if self.no_servers:
            return None
        servers_cfg = servers_cfg or self.g_servers_cfg()
        self.servers = c_servers(self.nova, self.qsvc, servers_cfg,
                                 prefix_name=self.prefix_name,
                                 suffix_name=self.suffix_name)

    def b_security_groups(self, sg_cfg=None):
        security_groups_cfg = sg_cfg or self.g_security_groups()
        self.security_groups = c_security_groups(self.qsvc,
                                                 security_groups_cfg)

    # get resources' build config
    def g_networks_cfg(self):
        networks = self._g_config(('networks', 'network'))
        return networks

    def g_routers_cfg(self):
        routers = self._g_config(('routers', 'router'))
        return routers

    def g_servers_cfg(self):
        s_opt = self.g_server_options_cfg()
        servers = self._g_config(('servers', 'server'))
        servers_cfg = []
        for s_cfg in servers:
            server_cfg = copy.deepcopy(s_opt)
            server_cfg.update(s_cfg)
            servers_cfg.append(server_cfg)
        return servers_cfg

    def g_server_options_cfg(self):
        server_opts = self._g_config(('server_options', 'server-options'))
        s_opts = copy.deepcopy(server_opts)
        for s_opt in s_opts:
            if 'user_data' in s_opt:
                if not os.path.isabs(s_opt['user_data']):
                    s_opt['user_data'] = os.path.realpath(
                        os.path.join(self.dirname_json_file,
                                     s_opt['user_data']))
                data = open(s_opt['user_data'], 'r').read()
                s_opt['user_data'] = base64.standard_b64encode(data)
        if len(s_opts) > 0:
            return s_opts[0]
        return {}

    def g_security_groups(self):
        security_groups = self._g_config(
            ('security-groups', 'security_groups', 'security-group',
             'security_group'))
        sg_rules = self._g_config(
            ('security-group-rules', 'security_group_rules'))
        sg_rules_cfg = {}
        for rule in sg_rules:
            rule_copy = copy.deepcopy(rule)
            name = rule_copy.pop('name')
            sg_rules_cfg[name] = rule_copy
        security_groups_cfg = {}
        for sg in security_groups:
            name = sg['name']
            security_groups_cfg[name] = []
            for rule_name in sg['rules']:
                rule_cfg = sg_rules_cfg[rule_name]
                security_groups_cfg[name].append(rule_cfg)
        return security_groups_cfg

    # delete resources
    def d_servers(self):
        for nid, server in self.servers.items():
            d_server(self.nova, server['id'], self.qsvc)

    def d_routers(self):
        for nid, router in self.routers.items():
            self.qsvc('d-this-router', router)

    def d_networks(self):
        for nid, network in self.networks.items():
            self.qsvc('net-delete', network['id'])

    def d_security_groups(self):
        for nid, sg in self.security_groups.items():
            self.qsvc('security-group-delete', sg['id'])

    def a_floatingip_to_server(self, server_id):
        return c_floatingip_to_server(self.qsvc, server_id)

    def d_floatingip_from_server(self, server_id):
        server = self.nova('server-show', server_id)
        return d_server_floatingip(self.qsvc, server)

    def a_security_group_to_server(self, server_id, security_group_name,
                                   on_interface=None):
        pass

    def d_security_group_from_server(self, server_id, security_group_name,
                                     on_interface=None):
        pass


def adjust_name(name, prefix_name=None, suffix_name=None):
    if prefix_name:
        name = prefix_name + "-" + name
    if suffix_name:
        name = name + "-" + suffix_name
    return name


def c_networks(qsvc, networks_cfg, prefix_name=None, suffix_name=None):
    networks = {}
    subnets = {}
    for network in networks_cfg:
        name = adjust_name(network.pop('name'),
                           prefix_name, suffix_name)
        subnets_cfg = pop_config(['subnet', 'subnets'], network)
        nets = qsvc('net-list', name=name)
        if len(nets) < 1:
            net = qsvc('net-create', name, **network)
        else:
            net = nets[0]
        networks[name] = qsvc('net-show', net['id'])
        subnets.update(c_subnets(qsvc, networks[name]['id'], subnets_cfg,
                                 prefix_name=prefix_name,
                                 suffix_name=suffix_name))
    return (networks, subnets)


def c_subnets(qsvc, network_id, subnets_cfg,
              prefix_name=None, suffix_name=None):
    subnets = {}
    for subnet in subnets_cfg:
        name = adjust_name(subnet['name'],
                           prefix_name, suffix_name)
        cidr = subnet.pop('cidr')
        subnet['name'] = name
        snets = qsvc('subnet-list', name=name)
        if len(snets) < 1:
            snet = qsvc('subnet-create', network_id, cidr, **subnet)
        else:
            snet = snets[0]
        subnets[name] = qsvc('subnet-show', snet['id'])
    return subnets


def c_router(qsvc, router_cfg, prefix_name=None, suffix_name=None):
    name = adjust_name(router_cfg.pop('name'), prefix_name, suffix_name)
    rtrs = qsvc('router-list', name=name)
    if len(rtrs) > 0:
        return qsvc('router-show', rtrs[0]['id'])
    else:
        if_names = router_cfg.pop('interfaces', [])
        gw_if = router_cfg.pop('gateway', None)
        gw_kwargs = {}
        if 'enable_snat' in router_cfg:
            gw_kwargs['enable_snat'] = router_cfg.pop('enable_snat')
        rtr = qsvc('router-create', name, **router_cfg)
        rtr_set_gateway(qsvc, rtr['id'], gateway_if=gw_if, **gw_kwargs)
        rtr = rtr_add_interfaces_by_name(qsvc, rtr['id'], if_names,
                                         prefix_name=prefix_name,
                                         suffix_name=suffix_name)
        return rtr


def rtr_set_gateway(qsvc, rtr_id, gateway_if=None):
    if gateway_if:
        xnet = qsvc('net-external-list', name=gateway_if)[0]
    else:
        xnet = qsvc('net-external-list')[0]
    qsvc('router-gateway-set', rtr_id, xnet['id'])
    return qsvc('router-show', rtr_id)


def rtr_set_gateway_snat(qsvc, rtr_id, gateway_if, enable_snat):
    qsvc('router-gateway-set', rtr_id, gateway_if,
         enable_snat=enable_snat)
    return qsvc('router-show', rtr_id)


def rtr_add_interfaces_by_name(qsvc, rtr_id, if_names,
                               prefix_name=None, suffix_name=None):
    for if_name in if_names:
        if_name = adjust_name(if_name, prefix_name, suffix_name)
        networks = qsvc('net-list', name=if_name)
        subnet_id = networks[0]['subnets'][0]
        qsvc('router-interface-add', rtr_id, subnet_id)
    return qsvc('router-show', rtr_id)


def rtr_add_interfaces(qsvc, rtr_id, networks):
    for net_name in networks.keys():
        network = qsvc('network-list', name=net_name)
        subnet_id = network[0]['subnets'][0]
        qsvc('router-interface-add', rtr_id, subnet_id)
    return qsvc('router-show', rtr_id)


def c_security_groups(qsvc, security_groups_cfg):
    security_groups = {}
    for sg_name, sg_rules_cfg in security_groups_cfg.items():
        sgs = qsvc('security-group-list', name=sg_name)
        if len(sgs) < 1:
            # create this security-group only it does not exist
            sg = qsvc('security-group-create', sg_name)
            for rule_cfg in sg_rules_cfg:
                qsvc('security-group-rule-create', sg['id'], **rule_cfg)
        else:
            sg = sgs[0]
        security_groups[sg_name] = qsvc('security-group-show', sg['id'])
    return security_groups


def c_servers(nova, qsvc, servers_cfg,
              prefix_name=None, suffix_name=None,
              security_groups=None, wait_on_boot=False):
    from_images = nova('image-list')
    from_flavors = nova('flavor-list')
    servers = {}
    for serv_cfg in servers_cfg:
        server = boot_server(nova, qsvc, serv_cfg,
                             from_images, from_flavors,
                             prefix_name=prefix_name,
                             security_groups=security_groups,
                             wait_on_boot=wait_on_boot)
        servers[server['name']] = server
    return servers


def boot_server(nova, qsvc, server_cfg,
                from_images=None, from_flavors=None,
                prefix_name=None, suffix_name=None,
                security_groups=None, wait_on_boot=False):
    sv_name = adjust_name(server_cfg.pop('name'), prefix_name, suffix_name)
    sg_names = server_cfg.pop('security_groups', None)
    if sg_names:
        security_groups = [{'name': x} for x in sg_names]
    servs = nova('server-list-with-detail', name=sv_name)
    # nova name match is regexp, potentially you get more than you request
    for sv in servs:
        if sv_name == sv['name']:
            return sv
    from_images = from_images or nova('image-list')
    from_flavors = from_flavors or nova('flavor-list')
    sv_interfaces = pop_config(['interface', 'interfaces'], server_cfg)
    networks = f_server_interfaces(qsvc, sv_interfaces,
                                   prefix_name, suffix_name)
    image_id = get_image_id(server_cfg.pop('image'), from_images)
    flavor_id = get_flavor_id(server_cfg.pop('flavor'), from_flavors)
    return nova('c-server-on-interface', networks, image_id,
                name=sv_name, flavor=flavor_id,
                security_groups=security_groups,
                wait_on_boot=wait_on_boot, **server_cfg)


def f_server_interfaces(qsvc, interface_names, prefix_name, suffix_name):
    if type(interface_names) in (str, unicode):
        interface_names = [interface_names]
    networks = []
    for if_name in interface_names:
        if_name = adjust_name(if_name, prefix_name, suffix_name)
        svs = qsvc('net-list', name=if_name)
        networks.extend(svs)
    return networks


def c_floatingip_to_server(qsvc, server_id, public_id=None, **kwargs):
    public_network_id = public_id or qsvc('net-external-list')[0]
    floatingip = qsvc('floatingip-create-for-server',
                      public_network_id['id'], server_id)
    return floatingip


def d_server(nova, server_id, qsvc=None):
    try:
        sv = nova('server-show', server_id)
        d_server_floatingip(qsvc, sv) if qsvc else None
        return nova('server-delete', server_id)
    except Exception:
        pass


def d_server_floatingip(qsvc, server):
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                addr['OS-EXT-IPS:type'] == u'floating'):
                fip = qsvc('floatingip-list',
                           floating_network_address=addr['addr'])
                qsvc('floatingip_disassociate', fip[0]['id'])
                qsvc('floatingip-delete', fip[0]['id'])


def get_image_id(image_name, from_images, use_any_ifnot_exist=True):
    for m in from_images:
        if m['name'] == image_name:
            return m['id']
    if use_any_ifnot_exist:
        return from_images[0]['id']
    else:
        return None


def get_flavor_id(flavor, from_flavors):
    if type(flavor) is int:
        return flavor
    if type(flavor) is str and flavor.is_digit():
        return int(flavor)
    for f in from_flavors:
        if f['name'] == flavor:
            return int(f['id'])
    return 1


def get_subnet_name(network_name):
    ix = network_name.find("-network")
    if ix > 1:
        subname = network_name[:ix]
        return subname + "-subnet"
    return network_name + "-sub"


def pop_config(otypes, from_topo_cfg):
    for otype in otypes:
        if otype in from_topo_cfg:
            # the reason to pop is to remove attributes that should not be
            # in the config as we just pass whatever defined in the conf.
            cfg = from_topo_cfg.pop(otype)
            if type(cfg) is dict:
                return [cfg]
            return cfg
    return []


def get_last_trace():
    return traceback.extract_tb(sys.last_traceback)


def print_trace(tracemsg=None):
    tracemsg = tracemsg or get_last_trace()
    for msg in tracemsg:
        print("line#%s @file: %s\n  %s\n    %s" %
              (msg[1], msg[0], msg[2], msg[3]))
