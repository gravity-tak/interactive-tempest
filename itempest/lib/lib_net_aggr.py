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

from operator import itemgetter
import re
import time
import traceback

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


# cli_mgr = utils.get_mimic_manager_cli(os_auth_url, username, passwor)
def wipeout_net_resources_of_orphan_networks(cli_mgr, **kwargs):
    force_rm_fip = kwargs.pop('force_rm_fip', True)
    tenant_list = get_tenant_of_orphan_networks(cli_mgr)
    times_used = 0
    for tenant_id in tenant_list:
        times_used += wipeout_tenant_net_resources(
            tenant_id, cli_mgr, force_rm_fip=force_rm_fip, **kwargs)
    return times_used


def wipeout_tenant_net_resources(tenant_id, cli_mgr,
                                 force_rm_fip=False, **kwargs):
    t0 = time.time()
    kwargs = {'tenant_id': tenant_id}
    # delete servers
    # self.nova('destroy-my-servers', **kwargs)
    for server in cli_mgr.nova('server-list', tenant_id=tenant_id):
        del_server(cli_mgr.nova, server['id'])
    time.sleep(3.0)
    # detroy tenant networks+routers
    cli_mgr.qsvc('destroy-myself',
                 force_rm_fip=force_rm_fip, **kwargs)
    return (time.time() - t0)


# get_orphan_networks(sun_qsvc, sun_keys)
def get_orphan_networks(cli_mgr):
    tenant_list = [x['id'] for x in cli_mgr.keys('tenant-list')]
    net_list = cli_mgr.qsvc('net-list', **{'router:external': False})
    orphan_list = []
    for net in net_list:
        if net['name'].startswith('inter-edge-net'):
            # metadata network, do nothingsu
            continue
        if net['tenant_id'] not in tenant_list:
            orphan_list.append(net)
    return orphan_list


def del_orphan_networks(cli_mgr):
    orphan_net_list = get_orphan_networks(cli_mgr)
    for net in orphan_net_list:
        cli_mgr.qsvc('destroy-myself', tenant_id=net['tenant_id'])


def get_tenant_of_orphan_networks(cli_mgr):
    o_list = get_orphan_networks(cli_mgr)
    o_tenant_list = []
    for o in o_list:
        if o['tenant_id'] not in o_tenant_list:
            o_tenant_list.append(o['tenant_id'])
    return o_tenant_list


