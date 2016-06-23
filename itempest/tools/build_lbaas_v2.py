# Copyright 2016 VMware Inc.
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

import re
import urllib3

from tempest.lib.common.utils import data_utils
from itempest.lib import lib_networks as NET
import build_lbaas_networks as LB_NET

LB_ALGORITHMS = ('ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP')


def build_os_lbaas(cmgr, name, **kwargs):
    """Build lbaas environment for UpStream OpenStack"""
    return build_nsx_lbaas(cmgr, name, router_type='default', **kwargs)


def build_nsx_lbaas(cmgr, name, **kwargs):
    """Build lbaas environment for NSX OpenStack."""
    lb_name = kwargs.pop('prefix', kwargs.pop('lb_name', name))
    build_network_only = kwargs.pop('build_network_only', False)
    public_network_id = kwargs.pop('public_network_id', None)
    net_cfg = dict(
        num_servers=kwargs.pop('num_servers', 2),
        username=kwargs.pop('username', 'cirros'),
        password=kwargs.pop('password', 'cubswin:)'),
        image_id=kwargs.pop('image_id', None),
        flavor_id=kwargs.pop('flavor_id', 1),
        cidr=kwargs.pop('cidr', '10.199.88.0/24'),
        port=kwargs.pop('port', 80),
        public_network_id=public_network_id,
        router_type=kwargs.pop('router_type', 'exclusive'))
    start_servers = kwargs.pop('start_servers', True)
    protocol = kwargs.get('protocol', 'HTTP')
    if 'TCP' in protocol.upper():
        start_servers = False
    lb2_network = setup_core_network(cmgr, name, start_servers, **net_cfg)
    if build_network_only:
        return {'network': lb2_network, 'lbaas': None}
    lbaas = create_lbaasv2(cmgr, lb2_network, lb_name=lb_name, **kwargs)
    security_group_id = lb2_network['security_group']['id']
    assign_floatingip_to_vip(cmgr, lb_name,
                             public_network_id=public_network_id,
                             security_group_id=security_group_id)
    return {'network': lb2_network, 'lbaas': lbaas}


def setup_core_network(cmgr, name, start_servers=True, **kwargs):
    lb2_network = LB_NET.setup_lb_network_and_servers(cmgr, name, **kwargs)
    if start_servers:
        LB_NET.start_webservers(lb2_network)
    return lb2_network


def create_lbaasv2(cmgr, lb_core_network, lb_name=None,
                   protocol='HTTP', protocol_port=80, ip_version=4,
                   delay=4, max_retries=3,
                   monitor_type="HTTP", monitor_timeout=1, **kwargs):
    lb_name = lb_name if lb_name else data_utils.rand_name('lb2')
    # pool atrributes
    lb_algorithm = kwargs.pop('lb_algorithm', 'ROUND_ROBIN')
    persistence_type = kwargs.pop('persistence_type', None)
    cookie_name = kwargs.pop('cookie_name', None)
    if cmgr.lbaas is None:
        raise Exception(
            "Client manager does not have LBaasV2 clients installed.")
    subnet_id = lb_core_network['subnet']['id']
    load_balancer = cmgr.lbaas('loadbalancer-create', subnet_id,
                               name=lb_name)
    cmgr.lbaas('loadbalancer_waitfor_active', lb_name)
    listener1 = cmgr.lbaas('listener-create', protocol=protocol,
                           protocol_port=protocol_port,
                           loadbalancer_id=load_balancer['id'],
                           name=lb_name + "-listener1")
    cmgr.lbaas('loadbalancer_waitfor_active', lb_name)
    pool_body = dict(lb_algorithm=lb_algorithm,
                     protocol=protocol,
                     listener_id=listener1['id'],
                     name=lb_name + "-pool1")
    if persistence_type:
        pool_body.update({'session_persistence': {'type': persistence_type}})
    if cookie_name:
        pool_body.update(
            {'session_persistence': {'cookie_name': cookie_name}})
    pool1 = cmgr.lbaas('pool-create', **pool_body)
    cmgr.lbaas('loadbalancer_waitfor_active', lb_name)
    member_list = []
    for server_id in lb_core_network['servers']:
        server = lb_core_network['servers'][server_id]
        fip = server['fip']
        fixed_ip_address = fip['fixed_ip_address']
        member = cmgr.lbaas('member-create', pool1['id'],
                            subnet_id=subnet_id,
                            address=fixed_ip_address,
                            protocol_port=protocol_port)
        member_list.append(member)
        cmgr.lbaas('loadbalancer_waitfor_active', lb_name)
    healthmonitor1 = cmgr.lbaas('healthmonitor-create',
                                pool_id=pool1['id'],
                                delay=delay,
                                max_retries=max_retries,
                                type=monitor_type,
                                timeout=monitor_timeout)
    cmgr.lbaas('loadbalancer_waitfor_active', lb_name)

    return dict(
        name=lb_name,
        load_balancer=load_balancer,
        listener=listener1,
        pool=pool1,
        member=member_list,
        health_monitor=healthmonitor1)


