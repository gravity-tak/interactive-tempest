from tempest.lib.services.network import base


class BandwidthLimitRulesClient(base.BaseNetworkClient):
    resource = 'bandwidth_limit_rule'
    resource_plural = 'bandwidth_limit_rules'
    path = 'qos/policies'
    resource_base_path = '/%s/%%s/bandwidth_limit_rules' % path
    resource_object_path = '/%s/%%s/bandwidth_limit_rules/%%s' % path

    def create_bandwidth_limit_rule(self, policy_id, **kwargs):
        uri = self.resource_base_path % policy_id
        post_data = {self.resource: kwargs}
        return self.create_resource(uri, post_data)

    def update_bandwidth_limit_rule(self, policy_id, rule_id, **kwargs):
        uri = self.resource_object_path % (policy_id, rule_id)
        post_data = {self.resource: kwargs}
        return self.update_resource(uri, post_data)

    def show_bandwidth_limit_rule(self, policy_id, rule_id, **fields):
        uri = self.resource_object_path % (policy_id, rule_id)
        return self.show_resource(uri, **fields)

    def delete_bandwidth_limit_rule(self, policy_id, rule_id):
        uri = self.resource_object_path % (policy_id, rule_id)
        return self.delete_resource(uri)

    def list_bandwidth_limit_rules(self, policy_id, **filters):
        uri = self.resource_base_path % policy_id
        return self.list_resources(uri, **filters)


def get_client(client_mgr):
    """create a qos policy bandwidth limit rules client

    For itempest user:
        from itempest import load_our_solar_system as osn
        from vmware_nsx_tempest.services.qos import
        bandwidth_limit_rules_client
        client = bandwidth_limit_rules_client.get_client(
        osn.adm.manager)
    For tempest user:
        client = bandwidth_limit_rules_client.get_client(osn.adm)
    """
    manager = getattr(client_mgr, 'manager', client_mgr)
    net_client = getattr(manager, 'networks_client')
    try:
        _params = manager.default_params_with_timeout_values.copy()
    except Exception:
        _params = {}
    client = BandwidthLimitRulesClient(net_client.auth_provider,
                                       net_client.service,
                                       net_client.region,
                                       net_client.endpoint_type,
                                       **_params)
    return client
