from itempest.services.qos import policies


class BaseQosClient(object):
    def __init__(self, manager):
        self.policies_client = policies.get_client(manager)

    def create_qos_policies(self, name, description, shared, **kwargs):
        return self.policies_client.create_policy(
            name=name,
            description=description,
            shared=shared,
            **kwargs
        )

    def delete_qos_policies(self, policy_id):
        return self.policies_client.delete_policy(policy_id)

    def list_qos_policies(self, **filter):
        return self.policies_client.list_policies(**filter)

    def update_qos_policies(self, policy_id, **kwargs):
        return self.policies_client.update_policy(policy_id, **kwargs)
