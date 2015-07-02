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
from itempest.lib import cmd_glance as Glance
from itempest.lib import utils as U


# earth1 = SimpleTenantNetwork(earth_mgr, 'earth_topo.json', prefix_name=True)
# earth2 = SimpleTenantNetwork(earth_mgr, 'earth_topo.json', prefix_name='earth2')
# earth3 = SimpleTenantNetwork(earth_mgr, 'earth_topo.json', prefix_name='earth3')
class SimpleTenantNetworks(object):
    def __init__(self, client_mgr, json_file, **kwargs):
        self._client_mgr = client_mgr
        self._cfg_file = json_file
        self.prepare_prefix_name(kwargs.pop('prefix_name', None))
        self.prepare_suffix_name(kwargs.pop('suffix_name', None))
        log_cmd = kwargs.pop('log_cmd', False)
        verbose = kwargs.pop('verbose', True)
        self.load_tenant_topo(json_file)
        self.qsvc = U.command_wrapper(self._client_mgr, Neutron,
                                      log_cmd=log_cmd,
                                      verbose=verbose)
        self.nova = U.command_wrapper(self._client_mgr, Nova,
                                      nova_flavor=True,
                                      log_cmd=log_cmd,
                                      verbose=verbose)
        self.security_groups = {}
        self.networks = {}
        self.routers = {}
        self.servers = {}

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
    def wipeout(self):
        t0 = time.time()
        # delete servers
        self.nova('destroy-my-servers')
        # detroy tenant networks+routers
        self.qsvc('destroy-myself')
        return (time.time() - t0)

    def _g_config(self, otypes):
        for otype in otypes:
            if otype in self._tenant_topo:
                cfg = self._tenant_topo[otype]
                if type(cfg) is dict:
                    return [cfg]
                return cfg
        return []

    # build resources
    def b_networks(self, networks=None):
        self.networks = {}
        self.subnets = {}
        networks_cfg = self.g_networks_cfg()
        for network in networks_cfg:
            name = adjust_name(network.pop('name'),
                               self.prefix_name, self.suffix_name)
            if 'subnet' in network:
                subnets = [network.pop('subnet')]
            elif 'subnets' in network:
                subnets = network.pop('subnets')
            nets = self.qsvc('net-list', name=name)
            if len(nets) < 1:
                net = self.qsvc('net-create',name, **network)
            else:
                net = nets[0]
            self.networks[name] = self.qsvc('net-show', net['id'])
            self.b_subnets(self.networks[name]['id'], subnets)

    def b_subnets(self, network_id, subnets=None):
        for subnet in subnets:
            name = adjust_name(subnet['name'],
                               self.prefix_name, self.suffix_name)
            cidr = subnet.pop('cidr')
            subnet['name'] = name
            snets = self.qsvc('subnet-list', name=name)
            if len(snets) < 1:
                snet = self.qsvc('subnet-create', network_id, cidr, **subnet)
            else:
                snet = snets[0]
            self.subnets[name] = self.qsvc('subnet-show', snet['id'])

    def b_routers(self, routers=None):
        self.routers = {}
        routers_cfg = self.g_routers_cfg()
        for router in routers_cfg:
            rtr = c_router(self.qsvc, router,
                           prefix_name=self.prefix_name,
                           suffix_name=self.suffix_name)
            self.routers[rtr['name']] = rtr

    def b_servers(self, servers_cfg=None):
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
        return copy.deepcopy(networks)

    def g_routers_cfg(self):
        routers = self._g_config(('routers', 'router'))
        return copy.deepcopy(routers)

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
                        os.path.join(self.dirname_json_file, s_opt['user_data']))
                data = open(s_opt['user_data'], 'r').read()
                s_opt['user_data'] = base64.standard_b64encode(data)
        if len(s_opts) > 0:
            return s_opts[0]
        return {}

    def g_security_groups(self):
        security_groups = self._g_config(
            ('security-groups', 'security_groups', 'security-group', 'security_group'))
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
            self.nova('server-delete', server['id'])

    def d_routers(self):
        for nid, router in self.routers.items():
            self.qsvc('d-this-router', router)

    def d_networks(self):
        for nid, network in self.networks.items():
            self.qsvc('net-delete', network['id'])

    def d_security_groups(self):
        for nid, sg in self.security_groups.items():
            self.qsvc('security-group-delete', sg['id'])


