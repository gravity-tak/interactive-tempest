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

from operator import itemgetter
import re
import time
import traceback

from itempest.lib import cmd_keystone
from itempest.lib import cmd_neutron
from itempest.lib import cmd_neutron_u1
from itempest.lib import cmd_nova
from itempest.lib import utils
from itempest.lib import man_data as mdata

from tempest.common.utils.linux import remote_client

VM_DEFAULT_CREDENTIALS = {
    'cirros-0.3.3-x86_64-disk': {'username': 'cirros',
                                 'password': 'cubswin:)'}
}


def get_image_cred(img_name):
    if img_name in VM_DEFAULT_CREDENTIALS:
        return VM_DEFAULT_CREDENTIALS[img_name]
    else:
        return dict(username='root', password='password')


def get_net_resource_commands(tenant_mgr):
    keys = utils.command_wrapper(tenant_mgr, [cmd_keystone],
                                 log_header='OS-Keystone')
    nova = utils.command_wrapper(tenant_mgr, [cmd_nova],
                                 log_header='OS-Nova')
    qsvc = utils.command_wrapper(tenant_mgr, [cmd_neutron, cmd_neutron_u1],
                                 log_header='OS-Neutron')
    return (keys, nova, qsvc)


def wipeout_net_resources_of_orphan_networks(adm_mgr, **kwargs):
    keys, nova, qsvc = get_net_resource_commands(adm_mgr)
    tenant_list = get_tenant_of_orphan_networks(qsvc, keys)
    times_used = 0
    for tenant_id in tenant_list:
        times_used += wipeout_tenant_net_resources(tenant_id, adm_mgr)
    return times_used


def wipeout_tenant_net_resources(tenant_id, adm_mgr, **kwargs):
    keys, nova, qsvc = get_net_resource_commands(adm_mgr)
    t0 = time.time()
    kwargs = {'tenant_id': tenant_id}
    # delete servers
    # self.nova('destroy-my-servers', **kwargs)
    for server in nova('server-list', tenant_id=tenant_id):
        del_server(nova, server['id'], qsvc)
    time.sleep(3.0)
    # detroy tenant networks+routers
    qsvc('destroy-myself',
         force_rm_fip=force_rm_fip, **kwargs)
    return (time.time() - t0)


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


def add_floatingip_to_server(qsvc, server_id,
                             public_id=None, security_group_id=None,
                             **kwargs):
    public_network_id = public_id or qsvc('net-external-list')[0]
    action = kwargs.pop('action', 'add')
    check_interval = kwargs.pop('check_interval', None)
    duration = kwargs.pop('check_duration', 30)
    sleep_for = kwargs.pop('sleep_for', 1)
    show_progress = kwargs.pop('show_progress', True)
    floatingip = qsvc('create-floatingip-for-server',
                      public_network_id['id'], server_id)
    if security_group_id:
        qsvc('update-port-security-group', floatingip['port_id'],
             security_group_id, action=action)
    if check_interval:
        server_public_ipaddr = floatingip['floating_ip_address']

        # pause for control-plane to propagate floating-ip to resources
        time.sleep(_g_float(check_interval))
        is_reachable = utils.ipaddr_is_reachable(
            server_public_ipaddr,
            duration, sleep_for, show_progress=show_progress)
    else:
        is_reachable = None
    return (floatingip, is_reachable)


def del_server(nova, server_id, qsvc=None):
    try:
        sv = nova('server-show', server_id)
        del_server_floatingip(qsvc, sv) if qsvc else None
        return nova('server-delete', server_id)
    except Exception:
        pass


def del_server_floatingip_by_id(qsvc, nova, server_id):
    server = nova('server-show', server_id)
    del_server_floatingip(qsvc, server)
    # TODO(akang): read sever to make sure floatingip is DELETED.
    #              If not it is BUG
    return nova('server-show', server_id)


def del_server_floatingip(qsvc, server):
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                        addr['OS-EXT-IPS:type'] == u'floating'):
                fip = qsvc('floatingip-list',
                           floating_network_address=addr['addr'])
                qsvc('floatingip_disassociate', fip[0]['id'])
                qsvc('floatingip-delete', fip[0]['id'])


def test_servers_are_reachable(mgr_or_client, loginable_sg_name='loginable',
                               action='add', del_fip=True):
    keys, nova, qsvc = get_net_resource_commands(mgr_or_client)
    serv_list = [x['id'] for x in nova('server-list')]
    sg_id = qsvc('security-group-list', name=loginable_sg_name)[0]
    return check_servers_are_reachable(qsvc, nova, serv_list,
                                       security_group_id=sg_id['id'],
                                       action=action, del_fip=del_fip)


def check_servers_are_reachable(qsvc, nova, server_id_list,
                               security_group_id=None,
                               check_interval=5,
                               check_duration=60,
                               action='add', del_fip=True):
    result = {}
    n_failure = 0
    for server_id in server_id_list:
        fip_result = add_floatingip_to_server_and_test_reachibility(
            qsvc, nova, server_id,
            security_group_id=security_group_id,
            action=action,
            check_interval=check_interval,
            check_duration=check_duration)
        n_failure += 0 if fip_result[1] else 0
        if del_fip:
            del_server_floatingip_by_id(qsvc, nova, server_id)
    return (n_failure, result)


