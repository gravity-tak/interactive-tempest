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
def _g_loadbalancers_client(mgr_or_client):
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
    return _return_result(result, 'loadbalancer')


def loadbalancer_update(mgr_or_client, load_balancer_id, **kwargs):
    net_client = _g_loadbalancers_client(mgr_or_client)
    nobj_id = loadbalancer_get_id(mgr_or_client, load_balancer_id)
    result = net_client.update_load_balancer(nobj_id, **kwargs)
    return _return_result(result, 'loadbalancer')


def loadbalancer_delete(mgr_or_client, load_balancer_id):
    net_client = _g_loadbalancers_client(mgr_or_client)
    nobj_id = loadbalancer_get_id(mgr_or_client, load_balancer_id)
    result = net_client.delete_load_balancer(nobj_id)
    return _return_result(result, 'loadbalancer')


# user-defined command
def loadbalancer_delete_tree(mgr_or_client, loadbalancer=None, **filters):
    if loadbalancer:
        lb_list = [loadbalancer_show(mgr_or_client, loadbalancer)]
    else:
        lb_list = loadbalancer_list(mgr_or_client)
    for lb in lb_list:
        destroy_loadbalancer(mgr_or_client, lb['id'])
    return None


def loadbalancer_show(mgr_or_client, load_balancer_id, **fields):
    net_client = _g_loadbalancers_client(mgr_or_client)
    try:
        result = net_client.show_load_balancer(load_balancer_id, **fields)
    except Exception:
        nobj = loadbalancer_list(mgr_or_client, name=load_balancer_id)[0]
        result = net_client.show_load_balancer(nobj['id'], **fields)
    return _return_result(result, 'loadbalancer')


def loadbalancer_list(mgr_or_client, **filters):
    net_client = _g_loadbalancers_client(mgr_or_client)
    result = net_client.list_load_balancers(**filters)
    return _return_result(result, 'loadbalancers')


# no CLI counter part
def loadbalancer_get_id(mgr_or_client, load_balancer_id):
    nobj = loadbalancer_show(mgr_or_client, load_balancer_id)
    return nobj['id']


def loadbalancer_statuses(mgr_or_client, load_balancer_id, **fields):
    return loadbalancer_status_tree(mgr_or_client, load_balancer_id,
                                    **fields)


def loadbalancer_status_tree(mgr_or_client, load_balancer_id, **fields):
    net_client = _g_loadbalancers_client(mgr_or_client)
    nobj_id = loadbalancer_get_id(mgr_or_client, load_balancer_id)
    result = net_client.show_load_balancer_status_tree(nobj_id,
                                                       **fields)
    return _return_result(result, 'statuses')


def loadbalancer_stats(mgr_or_client, load_balancer_id, **fields):
    net_client = _g_loadbalancers_client(mgr_or_client)
    nobj_id = loadbalancer_get_id(mgr_or_client, load_balancer_id)
    result = net_client.show_load_balancer_stats(nobj_id,
                                                 **fields)
    return _return_result(result, 'stats')


# timeout & interval_time added so you know what to control how long to wait
def loadbalancer_waitfor_active(mgr_or_client, load_balancer_id,
                                timeout=600, interval_time=1, **filters):
    filters['provisioning_status'] = 'ACTIVE'
    filters['operating_status'] = 'ONLINE'
    return loadbalancer_waitfor_status(mgr_or_client, load_balancer_id,
                                       timeout=timeout,
                                       interval_time=interval_time,
                                       **filters)


# while deleting the lbaas resource, no need for operating-status be ONLINE
def loadbalancer_waitfor_provisioning_active(mgr_or_client, load_balancer_id,
                                             timeout=600, interval_time=1,
                                             **filters):
    filters['provisioning_status'] = 'ACTIVE'
    return loadbalancer_waitfor_status(mgr_or_client, load_balancer_id,
                                       timeout=timeout,
                                       interval_time=interval_time,
                                       ignore_operating_status=True,
                                       **filters)


def loadbalancer_waitfor_status(mgr_or_client, load_balancer_id, **filters):
    net_client = _g_loadbalancers_client(mgr_or_client)
    load_balancer_id = loadbalancer_get_id(mgr_or_client, load_balancer_id)
    lb = net_client.wait_for_load_balancers_status(load_balancer_id,
                                                   **filters)
    return lb


# listener
def listener_create(mgr_or_client, **kwargs):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.create_listener(**kwargs)
    return _return_result(result, 'listener')


def listener_update(mgr_or_client, listener_id, **kwargs):
    net_client = _g_listeners_client(mgr_or_client)
    listener_id = listener_get_id(mgr_or_client, listener_id)
    result = net_client.update_listener(listener_id, **kwargs)
    return _return_result(result, 'listener')


def listener_delete(mgr_or_client, listener_id):
    net_client = _g_listeners_client(mgr_or_client)
    listener_id = listener_get_id(mgr_or_client, listener_id)
    result = net_client.delete_listener(listener_id)
    return _return_result(result, 'listener')


def listener_show(mgr_or_client, listener_id, **fields):
    net_client = _g_listeners_client(mgr_or_client)
    try:
        result = net_client.show_listener(listener_id, **fields)
    except Exception:
        nobj = listener_list(mgr_or_client, name=listener_id)[0]
        result = net_client.show_listener(nobj['id'], **fields)
    return _return_result(result, 'listener')


