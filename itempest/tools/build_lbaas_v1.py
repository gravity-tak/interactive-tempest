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

import urllib2
import re

from tempest.lib.common.utils import data_utils
from itempest.lib import lib_networks as NET


# one network/subnet with one VM which will host 2+ servers
# for clearity, please use
# build_lbaas_networks.setup_lb_network_and_servers(cmgr, x_name)
def setup_single_node_network(cmgr, prefix, **kwargs):
    prefix = prefix if prefix else data_utils.rand_name('itempest-lb')
    ip_version = kwargs.pop('ip_version', 4)
    net_name = prefix + "-network"
    snet_name = prefix + "-subnet"
    rtr_name = prefix + "-router"
    cidr = kwargs.pop('cidr', '192.168.11.0/24')
    xnet_id = kwargs.pop('public_network_id', None)
    if xnet_id is None:
        xnet = cmgr.qsvc('net-external-list')[0]
        xnet_id = xnet['id']
    network_list = cmgr.qsvc('net-list', name=net_name)
    if len(network_list) > 0:
        network = network_list[0]
    else:
        network = cmgr.qsvc('net-create', net_name)
    subnet_list = cmgr.qsvc('subnet-list', name=snet_name)
    if len(subnet_list) > 0:
        subnet = subnet_list[0]
    else:
        subnet = cmgr.qsvc('subnet-create', network['id'], cidr,
                           name=snet_name, ip_version=ip_version)
    router_list = cmgr.qsvc('router-list', name=rtr_name)
    if len(router_list) > 0:
        router = router_list[0]
    else:
        router = cmgr.qsvc('router-create', rtr_name, admin_state_up=True,
                           router_type='exclusive')
        cmgr.qsvc('router-gateway-set', router['id'],
                  external_network_id=xnet_id)
        cmgr.qsvc('router-interface-add', router['id'], subnet['id'])
    return dict(network=network, subnet=subnet, router=router,
                prefix=prefix)


def create_lbv1(cmgr, subnet, member_address_list,
                prefix=None, protocol_port=80, ip_version=4,
                delay=4, max_retries=3,
                monitor_type="TCP", monitory_timeout=1):
    prefix = prefix if prefix else data_utils.rand_name('itempest-lb')
    pool_name = prefix + "-pool"
    vip_name = prefix + "-vip"

    lb_cfg = dict(name=prefix)
    lb_cfg['pool'] = cmgr.lbv1('lb-pool-create', pool_name,
                               lb_method="ROUND_ROBIN", protocol="HTTP",
                               subnet_id=subnet['id'])
    pool_id = lb_cfg['pool']['id']
    lb_cfg['vip'] = cmgr.lbv1('lb-vip-create', pool_id,
                              name=vip_name, protocol="HTTP",
                              protocol_port=protocol_port,
                              subnet_id=subnet['id'])
    lb_cfg['member'] = []
    if member_address_list:
        for m_addr in member_address_list:
            mbr = cmgr.lbv1('lb-member-create', pool_id, protocol_port,
                            ip_version=ip_version, address=m_addr)
            lb_cfg['member'].append(mbr)
    else:
        lb_cfg['member'].append(
            cmgr.lbv1('lb-member-create', pool_id,
                      protocol_port, ip_version=ip_version))
    lb_cfg['health_monitor'] = cmgr.lbv1('lb-healthmonitor-create',
                                         delay=delay,
                                         max_retries=max_retries,
                                         type=monitor_type,
                                         timeout=monitory_timeout)
    health_monitor_id = lb_cfg['health_monitor']['id']
    cmgr.lbv1('lb-healthmonitor-associate', pool_id, health_monitor_id)
    return lb_cfg


