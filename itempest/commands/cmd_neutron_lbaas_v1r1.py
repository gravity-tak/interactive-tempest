
def _g_net_client(mgr_or_client):
    return getattr(mgr_or_client, 'lbs_client', mgr_or_client)


def _return_result(result, of_attr):
    if of_attr in result:
        return result[of_attr]
    return result


def lb_agent_hosting_pool(mgr_or_client):
    """Get loadbalancer agent hosting a pool."""
    pass


def lb_healthmonitor_associate(mgr_or_client, pool_id, health_monitor_id):
    """Create a mapping between a health monitor and a pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.associate_health_monitor_with_pool(
        health_monitor_id, pool_id)
    return _return_result(result, 'health_monitor')


def lb_healthmonitor_create(mgr_or_client, **kwargs):
    """Create a health monitor."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.create_health_monitor(**kwargs)
    return _return_result(result, 'health_monitor')


def lb_healthmonitor_delete(mgr_or_client, healthmonitor_id):
    """Delete a given health monitor."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.delete_health_monitors(healthmonitor_id)
    return _return_result(result, 'health_monitor')


def lb_healthmonitor_disassociate(mgr_or_client, pool_id, health_monitor_id):
    """Remove a mapping from a health monitor to a pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.disassociate_health_monitor_with_pool(
        health_monitor_id, pool_id)
    return _return_result(result, 'health_monitor')


def lb_healthmonitor_list(mgr_or_client, **filters):
    """List health monitors that belong to a given tenant."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.list_health_monitors(**filters)
    return _return_result(result, 'health_monitors')


def lb_healthmonitor_show(mgr_or_client, healthmonitor_id):
    """Show information of a given health monitor."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.show_health_monitor(healthmonitor_id)
    return _return_result(result, 'health_monitor')


def lb_healthmonitor_update(mgr_or_client, healthmonitor_id,
                            show_then_update=True, **kwargs):
    """Update a given health monitor."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.update_health_monitor(healthmonitor_id)
    return _return_result(result, 'health_monitor')


# tempest create_member(self,protocol_port, pool, ip_version)
# we use pool_id
def lb_member_create(mgr_or_client, pool_id, protocol_port,
                     ip_version=4, **kwargs):
    """Create a member."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.create_member(pool_id=pool_id,
                                      protocol_port=protocol_port,
                                      ip_version=ip_version, **kwargs)
    return _return_result(result, 'member')


def lb_member_delete(mgr_or_client, member_id):
    """Delete a given member."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.delete_member(member_id)
    return _return_result(result, 'member')


def lb_member_list(mgr_or_client, **filters):
    """List members that belong to a given tenant."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.list_members(**filters)
    return _return_result(result, 'members')


def lb_member_show(mgr_or_client, member_id):
    """Show information of a given member."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.show_member(member_id)
    return _return_result(result, 'member')


def lb_member_update(mgr_or_client, member_id, **kwargs):
    """Update a given member."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.update_member(member_id, **kwargs)
    return _return_result(result, 'member')


def lb_pool_create(mgr_or_client, pool_name, lb_method, protocol, subnet_id,
                   **kwargs):
    """Create a pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.create_pool(pool_name, lb_method, protocol,
                                    subnet_id, **kwargs)
    return _return_result(result, 'pool')


def lb_pool_delete(mgr_or_client, pool_id):
    """Delete a given pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.delete_pool(pool_id)
    return _return_result(result, 'pool')


def lb_pool_list(mgr_or_client, **filters):
    """List pools that belong to a given tenant."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.list_pools(**filters)
    return _return_result(result, 'pools')


def lb_pool_list_on_agent(mgr_or_client):
    """List the pools on a loadbalancer agent."""
    pass


def lb_pool_show(mgr_or_client, pool_id):
    """Show information of a given pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.show_pool(pool_id)
    return _return_result(result, 'pool')


def lb_pool_stats(mgr_or_client, pool_id, **filters):
    """Retrieve stats for a given pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.list_lb_pool_stats(pool_id, **filters)
    return _return_result(result, 'pools')


def lb_pool_update(mgr_or_client, pool_id,
                   show_then_update=True, **kwargs):
    """Update a given pool."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.update_pool(pool_id, **kwargs)
    return _return_result(result, 'pool')


def lb_vip_create(mgr_or_client, pool_id, **kwargs):
    """Create a vip."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.create_vip(pool_id, **kwargs)
    return _return_result(result, 'vip')


def lb_vip_delete(mgr_or_client, vip_id):
    """Delete a given vip."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.delete_vip(vip_id)
    return _return_result(result, 'vip')


def lb_vip_list(mgr_or_client, **filters):
    """List vips that belong to a given tenant."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.list_vips(**filters)
    return _return_result(result, 'vips')


def lb_vip_show(mgr_or_client, vip_id):
    """Show information of a given vip."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.show_vip(vip_id)
    return _return_result(result, 'vip')


def lb_vip_update(mgr_or_client, vip_id,
                  show_then_update=True, **kwargs):
    """Update a given vip."""
    net_client = _g_net_client(mgr_or_client)
    result = net_client.update_vip(vip_id, **kwargs)
    return _return_result(result, 'vip')


def destroy_lb(mgr_or_client):
    for o in lb_member_list(mgr_or_client):
        lb_member_delete(mgr_or_client, o['id'])
    for o in lb_healthmonitor_list(mgr_or_client):
        lb_healthmonitor_delete(mgr_or_client, o['id'])
    for o in lb_vip_list(mgr_or_client):
        lb_vip_delete(mgr_or_client, o['id'])
    for o in lb_pool_list(mgr_or_client):
        lb_pool_delete(mgr_or_client, o['id'])
