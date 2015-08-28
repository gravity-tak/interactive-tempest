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
#
# This implements load balance v1 which can not be found at libery release

import json

from tempest.common import service_client
from tempest.services.network.json.network_client import NetworkClient

VERSION = "2.0"
URI_PREFIX = "v2.0"
POOL_RID = 'pool'
VIP_RID = 'vip'
HEALTHMONITOR_RID = 'health_monitor'
MEMBER_RID = 'member'


def _g_net_client(mgr_or_client):
    if isinstance(mgr_or_client, NetworkClient):
        return mgr_or_client
    return mgr_or_client.network_client


def _g_resource_namelist(lb_resource):
    if lb_resource[-1] == 's':
        return (lb_resource[:-1], lb_resource)
    return (lb_resource, lb_resource + "s")


def _list_lb(mgr_or_client, lb_resource):
    resource_name_s, resource_name_p = _g_resource_namelist(lb_resource)
    req_uri = '%s/lb/%s' % (URI_PREFIX, resource_name_p)
    net_client = _g_net_client(mgr_or_client)
    resp, body = net_client.get(req_uri)
    net_client.expected_success(200, resp.status)
    body = json.loads(body)
    result = service_client.ResponseBody(resp, body)
    if lb_resource in result:
        return result[lb_resource]
    return result


def _show_lb(mgr_or_client, lb_resource, resource_id):
    resource_name_s, resource_name_p = _g_resource_namelist(lb_resource)
    req_uri = '%s/lb/%s/%s' % (URI_PREFIX, resource_name_p, resource_id)
    net_client = _g_net_client(mgr_or_client)
    resp, body = net_client.get(req_uri)
    net_client.expected_success(200, resp.status)
    body = json.loads(body)
    result = service_client.ResponseBody(resp, body)
    if lb_resource in result:
        return result[lb_resource]
    return result


def _delete_lb(mgr_or_client, lb_resource, resource_id):
    resource_name_s, resource_name_p = _g_resource_namelist(lb_resource)
    req_uri = '%s/lb/%s/%s' % (URI_PREFIX, resource_name_p, resource_id)
    net_client = _g_net_client(mgr_or_client)
    resp, body = net_client.delete(req_uri)
    net_client.expected_success(204, resp.status)
    result = service_client.ResponseBody(resp, body)
    return result


def _create_lb(mgr_or_client, lb_resource, **kwargs):
    resource_name_s, resource_name_p = _g_resource_namelist(lb_resource)
    req_uri = '%s/lb/%s' % (URI_PREFIX, resource_name_p)
    net_client = _g_net_client(mgr_or_client)
    post_body = {resource_name_s: kwargs}
    body = json.dumps(post_body)
    resp, body = net_client.post(req_uri, body)
    net_client.expected_success(201, resp.status)
    body = json.loads(body)
    return service_client.ResponseBody(resp, body)


def lb_agent_hosting_pool(mgr_or_client):
    """Get loadbalancer agent hosting a pool."""
    pass


def lb_healthmonitor_associate(mgr_or_client):
    """Create a mapping between a health monitor and a pool."""
    pass


def lb_healthmonitor_create(mgr_or_client):
    """Create a health monitor."""
    pass


def lb_healthmonitor_delete(mgr_or_client, healthmonitor_id):
    """Delete a given health monitor."""
    return _delete_lb(mgr_or_client, HEALTHMONITOR_RID, healthmonitor_id)


def lb_healthmonitor_disassociate(mgr_or_client):
    """Remove a mapping from a health monitor to a pool."""
    pass


def lb_healthmonitor_list(mgr_or_client):
    """List health monitors that belong to a given tenant."""
    return _list_lb(mgr_or_client, HEALTHMONITOR_RID)


def lb_healthmonitor_show(mgr_or_client, healthmonitor_id):
    """Show information of a given health monitor."""
    return _show_lb(mgr_or_client, HEALTHMONITOR_RID, healthmonitor_id)


def lb_healthmonitor_update(mgr_or_client):
    """Update a given health monitor."""
    pass


def lb_member_create(mgr_or_client):
    """Create a member."""
    pass


def lb_member_delete(mgr_or_client, member_id):
    """Delete a given member."""
    return _delete_lb(mgr_or_client, MEMBER_RID, member_id)


def lb_member_list(mgr_or_client):
    """List members that belong to a given tenant."""
    return _list_lb(mgr_or_client, MEMBER_RID)


def lb_member_show(mgr_or_client, member_id):
    """Show information of a given member."""
    return _show_lb(mgr_or_client, MEMBER_RID, member_id)


def lb_member_update(mgr_or_client):
    """Update a given member."""
    pass


def lb_pool_create(mgr_or_client, pool_name, lb_method, protocol, subnet_id,
                   **kwargs):
    """Create a pool."""
    lb_method = lb_method or 'ROUND_ROBIN'
    protocol = protocol or 'HTTP'
    post_body = dict(name=pool_name, lb_method=lb_method,
                     protocol=protocol, subnet_id=subnet_id)
    return _create_lb(mgr_or_client, POOL_RID, **post_body)


def lb_pool_delete(mgr_or_client, pool_id):
    """Delete a given pool."""
    return _delete_lb(mgr_or_client, 'pools', pool_id)


def lb_pool_list(mgr_or_client):
    """List pools that belong to a given tenant."""
    lb_resource = 'pools'
    return _list_lb(mgr_or_client, lb_resource)


def lb_pool_list_on_agent(mgr_or_client):
    """List the pools on a loadbalancer agent."""
    pass


def lb_pool_show(mgr_or_client, pool_id):
    """Show information of a given pool."""
    return _show_lb(mgr_or_client, 'pools', pool_id)


def lb_pool_stats(mgr_or_client, pool_id):
    """Retrieve stats for a given pool."""
    uri = '%s/lb/pools/%s/stats' % (URI_PREFIX, pool_id)
    net_client = _g_net_client(mgr_or_client)
    resp, body = net_client.get(uri)
    net_client.expected_success(200, resp.status)
    body = json.loads(body)
    return service_client.ResponseBody(resp, body)


def lb_pool_update(mgr_or_client, pool_id, **kwargs):
    """Update a given pool."""
    resource_name_s, resource_name_p = _g_resource_namelist(POOL_RID)
    uri = '%s/lb/pools/%s' % (URI_PREFIX, resource_name_p, pool_id)
    net_client = _g_net_client(mgr_or_client)
    body = lb_pool_show(mgr_or_client, pool_id)
    body.update(**kwargs)
    update_body = {resource_name_s: body}
    update_body = json.dumps(update_body)
    resp, body = net_client.put(uri, update_body)
    net_client.expected_success(200, resp.status)
    body = json.loads(body)
    return service_client.ResponseBody(resp, body)


def lb_vip_create(mgr_or_client, vip_id):
    """Create a vip."""
    pass


def lb_vip_delete(mgr_or_client, vip_id):
    """Delete a given vip."""
    return _delete_lb(mgr_or_client, 'vips', vip_id)


def lb_vip_list(mgr_or_client):
    """List vips that belong to a given tenant."""
    lb_resource = 'vips'
    return _list_lb(mgr_or_client, lb_resource)


def lb_vip_show(mgr_or_client, vip_id):
    """Show information of a given vip."""
    return _show_lb(mgr_or_client, 'vips', vip_id)


def lb_vip_update(mgr_or_client):
    """Update a given vip."""
    pass
