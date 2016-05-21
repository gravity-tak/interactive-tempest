from itempest.services.qos import policies_client
from itempest.services.qos import \
    bandwidth_limit_rules_client as bandwidth_limit_rules_client
from itempest.services.qos import \
    dscp_marking_rules_client as dscp_marking_rules_client
from itempest.services.qos import rule_types_client as rule_types_client


class BaseQosClient(object):
    def __init__(self, manager):
        self.policies_client = policies_client.get_client(manager)
        self.bandwidths_client = (
            bandwidth_limit_rules_client.get_client(manager))
        self.dscps_client = dscp_marking_rules_client.get_client(manager)
        self.types_client = rule_types_client.get_client(manager)

    def resp_body(self, result, item):
        return result.get(item, result)

    def create_policy(self, name, description, shared, **kwargs):
        result = self.policies_client.create_policy(
            name=name,
            description=description,
            shared=shared,
            **kwargs
        )
        return self.resp_body(result, 'policy')

    def delete_policy(self, policy_id):
        result = self.policies_client.delete_policy(policy_id)
        return self.resp_body(result, 'policy')

    def list_policies(self, **filter):
        result = self.policies_client.list_policies(**filter)
        return self.resp_body(result, 'policies')

    def update_policy(self, policy_id, **kwargs):
        result = self.policies_client.update_policy(policy_id, **kwargs)
        return self.resp_body(result, 'policy')

    def show_policy(self, policy_id, **fields):
        result = self.policies_client.show_policy(policy_id, **fields)
        return self.resp_body(result, 'policy')

    def create_bandwidth_limit_rule(self, policy_id,
                                    max_kbps, max_burst_kbps,
                                    **kwargs):
        result = self.bandwidths_client.create_bandwidth_limit_rule(
            policy_id,
            max_kbps=max_kbps, max_burst_kbps=max_burst_kbps,
            **kwargs)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def delete_bandwidth_limit_rule(self, policy_id, rule_id):
        result = self.bandwidths_client.delete_bandwidth_limit_rule(
            policy_id, rule_id)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def update_bandwidth_limit_rule(self, policy_id, rule_id, **kwargs):
        result = self.bandwidths_client.update_bandwidth_limit_rule(
            policy_id, rule_id, **kwargs)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def list_bandwidth_limit_rules(self, policy_id, **filter):
        result = self.bandwidths_client.list_bandwidth_limit_rules(
            policy_id, **filter)
        return self.resp_body(result, 'bandwidth_limit_rules')

    def show_bandwidth_limit_rule(self, policy_id, rule_id, **fields):
        result = self.bandwidths_client.show_bandwidth_limit_rule(
            policy_id, rule_id, **fields)
        return self.resp_body(result, 'bandwidth_limit_rule')

    def create_dscp_marking_rule(self, policy_id, dscp_mark, **kwargs):
        kwargs['dscp_mark'] = dscp_mark
        result = self.dscps_client.create_dscp_marking_rule(
            policy_id, **kwargs)
        return self.resp_body(result, 'dscp_marking_rule')

    def delete_dscp_marking_rule(self, policy_id):
        result = self.dscps_client.delete_dscp_marking_rule(policy_id)
        return self.resp_body(result, 'dscp_marking_rule')

    def update_dscp_marking_rule(self, policy_id, rule_id, **kwargs):
        result = self.dscps_client.update_dscp_marking_rule(
            policy_id, rule_id, **kwargs)
        return self.resp_body(result, 'dscp_marking_rule')

    def list_dscp_marking_rules(self, policy_id, **filter):
        result = self.dscps_client.list_dscp_marking_rules(
            policy_id, **filter)
        return self.resp_body(result, 'dscp_marking_rules')

    def show_dscp_marking_rule(self, policy_id, rule_id, **fields):
        result = self.dscps_client.show_dscp_marking_rule(
            policy_id, rule_id, **fields)
        return self.resp_body(result, 'dscp_marking_rule')

    def list_rule_types(self):
        result = self.types_client.list_rule_types()
        return result

    def available_rule_types(self):
        return self.list_rule_types()
