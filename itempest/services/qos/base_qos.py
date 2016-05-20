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

    def create_policies(self, name, description, shared, **kwargs):
        result = self.policies_client.create_policy(
            name=name,
            description=description,
            shared=shared,
            **kwargs
        )
        return result

    def delete_policies(self, policy_id):
        result = self.policies_client.delete_policy(policy_id)
        return result

    def list_policies(self, **filter):
        result = self.policies_client.list_policies(**filter)
        return result

    def update_policies(self, policy_id, **kwargs):
        result = self.policies_client.update_policy(policy_id, **kwargs)
        return result

    def show_policies(self, policy_id, **kwargs):
        result = self.policies_client.show_policy(policy_id, **kwargs)
        return result

    def create_bandwidth_limit_rule(self, policy_id,
                                    max_kbps, max_burst_kbps,
                                    **kwargs):
        result = self.bandwidths_client.create_bandwith_limit_rule(
            policy_id,
            max_kbps=max_kbps, max_burst_kbps=max_burst_kbps,
            **kwargs)
        return result

    def delete_bandwidth_limit_rule(self, policy_id, rule_id):
        result = self.bandwidths_client.delete_bandwidth_limit_rule(
            policy_id, rule_id)
        return result

    def update_bandwidth_limit_rule(self, policy_id, rule_id, **kwargs):
        result = self.bandwidths_client.update_bandwidth_limit_rule(
            policy_id, rule_id, **kwargs)
        return result

    def list_bandwidth_limit_rules(self, policy_id, **filter):
        result = self.bandwidths_client.list_bandwidth_limit_rules(
            policy_id, **filter)
        return result

    def show_bandwidth_limit_rule(self, policy_id, rule_id):
        result = self.bandwidths_client.show_bandwidth_limit_rule(
            policy_id, rule_id)
        return result

    def create_dscp_marking_rule(self, policy_id, dscp_mask, **kwargs):
        kwargs['dscp_mask'] = dscp_mask
        result = self.dscps_client.create_dscp_marking_rule(
            policy_id, **kwargs)
        return result

    def delete_dscp_marking_rule(self, policy_id):
        result = self.dscps_client.delete_dscp_marking_rule(policy_id)
        return result

    def update_dscp_marking_rule(self, policy_id, rule_id, **kwargs):
        result = self.dscps_client.update_dscp_marking_rule(
            policy_id, rule_id, **kwargs)
        return result

    def list_dscp_marking_rules(self, policy_id, **filter):
        result = self.dscps_client.list_dscp_marking_rules(
            policy_id, **filter)
        return result

    def show_dscp_marking_rule(self, policy_id, rule_id):
        result = self.dscps_client.show_dscp_marking_rule(
            policy_id, rule_id)
        return result

    def list_rule_types(self):
        result = self.types_client.list_rule_types()
        return result

    def available_rule_types(self):
        return self.list_rule_types()
