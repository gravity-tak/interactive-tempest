from tempest.lib.services.network import base


class RuleTypesClient(base.BaseNetworkClient):
    resource = 'rule_type'
    resource_plural = 'rule_types'
    path = 'qos/rule-types'
    resource_base_path = '/%s' % path
    resource_object_path = '/%s/%%s' % path

    def list_rule_types(self):
        uri = self.resource_base_path
        return self.list_resources(uri)


def get_client(client_mgr,
               set_property=False, with_name="qos_rule_types_client"):
    """create a qos rule_types client from manager or networks_client

    For itempest user:
        from itempest import load_our_solar_system as osn
        from vmware_nsx_tempest.services.qos import rule_types_client
        client = rule_types_client.get_client(osn.adm.manager)
    For tempest user:
        client = rule_types_client.get_client(osn.adm)
    """
    manager = getattr(client_mgr, 'manager', client_mgr)
    net_client = getattr(manager, 'networks_client')
    try:
        _params = manager.default_params_with_timeout_values.copy()
    except Exception:
        _params = {}
    client = RuleTypesClient(net_client.auth_provider,
                             net_client.service,
                             net_client.region,
                             net_client.endpoint_type,
                             **_params)
    if set_property:
        setattr(manager, with_name, client)
    return client