def delete_loadbalancer(cmgr, loadbalancer, quit=False):
    if quit:
        return cmgr.lbaas('loadbalancer-delete-tree', loadbalancer)
    else:
        return destroy_loadbalancer(cmgr, loadbalancer)


def destroy_loadbalancer(cmgr, loadbalancer, delete_fip=True):
    loadbalancer_id = cmgr.lbaas('loadbalancer-get-id', loadbalancer)
    get_loadbalancer_floatingip(cmgr, loadbalancer_id,
                                and_delete_it=delete_fip)
    statuses = cmgr.lbaas("loadbalancer-statuses", loadbalancer_id)
    lb = statuses.get('loadbalancer', None)
    if lb is None: return None
    lb_id = lb.get('id')
    for listener in lb.get('listeners', []):
        for pool in listener.get('pools', []):
            hm = pool.get('healthmonitor', None)
            if hm:
                cmgr.lbaas("healthmonitor-delete", hm['id'])
                cmgr.lbaas("loadbalancer-waitfor-active", lb_id)
            member_list = pool.get('members', [])
            for member in member_list:
                cmgr.lbaas("member-delete", pool['id'], member['id'])
                cmgr.lbaas("loadbalancer-waitfor-active", lb_id)
            cmgr.lbaas("pool-delete", pool['id'])
            cmgr.lbaas("loadbalancer-waitfor-active", lb_id)
        cmgr.lbaas("listener-delete", listener['id'])
        cmgr.lbaas("loadbalancer-waitfor-active", lb_id)
    cmgr.lbaas("loadbalancer-delete", lb_id)
    try:
        cmgr.lbaas("loadbalancer-waitfor-active", lb_id)
    except Exception:
        pass
    return None


def show_lbaas_tree(cmgr, loadbalancer):
    lb2 = cmgr.lbaas('loadbalancer-show', loadbalancer)
    lb_id = lb2['id']
    lb_tree = pack_fields(lb2, ('id', 'name', 'operating_status',
                                'provisioning_status', 'provider'
                                                       'vip_address',
                                'vip_port',
                                'vip_subnet_id'))

    for listener_dd in lb2.get('listeners'):
        listener = cmgr.lbaas('listener-show', listener_dd.get('id'))
        lb_tree += "\n" + pack_fields(listener, ('id', 'name'))
        pool_id = listener.get('default_pool_id', None)
        if pool_id:
            pool = cmgr.lbaas('pool-show', pool_id)
            lb_tree += "\n" + pack_fields(pool, ('id', 'name'), sp=4)
            hm_id = pool.get('healthmonitor_id', None)
            if hm_id:
                hm = cmgr.lbaas('healthmonitory-show', hm_id)
                lb_tree += "\n" + pack_fields(hm, ('id', 'tcp'), sp=4)
            for member in pool.get('members'):
                mbr = cmgr.lbaas('member-show', pool_id, member['id'])
                lb_tree += "\n" + pack_fields(mbr, ('id', 'tcp'), sp=8)
    return lb_tree


def delete_all_lbaas(cmgr, waitfor_active=60):
    for lb in cmgr.lbaas('loadbalancer-list'):
        delete_lbaas(cmgr, lb['id'], waitfor_active=waitfor_active)


