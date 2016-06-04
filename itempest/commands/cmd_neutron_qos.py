
def _g_qos_client(mgr_or_client):
    qos_client = getattr(mgr_or_client, 'qos_client', mgr_or_client)
    return qos_client


def available_rule_types(mgr_or_client):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.available_rule_types()


def policy_create(mgr_or_client, name, description, shared, **kwargs):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.create_policy(name, description, shared, **kwargs)


def policy_list(mgr_or_client, **filters):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.list_policies(**filters)


def policy_show(mgr_or_client, policy_id):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.show_policy(policy_id)


def policy_update(mgr_or_client, policy_id, **fields):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.update_policy(policy_id, **fields)


def policy_delete(mgr_or_client, policy_id):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.delete_policy(policy_id)

def bandwidth_limit_rule_create(mgr_or_client, name, description, shared, **kwargs):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.create_bandwidth_limit_rule(name, description, shared, **kwargs)


def bandwidth_limit_rule_list(mgr_or_client, **filters):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.list_bandwidth_limit_rules(**filters)


def bandwidth_limit_rule_show(mgr_or_client, bandwidth_limit_rule_id):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.show_bandwidth_limit_rule(bandwidth_limit_rule_id)


def bandwidth_limit_rule_update(mgr_or_client, bandwidth_limit_rule_id, **fields):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.update_bandwidth_limit_rule(bandwidth_limit_rule_id, **fields)


def bandwidth_limit_rule_delete(mgr_or_client, bandwidth_limit_rule_id):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.delete_bandwidth_limit_rule(bandwidth_limit_rule_id)

def dscp_marking_rule_create(mgr_or_client, name, description, shared, **kwargs):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.create_dscp_marking_rule(name, description, shared, **kwargs)


def dscp_marking_rule_list(mgr_or_client, **filters):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.list_dscp_marking_rules(**filters)


def dscp_marking_rule_show(mgr_or_client, dscp_marking_rule_id):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.show_dscp_marking_rule(dscp_marking_rule_id)


def dscp_marking_rule_update(mgr_or_client, dscp_marking_rule_id, **fields):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.update_dscp_marking_rule(dscp_marking_rule_id, **fields)


def dscp_marking_rule_delete(mgr_or_client, dscp_marking_rule_id):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.delete_dscp_marking_rule(dscp_marking_rule_id)

