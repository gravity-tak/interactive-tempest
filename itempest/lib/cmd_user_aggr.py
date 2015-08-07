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

import time

from itempest.lib import cmd_keystone as Keystone
from itempest.lib import cmd_neutron as Neutron
from itempest.lib import cmd_neutron_u1 as N_UserCmd
from itempest.lib import cmd_nova as Nova
from itempest.lib import utils

def get_commands(tenant_mgr):
    keys = utils.command_wrapper(tenant_mgr, [Keystone],
                                 log_header='OS-Keystone')
    nova = utils.command_wrapper(tenant_mgr, [Nova],
                                 log_header='OS-Nova')
    qsvc = utils.command_wrapper(tenant_mgr, [Neutron, N_UserCmd],
                                 log_header='OS-Neutron')
    return (keys, nova, qsvc)


# get_orphan_networks(sun_qsvc, sun_keys)
def get_orphan_networks(qsvc, keys):
    tenant_list = [x['id'] for x in keys('tenant-list')]
    net_list = qsvc('net-list', **{'router:external': False})
    orphan_list = []
    for net in net_list:
        if net['name'].startswith('inter-edge-net'):
            # metadata network, do nothingsu
            continue
        if net['tenant_id'] not in tenant_list:
            orphan_list.append(net)
    return orphan_list


def del_orphan_networks(qsvc, keys):
    orphan_net_list = get_orphan_networks(qsvc, keys)
    for net in orphan_net_list:
        qsvc('destroy-myself', tenant_id=net['tenant_id'])


def get_tenant_of_orphan_networks(qsvc, keys):
    o_list = get_orphan_networks(qsvc, keys)
    o_tenant_list = []
    for o in o_list:
        if o['tenant_id'] not in o_tenant_list:
            o_tenant_list.append(o['tenant_id'])
    return o_tenant_list


def wipeout_net_resources_of_orphan_networks(adm_mgr, **kwargs):
    keys, nova, qsvc = get_commands(adm_mgr)
    tenant_list = get_tenant_of_orphan_networks(qsvc, keys)
    times_used = 0
    for tenant_id in tenant_list:
        times_used += wipeout_tenant_net_resources(tenant_id, adm_mgr)
    return times_used


def wipeout_tenant_net_resources(tenant_id, adm_mgr, **kwargs):
    keys, nova, qsvc = get_commands(adm_mgr)
    t0 = time.time()
    kwargs = {'tenant_id':tenant_id}
    # delete servers
    # self.nova('destroy-my-servers', **kwargs)
    for server in nova('server-list', tenant_id=tenant_id):
        del_server(nova, server['id'], qsvc)
    time.sleep(3.0)
    # detroy tenant networks+routers
    qsvc('destroy-myself',
         force_rm_fip=force_rm_fip, **kwargs)
    return (time.time() - t0)


def del_server(nova, server_id, qsvc=None):
    try:
        sv = nova('server-show', server_id)
        del_server_floatingip(qsvc, sv) if qsvc else None
        return nova('server-delete', server_id)
    except Exception:
        pass


def del_server_floatingip(qsvc, server):
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                addr['OS-EXT-IPS:type'] == u'floating'):
                fip = qsvc('floatingip-list',
                           floating_network_address=addr['addr'])
                qsvc('floatingip_disassociate', fip[0]['id'])
                qsvc('floatingip-delete', fip[0]['id'])

