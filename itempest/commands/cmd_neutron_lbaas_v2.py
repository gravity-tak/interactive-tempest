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
#
# NOTE:
#    unlike cmd_neutron_lbaas_v1, lbaasV2 commands utilizing the lbaas v2
#    clients directly.


# lbaasv2 clients
def _g_load_balancers_client(mgr_or_client):
    return getattr(mgr_or_client, 'load_balancers_client', mgr_or_client)


def _g_listeners_client(mgr_or_client):
    return getattr(mgr_or_client, 'listeners_client', mgr_or_client)


def _g_pools_client(mgr_or_client):
    return getattr(mgr_or_client, 'pools_client', mgr_or_client)


def _g_healthmonitors_client(mgr_or_client):
    return getattr(mgr_or_client, 'health_monitors_client', mgr_or_client)


def _g_members_client(mgr_or_client):
    return getattr(mgr_or_client, 'members_client', mgr_or_client)


def _return_result(result, of_attr):
    if of_attr in result:
        return result[of_attr]
    return result


# load-balancer
def loadbalancer_create(mgr_or_client, vip_subnet_id, **kwargs):
    net_client = _g_loadbalancers_client(mgr_or_client)
    kwargs['vip_subnet_id'] = vip_subnet_id
    result = net_client.create_load_balancer(**kwargs)
    return _retrun_result(result, 'loadbalancer')


def loadbalancer_update(mgr_or_client, load_balancer_id, **kwargs):
    net_client = _g_loadbalancers_client(mgr_or_client)
    result = net_client.update_load_balancer(load_balancer_id, **kwargs)
    return _retrun_result(result, 'loadbalancer')


def loadbalancer_delete(mgr_or_client, load_balancer_id):
    net_client = _g_loadbalancers_client(mgr_or_client)
    result = net_client.delete_load_balancer(load_balancer_id)
    return _retrun_result(result, 'loadbalancer')


def loadbalancer_show(mgr_or_client, load_balancer_id, **fields):
    net_client = _g_loadbalancers_client(mgr_or_client)
    result = net_client.show_load_balancer(load_balancer_id, **fields)
    return _retrun_result(result, 'loadbalancer')


# no CLI counter part
def loadbalancer_status_tree_show(mgr_or_client, load_balancer_id, **fields):
    net_client = _g_loadbalancer_client(mgr_or_client)
    result = net_client.show_load_balancers_status_tree(load_balancer_id,
                                                        **fields)
    return _retrun_result(result, 'loadbalancer')


# no CLI counter part
def loadbalancer_stats_show(mgr_or_client, load_balancer_id, **fields):
    net_client = _g_loadbalancer_client(mgr_or_client)
    result = net_client.show_load_balancers_stats(load_balancer_id,
                                                  **fields)
    return _retrun_result(result, 'loadbalancer')


def loadbalancer_list(mgr_or_client, **filters):
    net_client = _g_loadbalancers_client(mgr_or_client)
    result = net_client.list_load_balancers(**fields)
    return _retrun_result(result, 'loadbalancers')

# listener
def listener_create(mgr_or_client, **kwargs):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.create_listener(**kwargs)
    return _retrun_result(result, 'listener')


def listener_update(mgr_or_client, listener_id, **kwargs):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.update_listener(listener_id, **kwargs)
    return _retrun_result(result, 'listener')


def listener_delete(mgr_or_client, listener_id):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.delete_listener(listener_id)
    return _retrun_result(result, 'listener')


def listener_show(mgr_or_client, listener_id, **fields):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.show_listener(listener_id, **fields)
    return _retrun_result(result, 'listener')


def listener_list(mgr_or_client, **filters):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.list_listeners(**fields)
    return _retrun_result(result, 'listeners')


# pool
def pool_create(mgr_or_client, **kwargs):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.create_pool(**kwargs)
    return _retrun_result(result, 'pool')


def pool_update(mgr_or_client, pool_id, **kwargs):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.update_pool(pool_id, **kwargs)
    return _retrun_result(result, 'pool')


def pool_delete(mgr_or_client, pool_id):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.delete_pool(pool_id)
    return _retrun_result(result, 'pool')


def pool_show(mgr_or_client, pool_id, **fields):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.show_pool(pool_id, **fields)
    return _retrun_result(result, 'pool')


def pool_list(mgr_or_client, **filters):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.list_pools(**fields)
    return _retrun_result(result, 'pools')


# healthmonitor, CLI does not use health_monitor like API
def healthmonitor_create(mgr_or_client, **kwargs):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.create_healthmonitor(**kwargs)
    return _retrun_result(result, 'healthmonitor')


def healthmonitor_update(mgr_or_client, healthmonitor_id, **kwargs):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.update_healthmonitor(healthmonitor_id, **kwargs)
    return _retrun_result(result, 'healthmonitor')


def healthmonitor_delete(mgr_or_client, healthmonitor_id):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.delete_healthmonitor(healthmonitor_id)
    return _retrun_result(result, 'healthmonitor')


def healthmonitor_show(mgr_or_client, healthmonitor_id, **fields):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.show_healthmonitor(healthmonitor_id, **fields)
    return _retrun_result(result, 'healthmonitor')


def healthmonitor_list(mgr_or_client, **filters):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.list_healthmonitors(**fields)
    return _retrun_result(result, 'healthmonitors')


# member
def member_create(mgr_or_client, pool_id, **kwargs):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.create_member(pool_id, **kwargs)
    return _retrun_result(result, 'member')


def member_update(mgr_or_client, pool_id, member_id, **kwargs):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.update_member(pool_id, member_id, **kwargs)
    return _retrun_result(result, 'member')


def member_delete(mgr_or_client, pool_id, member_id):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.delete_member(pool_id, member_id)
    return _retrun_result(result, 'member')


def member_show(mgr_or_client, pool_id, member_id, **fields):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.show_member(pool_id, member_id, **fields)
    return _retrun_result(result, 'member')


def member_list(mgr_or_client, pool_id, **filters):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.list_members(pool_id, **fields)
    return _retrun_result(result, 'members')