def delete_lbaas(cmgr, loadbalancer, delete_fip=True, waitfor_active=60):
    lb2, fip = get_loadbalancer_floatingip(cmgr, loadbalancer, delete_fip)
    lb_id = lb2['id']
    for listener_dd in lb2.get('listeners'):
        listener = cmgr.lbaas('listener-show', listener_dd.get('id'))
        pool_id = listener.get('default_pool_id', None)
        if pool_id:
            pool = cmgr.lbaas('pool-show', pool_id)
            hm_id = pool.get('healthmonitor_id', None)
            if hm_id:
                cmgr.lbaas('healthmonitor-delete', hm_id)
                cmgr.lbaas("loadbalancer-waitfor-provisioning-active", lb_id,
                           timeout=waitfor_active)
            for member in pool.get('members'):
                cmgr.lbaas('member-delete', pool_id, member['id'])
                cmgr.lbaas("loadbalancer-waitfor-provisioning-active", lb_id,
                           timeout=waitfor_active)
            cmgr.lbaas('pool-delete', pool_id)
            cmgr.lbaas("loadbalancer-waitfor-provisioning-active", lb_id,
                       timeout=waitfor_active)
        cmgr.lbaas("listener-delete", listener['id'])
        cmgr.lbaas("loadbalancer-waitfor-provisioning-active", lb_id,
                   timeout=waitfor_active)
    # OK, we can delete the load-balancer
    cmgr.lbaas("loadbalancer-delete", lb_id)
    return cmgr.lbaas("loadbalancer-list", id=lb_id)


def assign_floatingip_to_vip(cmgr, loadbalancer, public_network_id=None,
                             security_group_id=None):
    public_network_id = (public_network_id or
                         NET.get_public_network_id(cmgr))
    lb = cmgr.lbaas('loadbalancer-show', loadbalancer)
    vip_port_id = lb['vip_port_id']
    floatingip = cmgr.qsvc('floatingip-create', public_network_id,
                           port_id=vip_port_id)
    # ovs-agent is not enforcing security groups on the vip port
    # see https://bugs.launchpad.net/neutron/+bug/1163569
    # if caller send in security_group_id, set port
    if security_group_id:
        cmgr.qsvc('port-update', vip_port_id,
                  security_groups=[security_group_id])
    return floatingip


def get_loadbalancer_floatingip(cmgr, loadbalancer_id, and_delete_it=False):
    lb2 = cmgr.lbaas("loadbalancer-show", loadbalancer_id)
    fip_list = cmgr.qsvc('floatingip-list', subnet_id=lb2['vip_subnet_id'],
                         fixed_ip_address=lb2['vip_address'])
    if len(fip_list) == 1:
        fip = fip_list[0]
        if and_delete_it:
            cmgr.qsvc('floatingip-disassociate', fip['id'])
            cmgr.qsvc('floatingip-delete', fip['id'])
        return (lb2, fip)
    elif len(fip_list) > 1:
        raise Exception("More than one floatingips attached to VIP!!!")
    return (lb2, None)


def count_http_servers(web_ip, count=10, show_progress=True):
    web_page = "http://{web_ip}/".format(web_ip=web_ip)
    if show_progress:
        print("lbaas webpage: %s" % web_page)
    ctx = {}
    http = urllib3.PoolManager()
    for x in range(count):
        resp = http.request('GET', web_page)
        data = resp.data
        m = re.search("([^\s]+)", data)
        s_ctx = m.group(1)
        if show_progress:
            print("%4d - %s" % (x, s_ctx))
        if s_ctx in ctx.keys():
            ctx[s_ctx] += 1
        else:
            ctx[s_ctx] = 1
    return ctx


def get_fields(sdict, *fields):
    odict = dict([(x, y) for (x, y) in sdict.items() if x in fields])
    return odict


def pack_fields(sdict, *args, **kwargs):
    width = kwargs.pop('width', 78)
    lead_sp = kwargs.pop('sp', 0)
    sss = ""
    ss = " " * lead_sp
    s = ""
    for field in args:
        if field not in sdict: continue
        s = "--%s=%s" % (field, sdict[field])
        if len(ss + s) > width:
            sss += ss + "\n"
            ss = " " * lead_sp
        elif len(ss) <= lead_sp:
            ss += s
        else:
            ss += " " + s
    if len(ss) > lead_sp:
        sss += ss + "\n"
    return sss
