# from itempest.services.qos.base_qos import BaseQosClient


def _g_qos_client(mgr_or_client):
    qos_client = getattr(mgr_or_client, 'qos_client', mgr_or_client)
    return qos_client


def available_rule_types(mgr_or_client):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.available_rule_types()


def policy_create(mgr_or_client, name, **kwargs):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.create_policy(name, **kwargs)


def policy_list(mgr_or_client, **filters):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.list_policies(**filters)


def policy_show(mgr_or_client, policy_id_or_name):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.show_policy(policy_id_or_name)


def policy_update(mgr_or_client, policy_id_or_name, **fields):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.update_policy(policy_id_or_name, **fields)


def policy_delete(mgr_or_client, policy_id_or_name):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.delete_policy(policy_id_or_name)


def bandwidth_limit_rule_create(mgr_or_client, policy_id_or_name, **kwargs):
    # max_kbps, max_burst_kbps are required.
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.create_bandwidth_limit_rule(policy_id_or_name,
                                                  **kwargs)


def bandwidth_limit_rule_list(mgr_or_client, policy_id_or_name, **filters):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.list_bandwidth_limit_rules(policy_id_or_name,
                                                 **filters)


def bandwidth_limit_rule_show(mgr_or_client, bandwidth_limit_rule_id,
                              policy_id_or_name):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.show_bandwidth_limit_rule(bandwidth_limit_rule_id,
                                                policy_id_or_name)


def bandwidth_limit_rule_update(mgr_or_client, bandwidth_limit_rule_id,
                                policy_id_or_name, **fields):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.update_bandwidth_limit_rule(bandwidth_limit_rule_id,
                                                  policy_id_or_name,
                                                  **fields)


def bandwidth_limit_rule_delete(mgr_or_client, bandwidth_limit_rule_id,
                                policy_id_or_name):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.delete_bandwidth_limit_rule(bandwidth_limit_rule_id,
                                                  policy_id_or_name)


def dscp_marking_rule_create(mgr_or_client, name, dscp_mark, **kwargs):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.create_dscp_marking_rule(name, dscp_mark, **kwargs)


def dscp_marking_rule_list(mgr_or_client, policy_id_or_name, **filters):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.list_dscp_marking_rules(policy_id_or_name, **filters)


def dscp_marking_rule_show(mgr_or_client, dscp_marking_rule_id,
                           policy_id_or_name):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.show_dscp_marking_rule(dscp_marking_rule_id,
                                             policy_id_or_name)


def dscp_marking_rule_update(mgr_or_client, dscp_marking_rule_id,
                             policy_id_or_name, **fields):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.update_dscp_marking_rule(dscp_marking_rule_id,
                                               policy_id_or_name, **fields)


def dscp_marking_rule_delete(mgr_or_client, dscp_marking_rule_id,
                             policy_id_or_name):
    qos_client = _g_qos_client(mgr_or_client)
    return qos_client.delete_dscp_marking_rule(dscp_marking_rule_id,
                                               policy_id_or_name)

