from tempest.lib.services.network import base


class DscpMarkingRulesClient(base.BaseNetworkClient):
    resource = 'dscp_marking_rule'
    resource_plural = 'dscp_marking_rules'
    path = 'qos/policies'
    resource_base_path = '/%s/%%s/dscp_marking_rules' % path
    resource_object_path = '/%s/%%s/dscp_marking_rules/%%s' % path

    def create_dscp_marking_rule(self, policy_id, **kwargs):
        uri = self.resource_base_path % policy_id
        post_data = {self.resource: kwargs}
        return self.create_resource(uri, post_data)

    def update_dscp_marking_rule(self, rule_id, policy_id, **kwargs):
        uri = self.resource_object_path % (policy_id, rule_id)
        post_data = {self.resource: kwargs}
        return self.update_resource(uri, post_data)

    def show_dscp_marking_rule(self, rule_id, policy_id, **fields):
        uri = self.resource_object_path % (policy_id, rule_id)
        return self.show_resource(uri, **fields)

    def delete_dscp_marking_rule(self, rule_id, policy_id):
        uri = self.resource_object_path % (policy_id, rule_id)
        return self.delete_resource(uri)

    def list_dscp_marking_rules(self, policy_id, **filters):
        uri = self.resource_base_path % policy_id
        return self.list_resources(uri, **filters)


def get_client(client_mgr,
               set_property=False,
               with_name="qos_dscp_marking_rules_client"):
    """create a qos policy bandwidth limit rules client

    For itempest user:
        from itempest import load_our_solar_system as osn
        from vmware_nsx_tempest.services.qos import dscp_marking_rules_client
        client = dscp_marking_rules_client.get_client(osn.adm.manager)
    For tempest user:
        client = dscp_marking_rules_client.get_client(osn.adm)
    """
    manager = getattr(client_mgr, 'manager', client_mgr)
    net_client = getattr(manager, 'networks_client')
    try:
        _params = manager.default_params_with_timeout_values.copy()
    except Exception:
        _params = {}
    client = DscpMarkingRulesClient(net_client.auth_provider,
                                    net_client.service,
                                    net_client.region,
                                    net_client.endpoint_type,
                                    **_params)
    if set_property:
        setattr(manager, with_name, client)
    return client
