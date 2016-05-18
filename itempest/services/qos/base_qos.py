from itempest.services.qos import policies_client
from itempest.services.qos import \
    bandwidth_limit_rules_client as bandwidth_client
from itempest.services.qos import dscp_marking_rules_client as dscp_client


class BaseQosClient(object):
    def __init__(self, manager):
        self.policies_client = policies_client.get_client(manager)
        self.bandwidth_client = bandwidth_client.get_client(manager)
        self.dscp_client = dscp_client.get_client(manager)

    def create_qos_policies(self, name, description, shared, **kwargs):
        result = self.policies_client.create_policy(
            name=name,
            description=description,
            shared=shared,
            **kwargs
        )
        return result

    def delete_qos_policies(self, policy_id):
        result = self.policies_client.delete_policy(policy_id)
        return result

    def list_qos_policies(self, **filter):
        result = self.policies_client.list_policies(**filter)
        return result

    def update_qos_policies(self, policy_id, **kwargs):
        result = self.policies_client.update_policy(policy_id, **kwargs)
        return result

    def show_qos_policies(self, policy_id, **kwargs):
        result = self.policies_client.show_policy(policy_id, **kwargs)
        return result

    def create_bandwidth_limit_rule(self, policy_id, **kwargs):
        result = self.bandwidth_client.create_bandwith_limit_rule(policy_id,
                                                                  **kwargs)
        return result

    def delete_bandwidth_limit_rule(self, policy_id):
        result = self.bandwidth_client.delete_bandwidth_limit_rule(policy_id)
        return result

    def update_bandwidth_limit_rule(self, policy_id):
        result = self.bandwidth_client.update_bandwidth_limit_rule(policy_id)
        return result

    def list_bandwidth_limit_rules(self, policy_id, **filter):
        result = self.bandwidth_client.list_bandwidth_limit_rules(policy_id,
                                                                  **filter)
        return result

    def show_bandwidth_limit_rule(self, policy_id):
        result = self.bandwidth_client.show_bandwidth_limit_rule(policy_id)
        return result

    def create_dscp_marking_rule(self, policy_id, **kwargs):
        result = self.dscp_client.create_dscp_marking_rule(policy_id,
                                                           **kwargs)
        return result

    def delete_dscp_marking_rule(self, policy_id):
        result = self.dscp_client.delete_dscp_marking_rule(policy_id)
        return result

    def update_dscp_marking_rule(self, policy_id):
        result = self.dscp_client.update_dscp_marking_rule(policy_id)
        return result

    def list_dscp_marking_rules(self, policy_id, **filter):
        result = self.dscp_client.list_dscp_marking_rules(policy_id, **filter)
        return result

    def show_dscp_marking_rule(self, policy_id):
        result = self.dscp_client.show_dscp_marking_rule(policy_id)
        return result
