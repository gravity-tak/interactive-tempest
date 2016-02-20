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

from tempest_lib.common.utils import data_utils


# one network/subnet with one VM which will host 2+ servers
def create_single_node_network(cli_mgr, prefix, **kwargs):
    prefix = prefix if prefix else data_utils.rand_name('itempest-lb')
    ip_version = kwargs.pop('ip_version', 4)
    net_name = prefix + "-network"
    snet_name = prefix + "-subnet"
    rtr_name = prefix + "-router"
    cidr = kwargs.pop('cidr', '192.168.11.0/24')
    xnet_id = kwargs.pop('public_network_id', None)
    if xnet_id is None:
        xnet = cli_mgr.qsvc('net-external-list')[0]
        xnet_id = xnet['id']
    network_list = cli_mgr.qsvc('net-list', name=net_name)
    if len(network_list) > 0:
        network = network_list[0]
    else:
        network = cli_mgr.qsvc('net-create', net_name)
    subnet_list = cli_mgr.qsvc('subnet-list', name=snet_name)
    if len(subnet_list) > 0:
        subnet = subnet_list[0]
    else:
        subnet = cli_mgr.qsvc('subnet-create', network['id'], cidr,
                              name=snet_name, ip_version=ip_version)
    router_list = cli_mgr.qsvc('router-list', name=rtr_name)
    if len(router_list) > 0:
        router = router_list[0]
    else:
        router = cli_mgr.qsvc('router-create', rtr_name, admin_state_up=True,
                              router_type='exclusive')
        cli_mgr.qsvc('router-gateway-set', router['id'],
                     external_network_id=xnet_id)
        cli_mgr.qsvc('router-interface-add', router['id'], subnet['id'])
    return dict(network=network, subnet=subnet, router=router)


def create_lbv1_4_single_node(cli_mgr, subnet, prefix=None,
                              protocol_port=80, ip_version=4,
                              delay=4, max_retries=3,
                              monitor_type="TCP", monitory_timeout=1):
    prefix = prefix if prefix else data_utils.rand_name('itempest-lb')
    pool_name = prefix + "-pool"
    vip_name = prefix + "-vip"
    lb_pool = cli_mgr.lbv1('lb-pool-create', pool_name,
                           lb_method="ROUND_ROBIN", protocol="HTTP",
                           subnet_id=subnet['id'])
    lb_vip = cli_mgr.lbv1('lb-vip-create', lb_pool['id'],
                          name=vip_name, protocol="HTTP",
                          protocol_port=protocol_port,
                          subnet_id=subnet['id'])
    lb_member = cli_mgr.lbv1('lb-member-create', protocol_port,
                             lb_pool['id'],
                             ip_version)
    lb_health_monitor = cli_mgr.lbv1('lb-healthmonitor-create',
                                     delay=delay, max_retries=max_retries,
                                     type=monitor_type,
                                     timeout=monitory_timeout)
    return dict(pool=lb_pool, member=lb_member, vip=lb_vip,
                healthmonitor=lb_health_monitor)


def delete_lbv1(cli_mgr, prefix, **kwargs):
    name_prefix = prefix + "-"
    for lb_resource in ('healthmonitor', 'member', 'vip', 'pool'):
        for lbo in cli_mgr.lbv1('lb-%s-list' % lb_resource):
            if 'name' not in lbo or lbo['name'].startswith(name_prefix):
                cli_mgr.lbv1('lb-%s-delete' % lb_resource, lbo['id'])
    for rtr in cli_mgr.qsvc('router-list'):
        if rtr['name'].startswith(name_prefix):
            cli_mgr.qsvc('delete-router', rtr['id'])
    for net in cli_mgr.qsvc('net-list'):
        if net['name'].startswith(name_prefix):
            cli_mgr.qsvc('net-delete', net['id'])
