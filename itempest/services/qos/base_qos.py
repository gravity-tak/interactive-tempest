from itempest.services.qos import policies_client
from itempest.services.qos import (
    bandwidth_limit_rules_client as bandwidth_limit_rules_client)
from itempest.services.qos import (
    dscp_marking_rules_client as dscp_marking_rules_client)
from itempest.services.qos import rule_types_client as rule_types_client

RULE_TYPE_BANDWIDTH_LIMIT = "bandwith_limit"
RULE_TYPE_DSCP_MARK = "dscp_marking"
VALID_RULE_TYPES = [RULE_TYPE_BANDWIDTH_LIMIT, RULE_TYPE_DSCP_MARK]
QOS_POLICY_ID = 'qos_policy_id'


class BaseQosClient(object):
    """usage:

    from itempest import client_manager
    adm = client_manager.get_client_manager('http://10.33.75.103:5000/v2.0', 'admin', 'openstack')
    qos = BaseQosClient(adm)
    qos.available_rule_types()
    """
    def __init__(self, manager):
        self.policies_client = policies_client.get_client(manager, True)
        self.bandwidths_client = (
            bandwidth_limit_rules_client.get_client(manager, True))
        self.dscps_client = dscp_marking_rules_client.get_client(
            manager, True)
        self.types_client = rule_types_client.get_client(manager, True)

    def resp_body(self, result, item):
        return result.get(item, result)

    def create_policy(self, name, **kwargs):
        result = self.policies_client.create_policy(
            name=name,
            **kwargs
        )
        return self.resp_body(result, 'policy')

    def delete_policy(self, policy_id_or_name):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.policies_client.delete_policy(policy_id)
        return self.resp_body(result, 'policy')

    def list_policies(self, **filters):
        result = self.policies_client.list_policies(**filters)
        return self.resp_body(result, 'policies')

    def update_policy(self, policy_id_or_name, **kwargs):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.policies_client.update_policy(policy_id, **kwargs)
        return self.resp_body(result, 'policy')

    def show_policy(self, policy_id_or_name, **fields):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.policies_client.show_policy(policy_id, **fields)
        return self.resp_body(result, 'policy')

    def create_bandwidth_limit_rule(self, policy_id_or_name,
                                    **kwargs):
        # required fields: max_kbps, max_burst_kbps
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.bandwidths_client.create_bandwidth_limit_rule(
            policy_id, **kwargs)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def delete_bandwidth_limit_rule(self, rule_id, policy_id_or_name):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.bandwidths_client.delete_bandwidth_limit_rule(
            rule_id, policy_id)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def update_bandwidth_limit_rule(self, rule_id, policy_id_or_name,
                                    **kwargs):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.bandwidths_client.update_bandwidth_limit_rule(
            rule_id, policy_id, **kwargs)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def list_bandwidth_limit_rules(self, policy_id_or_name, **filters):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.bandwidths_client.list_bandwidth_limit_rules(
            policy_id, **filters)
        return self.resp_body(result, 'bandwidth_limit_rules')

    def show_bandwidth_limit_rule(self, rule_id, policy_id_or_name,
                                  **fields):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.bandwidths_client.show_bandwidth_limit_rule(
            rule_id, policy_id)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def create_dscp_marking_rule(self, policy_id_or_name, dscp_mark,
                                 **kwargs):
        policy_id = self.get_policy_id(policy_id_or_name)
        kwargs['dscp_mark'] = dscp_mark
        result = self.dscps_client.create_dscp_marking_rule(
            policy_id, **kwargs)
        return self.resp_body(result, 'dscp_marking_rule')

    def delete_dscp_marking_rule(self, rule_id, policy_id_or_name):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.dscps_client.delete_dscp_marking_rule(rule_id,
                                                            policy_id)
        return self.resp_body(result, 'dscp_marking_rule')

    def update_dscp_marking_rule(self, rule_id, policy_id_or_name,
                                 **kwargs):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.dscps_client.update_dscp_marking_rule(
            rule_id, policy_id, **kwargs)
        return self.resp_body(result, 'dscp_marking_rule')

    def list_dscp_marking_rules(self, policy_id_or_name, **filters):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.dscps_client.list_dscp_marking_rules(
            policy_id, **filters)
        return self.resp_body(result, 'dscp_marking_rules')

    def show_dscp_marking_rule(self, rule_id, policy_id_or_name, **fields):
        policy_id = self.get_policy_id(policy_id_or_name)
        result = self.dscps_client.show_dscp_marking_rule(
            rule_id, policy_id, **fields)
        return self.resp_body(result, 'dscp_marking_rule')

    def list_rule_types(self):
        result = self.types_client.list_rule_types()
        return self.resp_body(result, 'rule_types')

    def available_rule_types(self):
        return self.list_rule_types()

    def get_policy_id(self, policy_id_or_name):
        return self.policies_client.get_policy_id(policy_id_or_name)