def add_floatingip_to_server_and_test_reachibility(qsvc, nova, server_id,
                                                   security_group_id=None,
                                                   action='add',
                                                   check_interval=5,
                                                   check_duration=60):
    mesg_p = "%s reach server[%s %s] with-ip[%s %s]."
    try:
        ss = nova('server-show', server_id)
        fip_result = add_floatingip_to_server(
            qsvc, server_id,
            security_group_id=security_group_id,
            check_interval=check_interval,
            check_duration=check_duration,
            action=action)
        m_type = "CAN" if fip_result[1] else "CAN'T"
        mesg = mesg_p % (m_type, server_id, ss['name'],
                         fip_result[0]['fixed_ip_address'],
                         fip_result[0]['floating_ip_address'])
        utils.log_msg(mesg)
        return fip_result
    except Exception:
        tb_str = traceback.format_exc()
        mesg = ("ERROR creating floatingip for server[%s]:\n%s" % (
            server_id, tb_str))
        utils.log_msg(mesg)
        return (server_id, False)


def check_server_public_interface_ssh_allowed(qsvc, nova, server_id,
                                              dest_ip_list):
    s_name, s_info = nova('info-server', server_id)
    img_name = s_info['image']
    cred = get_image_cred(img_name)
    n_reachable = 0
    floatingip_attr = 'IPv4-floating'
    for if_name, if_info in s_info['networks'].items():
        if floatingip_attr in if_info:
            handler = remote_client.RemoteClient(
                if_info[floatingip_attr],
                cred['username'], cred['password']
            )
            for dest_ip in dest_ip_list:
                is_ok = is_reachable(handler, dest_ip)
                n_reachable += 1 if is_ok else 0
    return n_reachable


def is_reachable(ssh_client, dest_ip, time_out=60.0, ping_timeout=5.0):
    for now in utils.run_till_timeout(time_out, ping_timeout):
        reachable = dest_is_reachable(ssh_client, dest_ip)
        if reachable:
            return True
        mesg = ("Dest[%s] not-reachable retry in %s seconds."
                % (dest_ip, time_out))
        utils.log_msg(mesg)
    return False


def isnot_reachable(ssh_client, dest_ip, time_out=60.0, ping_timeout=5.0,
                    idle_time=2.0):
    if idle_time > 0.0:
        time.sleep(idle_time)
    for now in utils.run_till_timeout(time_out, ping_timeout):
        reachable = dest_is_reachable(ssh_client, dest_ip)
        if not reachable:
            return True
        mesg = ("Dest[%s] is reachable retry in %s seconds."
                % (dest_ip, time_out))
        utils.log_msg(mesg)
    return False


def dest_is_reachable(ssh_client, dest_ip):
    XPTN = r"(\d+).*transmit.*(\d+).*receive.*(\d+).*loss"
    try:
        result = ssh_client.ping_host(dest_ip)
        utils.log_msg(result)
        m = re.search(XPTN, result, (re.I | re.M))
        if m and int(m.group(1)) > 0 and int(m.group(3)) == 0:
            return True
        else:
            return False
    except Exception:
        tb_str = traceback.format_exc()
        mesg = ("ERROR test dest_ip[%s] is reachable:\n%s" % (
            dest_ip, tb_str))
        utils.log_msg(mesg)
        return False


def show_toplogy(mgr_or_client, return_topo=False):
    tenant_name = mgr_or_client.credentials.tenant_name
    FMT_ROUTER = "%s>> router: {name} {id} {router_type}" % (' ' * 2)
    FMT_INTERFACE = "%s>> interface: {name} {id}" % (' ' * 6)
    FMT_SUBNETS = "%s subnets: {subnets}" % (' ' * 12)
    FMT_SERVER = "%s>> sever: {name} {id}" % (' ' * 10)
    FMT_SERV_ADDR = "%s>> network: %s "
    topo = []
    topo_line = ["\nNetwork topology of tenant[%s]" % tenant_name]
    keys, nova, qsvc = get_net_resource_commands(mgr_or_client)
    s_list = nova('server-list-with-detail')
    router_list = qsvc('router-list')
    sorted(router_list, key=itemgetter('name'))
    for router in router_list:
        rtr = _g_by_attr(router, ('id', 'name', 'router_type'))
        rtr['networks'] = []
        topo_line.append(FMT_ROUTER.format(**rtr))
        rp_list = qsvc('router-port-list', router['id'])
        for rp in rp_list:
            network = qsvc('net-show', rp['network_id'])
            netwk = _g_by_attr(network, ('name', 'id', 'subnets'))
            netwk['port_id'] = rp['id']
            netwk['servers'] = []
            topo_line.append(FMT_INTERFACE.format(**netwk))
            topo_line.append(FMT_SUBNETS.format(**netwk))
            if_name = network['name']
            if_servers = [s for s in s_list if if_name in s['addresses']]
            for s in if_servers:
                addr_dict = mdata.get_server_address(s)
                no_if = len(addr_dict)
                serv = _g_by_attr(s, ('name', 'id'))
                serv['#interface'] = no_if
                topo_line.append(
                    FMT_SERVER.format(**s) + " #network=%s" % no_if)
                if if_name in addr_dict:
                    serv['interface'] = addr_dict[if_name]
                    topo_line.append(
                        FMT_SERV_ADDR % (' ' * 14, addr_dict[if_name]))
                netwk['servers'].append(serv)
            rtr['networks'].append(netwk)
        topo.append(rtr)
    print("\n".join(topo_line))
    return topo if return_topo else {}


def _g_by_attr(s_dict, attr_list):
    d_dict = {}
    for attr in attr_list:
        if attr in s_dict:
            d_dict[attr] = s_dict[attr]
    return d_dict


def _g_float(something, somevalue=1.0):
    try:
        return float(something)
    except Exception:
        return somevalue
