from tempest.lib.services.network import base


class L7PoliciesClient(base.BaseNetworkClient):
    resource = 'l7policy'
    resource_plural = 'l7policies'
    resource_base_path = '/lbaas/l7policies'
    resource_object_path = '/lbaas/l7policies/%s'

    def create_l7policy(self, **kwargs):
        uri = self.resource_base_path
        post_data = {self.resource: kwargs}
        return self.create_resource(uri, post_data)

    def update_l7policy(self, policy_id, **kwargs):
        uri = self.resource_object_path % (policy_id)
        post_data = {self.resource: kwargs}
        return self.update_resource(uri, post_data)

    def show_l7policy(self, policy_id, **fields):
        uri = self.resource_object_path % (policy_id)
        return self.show_resource(uri, **fields)

    def delete_l7policy(self, policy_id):
        uri = self.resource_object_path % (policy_id)
        return self.delete_resource(uri)

    def list_l7policies(self, **filters):
        uri = self.resource_base_path
        return self.list_resources(uri, **filters)


def get_client(client_mgr):
    """create a lbaas l7policies client from manager or networks_client"""
    manager = getattr(client_mgr, 'manager', client_mgr)
    net_client = getattr(manager, 'networks_client')
    try:
        _params = manager.default_params_with_timeout_values.copy()
    except Exception:
        _params = {}
    client = L7PoliciesClient(net_client.auth_provider,
                           net_client.service,
                           net_client.region,
                           net_client.endpoint_type,
                           **_params)
    return client