def adjust_name(name, prefix_name=None, suffix_name=None):
    if prefix_name:
        name = prefix_name + "-" + name
    if suffix_name:
        name = name + "-" + suffix_name
    return name


def c_router(qsvc, router_cfg, prefix_name=None, suffix_name=None):
    name = adjust_name(router_cfg.pop('name'), prefix_name, suffix_name)
    rtrs = qsvc('router-list', name=name)
    if len(rtrs) > 0:
        return qsvc('router-show', rtrs[0]['id'])
    else:
        rtr = qsvc('router-create', name)
        gw_if = router_cfg.get('gateway', None)
        gw_kwargs = {}
        if 'enable_snat' in router_cfg:
            gw_kwargs['enable_snat'] = router_cfg['enable_snat']
        rtr_set_gateway(qsvc, rtr['id'], gateway_if=gw_if, **gw_kwargs)
        if_names = router_cfg.get('interfaces', [])
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
    images_in_house = nova('image-list')
    flavors_in_house = nova('flavor-list')
    servers = {}
    for serv_cfg in servers_cfg:
        server = boot_server(nova, qsvc, serv_cfg,
                             images_in_house, flavors_in_house,
                             prefix_name=prefix_name,
                             security_groups=security_groups,
                             wait_on_boot=wait_on_boot)
        servers[server['name']] = server
    return servers


def boot_server(nova, qsvc, server_cfg,
                images_in_house=None, flavors_in_house=None,
                prefix_name=None, suffix_name=None,
                security_groups=None, wait_on_boot=False):
    images_in_house = images_in_house or nova('image-list')
    flavors_in_house = flavors_in_house or nova('flavor-list')
    sv_name = adjust_name(server_cfg.pop('name'), prefix_name, suffix_name)
    if_name = adjust_name(server_cfg.pop('interface'), prefix_name, suffix_name)
    networks = qsvc('net-list', name=if_name)
    image_id = get_image_id(server_cfg.pop('image'), images_in_house)
    flavor_id = get_flavor_id(server_cfg.pop('flavor'), flavors_in_house)
    return nova('c-server-on-interface', networks, image_id,
                name=sv_name, flavor=flavor_id,
                security_groups=security_groups,
                wait_on_boot=wait_on_boot, **server_cfg)


def c_floatingip_to_server(nova, qsvc, server_id,
                           public_id=None, **kwargs):
    network_public_id = public_id or qsvc('net-external-list')[0]
    server = nova('server-show', server_id)
    

def get_image_id(image_name, images_in_house):
    for m in images_in_house:
        if m['name'] == image_name:
            return m['id']
    return None


def get_flavor_id(flavor, flavors_in_house):
    if type(flavor) is int:
        return flavor
    if type(flavor) is str and flavor.is_digit():
        return int(flavor)
    for f in flavors_in_house:
        if f['name'] == flavor:
            return int(f['id'])
    return 1


def get_subnet_name(network_name):
    ix = network_name.find("-network")
    if ix > 1:
        subname = network_name[:ix]
        return subname + "-subnet"
    return network_name + "-sub"


def get_last_trace():
    return traceback.extract_tb(sys.last_traceback)


def print_trace(tracemsg=None):
    tracemsg = tracemsg or get_last_trace()
    for msg in tracemsg:
        print("line#%s @file: %s\n  %s\n    %s" % (msg[1], msg[0], msg[2], msg[3]))