def add_floatingip_to_server(cli_mgr, server_id,
                             public_id=None, security_group_id=None,
                             **kwargs):
    public_network_id = public_id or cli_mgr.qsvc('net-external-list')[0]
    action = kwargs.pop('action', 'add')
    check_interval = kwargs.pop('check_interval', None)
    duration = kwargs.pop('check_duration', 30)
    sleep_for = kwargs.pop('sleep_for', 1)
    show_progress = kwargs.pop('show_progress', True)
    floatingip = cli_mgr.qsvc('create-floatingip-for-server',
                              public_network_id['id'], server_id)
    if security_group_id:
        cli_mgr.qsvc('update-port-security-group', floatingip['port_id'],
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


def del_server(cli_mgr, server_id):
    try:
        sv = cli_mgr.nova('server-show', server_id)
        del_server_floatingip(cli_mgr, sv)
        return cli_mgr.nova('server-delete', server_id)
    except Exception:
        pass


def del_server_floatingip_by_id(cli_mgr, server_id):
    server = cli_mgr.nova('server-show', server_id)
    del_server_floatingip(cli_mgr, server)
    # TODO(akang): read sever to make sure floatingip is DELETED.
    #              If not it is BUG
    return cli_mgr.nova('server-show', server_id)


def del_server_floatingip(cli_mgr, server):
    for if_name, if_addresses in server['addresses'].items():
        for addr in if_addresses:
            if ('OS-EXT-IPS:type' in addr and
                        addr['OS-EXT-IPS:type'] == u'floating'):
                fip = cli_mgr.qsvc('floatingip-list',
                                   floating_network_address=addr['addr'])
                cli_mgr.qsvc('floatingip_disassociate', fip[0]['id'])
                cli_mgr.qsvc('floatingip-delete', fip[0]['id'])


def test_servers_are_reachable(cli_mgr, loginable_sg_name='loginable',
                               action='add', del_fip=True):
    serv_list = [x['id'] for x in cli_mgr.nova('server-list')]
    sg_id = cli_mgr.qsvc('security-group-list', name=loginable_sg_name)[0]
    return check_servers_are_reachable(cli_mgr, serv_list,
                                       security_group_id=sg_id['id'],
                                       action=action, del_fip=del_fip)


def check_servers_are_reachable(cli_mgr, server_id_list,
                                security_group_id=None,
                                check_interval=5,
                                check_duration=60,
                                action='add', del_fip=True):
    result = {}
    n_failure = 0
    for server_id in server_id_list:
        fip_result = add_floatingip_to_server_and_test_reachibility(
            cli_mgr, server_id,
            security_group_id=security_group_id,
            action=action,
            check_interval=check_interval,
            check_duration=check_duration)
        n_failure += 0 if fip_result[1] else 0
        if del_fip:
            del_server_floatingip_by_id(cli_mgr, server_id)
    return (n_failure, result)


def add_floatingip_to_server_and_test_reachibility(
        cli_mgr, server_id, security_group_id=None, action='add',
        check_interval=5, check_duration=60):
    mesg_p = "%s reach server[%s %s] with-ip[%s %s]."
    try:
        ss = cli_mgr.nova('server-show', server_id)
        fip_result = add_floatingip_to_server(
            cli_mgr, server_id,
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


def check_server_public_interface_ssh_allowed(
        cli_mgr, server_id, dest_ip_list):
    s_name, s_info = cli_mgr.nova('info-server', server_id)
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


def show_toplogy(cli_mgr, return_topo=False):
    tenant_name = cli_mgr.manager.credentials.tenant_name
    FMT_ROUTER = "%s>> router: {name} {id} {router_type}" % (' ' * 2)
    FMT_INTERFACE = "%s>> interface: {name} {id}" % (' ' * 6)
    FMT_SUBNETS = "%s subnets: {subnets}" % (' ' * 10)
    FMT_SERVER = "%s>> server: {name} {id}" % (' ' * 10)
    FMT_SERV_ADDR = "%s>> network: %s "
    topo = []
    topo_line = ["\nNetwork topology of tenant[%s]" % tenant_name]
    s_list = cli_mgr.nova('server-list-with-detail')
    router_list = cli_mgr.qsvc('router-list')
    sorted(router_list, key=itemgetter('name'))
    for router in router_list:
        rtr = _g_by_attr(router, ('id', 'name', 'router_type'))
        rtr['networks'] = []
        topo_line.append(FMT_ROUTER.format(**rtr))
        rp_list = cli_mgr.qsvc('router-port-list', router['id'])
        for rp in rp_list:
            network = cli_mgr.qsvc('net-show', rp['network_id'])
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


def get_user_data_of_server(server_ipaddr,
                            username='cirros', password='cubswin:)'):
    ud_cmd = 'curl -v http://169.254.169.254/openstack/latest/user_data'
    s_client = remote_client.RemoteClient(server_ipaddr, username, password)
    user_data = s_client.exec_command(ud_cmd)
    return user_data


def wipeout(cli_mgr, tenant_id=None, force_rm_fip=True):
    t0 = time.time()
    kwargs = {}
    if tenant_id:
        kwargs['tenant_id'] = tenant_id
    # delete servers
    # self.nova('destroy-my-servers', **kwargs)
    for server in cli_mgr.nova('server-list'):
        del_server(cli_mgr, server['id'])
    time.sleep(3.0)
    # detroy tenant networks+routers
    cli_mgr.qsvc('destroy-myself',
                 force_rm_fip=force_rm_fip,
                 **kwargs)
    return (time.time() - t0)


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
