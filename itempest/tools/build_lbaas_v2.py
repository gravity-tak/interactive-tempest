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

import urllib2
import re

from tempest.lib.common.utils import data_utils
from itempest.lib import lib_networks as NET


def setup_core_network(cmgr, start_servers=True):
    lb_rcfg = NET.setup_lb_network_and_servers(venus, 'lb-v')
    if start_servers:
        NET.start_webservers(lb_rcfg)
    return lb_rcfg


def create_lbv2(cmgr, lb_core_network, prefix=None,
                protocol='HTTP', protocol_port=80, ip_version=4,
                delay=4, max_retries=3,
                monitor_type="HTTP", monitor_timeout=1):
    prefix = prefix if prefix else data_utils.rand_name('kilo-lb2')
    if cmgr.lbaas is None:
        raise Exception(
            "Client manager does not have LBaasV2 clients installed.")
    subnet_id = lb_core_network['subnet']['id']
    load_balancer = cmgr.lbaas('loadbalancer-create', subnet_id,
                               name=prefix)
    listener1 = cmgr.lbaas('listener-create', protocol=protocol,
                           protocol_port=protocol_port,
                           loadbalancer_id=load_balancer['id'],
                           name=prefix + "-listener1")
    pool1 = cmgr.lbaas('pool-create', lb_algorithm='ROUND_ROBIN',
                       protocol=protocol, listener_id=listener1['id'],
                       name=prefix + "-pool1")
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
    healthmonitr1 = cmgr.lbaas('healthmonitor-create',
                               pool_id=pool1['id'],
                               delay=delay,
                               max_retries=max_retries,
                               type=monitor_type,
                               timeout=monitor_timeout)

    return dict(
        name=prefix,
        load_balancer=load_balancer,
        listener=listener1,
        pool=pool1,
        member=member_list,
        health_monitor=healthmonitr1)


def delete_loadbalancer(cmgr, loadbalancer):
    return cmgr.lbaas('loadbalancer-delete-tree', loadbalancer)


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