def delete_lbv1(cmgr, prefix, **kwargs):
    name_prefix = prefix + "-"
    # after deleting VIP'floatingip
    for vip in cmgr.lbv1('lb-vip-list'):
        if name_prefix == "-" or vip['name'].startswith(name_prefix):
            fip_list = cmgr.qsvc('floatingip-list',
                                 fixed_ip_address=vip['address'])
            for fip in fip_list:
                cmgr.qsvc('floatingip-delete', fip['id'])
    # then we can delete lb resources
    for lb_resource in ('healthmonitor', 'member', 'vip', 'pool'):
        for lbo in cmgr.lbv1('lb-%s-list' % lb_resource):
            if ('name' not in lbo or name_prefix == "-"
                or lbo['name'].startswith(name_prefix)):
                cmgr.lbv1('lb-%s-delete' % lb_resource, lbo['id'])


def delete_vip_resources(cmgr, vip_name_or_id):
    try:
        vip = cmgr.lbv1('lb-vip-show', vip_name_or_id)
    except Exception:
        vip = cmgr.lbv1('lb-vip-list', name=vip_name_or_id)[0]
        vip = cmgr.lbv1('lb-vip-show', vip['id'])

    fip_list = cmgr.qsvc('floatingip-list',
                         fixed_ip_address=vip['address'])
    for fip in fip_list:
        cmgr.qsvc('floatingip-delete', fip['id'])

    vip_id = vip.get('id')
    cmgr.lbv1('lb-vip-delete', vip_id)
    # After delete VIP then we can delete other resources,
    # otherwise delete pool get conflict
    pool_id = vip.get('pool_id')
    if pool_id:
        delete_pool_resources(cmgr, pool_id, delete_pool=True)


def delete_pool_resources(cmgr, pool_id, delete_pool=True):
    pool = cmgr.lbv1('lb-pool-show', pool_id)
    member_ids = pool.get('members', [])
    for member_id in member_ids:
        cmgr.lbv1('lb-member-delete', member_id)

    hms = pool.get('health_monitors', [])
    for hm_id in hms:
        try:
            cmgr.lbv1('lb-healthmonitor-disassociate', pool_id, hm_id)
        except Exception:
            pass
        cmgr.lbv1('lb-healthmonitor-delete', hm_id)
    if delete_pool:
        cmgr.lbv1('lb-pool-delete', pool_id)

# vip_fip = assign_floating_to_vip(cmgr, vip)
def assign_floatingip_to_vip(cmgr, vip, public_network_id=None,
                             security_group_id=None):
    public_network_id = public_network_id or NET.get_public_network_id(
        cmgr)
    port_id = vip['port_id']
    floatingip = cmgr.qsvc('floatingip-create', public_network_id,
                           port_id=port_id)
    # ovs-agent is not enforcing security groups on the vip port
    # see https://bugs.launchpad.net/neutron/+bug/1163569
    # if caller send in security_group_id, set port
    if security_group_id:
        cmgr.qsvc('port-update', port_id,
                  security_groups=[security_group_id])
    return floatingip


def get_vip_port_info(cmgr, vip_fixed_ip):
    filters = dict(
        device_owner="neutron:LOADBALANCER",
        fixed_ips=("ip_address=%s" % (vip_fixed_ip))
    )
    port_list = cmgr.qsvc("port-list", **filters)
    return port_list


# use this method to check lb_method being executed by loadbalancer
# count_http_servers(vip_fip['floating_ip_address'], 50)
def count_http_servers(web_ip, count=20, show_progress=True):
    web_page = "http://{web_ip}/".format(web_ip=web_ip)
    if show_progress:
        print("lbv1 webpage: %s" % web_page)
    ctx = {}
    for x in range(count):
        data = urllib2.urlopen(web_page).read()
        m = re.search("([^\s]+)", data)
        s_ctx = m.group(1)
        if show_progress:
            print("%4d - %s" % (x, s_ctx))
        if s_ctx in ctx.keys():
            ctx[s_ctx] += 1
        else:
            ctx[s_ctx] = 1
    return ctx