def listener_list(mgr_or_client, **filters):
    net_client = _g_listeners_client(mgr_or_client)
    result = net_client.list_listeners(**filters)
    return _return_result(result, 'listeners')


def listener_get_id(mgr_or_client, listener_id):
    nobj = listener_show(mgr_or_client, listener_id)
    return nobj['id']


# pool
def pool_create(mgr_or_client, **kwargs):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.create_pool(**kwargs)
    return _return_result(result, 'pool')


def pool_update(mgr_or_client, pool_id, **kwargs):
    net_client = _g_pools_client(mgr_or_client)
    pool_id = pool_get_id(mgr_or_client, pool_id)
    result = net_client.update_pool(pool_id, **kwargs)
    return _return_result(result, 'pool')


def pool_delete(mgr_or_client, pool_id):
    net_client = _g_pools_client(mgr_or_client)
    pool_id = pool_get_id(mgr_or_client, pool_id)
    result = net_client.delete_pool(pool_id)
    return _return_result(result, 'pool')


def pool_show(mgr_or_client, pool_id, **fields):
    net_client = _g_pools_client(mgr_or_client)
    try:
        result = net_client.show_pool(pool_id, **fields)
    except Exception:
        nobj = pool_list(mgr_or_client, name=pool_id)[0]
        result = net_client.show_pool(nobj['id'], **fields)
    return _return_result(result, 'pool')


def pool_list(mgr_or_client, **filters):
    net_client = _g_pools_client(mgr_or_client)
    result = net_client.list_pools(**filters)
    return _return_result(result, 'pools')


def pool_get_id(mgr_or_client, pool_id):
    nobj = pool_show(mgr_or_client, pool_id)
    return nobj['id']


def pool_waitfor_session_persistence(mgr_or_client, pool_id, sp_type=None):
    net_client = _g_pools_client(mgr_or_client)
    pool = net_client.wait_for_pool_session_persistence(pool_id, sp_type)
    return pool


# healthmonitor, CLI does not use health_monitor like API
# required attributes: max_retires, pool_id, delay, timeout, type
def healthmonitor_create(mgr_or_client, **kwargs):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.create_health_monitor(**kwargs)
    return _return_result(result, 'healthmonitor')


def healthmonitor_update(mgr_or_client, healthmonitor_id, **kwargs):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.update_health_monitor(healthmonitor_id, **kwargs)
    return _return_result(result, 'healthmonitor')


def healthmonitor_delete(mgr_or_client, healthmonitor_id):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.delete_health_monitor(healthmonitor_id)
    return _return_result(result, 'healthmonitor')


def healthmonitor_show(mgr_or_client, healthmonitor_id, **fields):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.show_health_monitor(healthmonitor_id, **fields)
    return _return_result(result, 'healthmonitor')


def healthmonitor_list(mgr_or_client, **filters):
    net_client = _g_healthmonitors_client(mgr_or_client)
    result = net_client.list_health_monitors(**filters)
    return _return_result(result, 'healthmonitors')


def healthmonitor_get_id(mgr_or_client, healthmonitor_id):
    nobj = healthmonitor_show(mgr_or_client, healthmonitor_id)
    return nobj['id']


# member
def member_create(mgr_or_client, pool_id, **kwargs):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.create_member(pool_id, **kwargs)
    return _return_result(result, 'member')


def member_update(mgr_or_client, pool_id, member_id, **kwargs):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.update_member(pool_id, member_id, **kwargs)
    return _return_result(result, 'member')


def member_delete(mgr_or_client, pool_id, member_id):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.delete_member(pool_id, member_id)
    return _return_result(result, 'member')


def member_show(mgr_or_client, pool_id, member_id, **fields):
    net_client = _g_members_client(mgr_or_client)
    pool_id = pool_get_id(mgr_or_client, pool_id)
    result = net_client.show_member(pool_id, member_id, **fields)
    return _return_result(result, 'member')


def member_list(mgr_or_client, pool_id, **filters):
    net_client = _g_members_client(mgr_or_client)
    result = net_client.list_members(pool_id, **filters)
    return _return_result(result, 'members')


def destroy_loadbalancer(mgr_or_client, loadbalancer_id):
    statuses = loadbalancer_status_tree(mgr_or_client, loadbalancer_id)
    lb = statuses.get('loadbalancer', None)
    if lb is None: return None
    lb_id = lb.get('id')
    for listener in lb.get('listeners', []):
        for pool in listener.get('pools', []):
            hm = pool.get('healthmonitor', None)
            if hm:
                healthmonitor_delete(mgr_or_client, hm['id'])
                loadbalancer_waitfor_active(mgr_or_client, lb_id)
            member_list = pool.get('members', [])
            for member in member_list:
                member_delete(mgr_or_client, pool['id'], member['id'])
                loadbalancer_waitfor_active(mgr_or_client, lb_id)
            pool_delete(mgr_or_client, pool['id'])
            loadbalancer_waitfor_active(mgr_or_client, lb_id)
        listener_delete(mgr_or_client, listener['id'])
        loadbalancer_waitfor_active(mgr_or_client, lb_id)
    loadbalancer_delete(mgr_or_client, lb_id)
    try:
        loadbalancer_waitfor_active(mgr_or_client, lb_id)
    except Exception:
        pass
    return None
