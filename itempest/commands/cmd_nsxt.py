from itempest.services import nsxv3_client


def _g_nsxt_client(mgr_or_client):
    return getattr(mgr_or_client, 'nsxt_client', mgr_or_client)


def transport_zones(mgr_or_client, **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    result = net_client.get_transport_zones(**kwargs)
    return result


def logical_switches(mgr_or_client, **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    result = net_client.get_logical_switches(**kwargs)
    return result


def logical_ports(mgr_or_client, **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    result = net_client.get_logical_ports(**kwargs)
    return result


def cluster(mgr_or_client, **kwargas):
    net_client = _g_nsxt_client(mgr_or_client)
    resp = net_client.get("/cluster")
    return resp.json()


def cluster_nodes(mgr_or_client):
    return nodes(mgr_or_client)


def nodes(mgr_or_client, **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    resp = net_client.get("/cluster/nodes")
    return resp.json().get('results')


def node_interfaces(mgr_or_client, node_id, **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    resp = net_client.get("/cluster/nodes/%s/network/interfaces" % node_id)
    return resp.json().get('results')


def node_interface(mgr_or_client, node_id, node_if='eth0', **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    resp = net_client.get("/cluster/nodes/%s/network/interfaces/%s" %
                          (node_id, node_if))
    return resp.json()


def node_if_stats(mgr_or_client, node_id, node_if='eth0', **kwargs):
    net_client = _g_nsxt_client(mgr_or_client)
    resp = net_client.get("/cluster/nodes/%s/network/interfaces/%s/stats" %
                          (node_id, node_if))
    return resp.json()


class NSXT(object):
    def __init__(self, host, username, password, **kwargs):
        self.nsxt = nsxv3_client.NSXV3Client(host, username, password)

    def g_resource_uri(self, resource_path, resource_id=None):
        if resource_id:
            _url = "%s/%s" % (resource_path, resource_id)
            return _url
        return resource_path

    def r_response(self, resp):
        resp_json = resp.json()
        if 'results' in resp_json:
            return resp_json.get('results')
        return resp_json

    def get_cluster(self):
        resp = self.nsxt.get("/cluster")
        return resp.json()

    def get_nodes(self, node_id=None):
        endpoint = self.g_resource_uri("/cluster/nodes", node_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_node_status(self, node_id):
        resp = self.nsxt.get("/cluster/nodes/%s/status" % node_id)
        return self.r_response(resp)

    def get_logical_switches(self, lswitch_id=None):
        endpoint = self.g_resource_uri("/logical-switches", lswitch_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_logical_ports(self, lport_id=None):
        endpoint = self.g_resource_uri("/logical-ports", lport_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_lswitch_ports(self, lswitch_id):
        lsws = self.get_logical_ports()
        lsw2 = [sw for sw in lsws if sw['logical_switch_id'] == lswitch_id]
        return lsw2

    def get_firewall_excludelist(self):
        resp = self.nsxt.get("/firewall/excludelist")
        return resp.json()

    def get_firewall_sections(self, section_id=None):
        endpoint = self.g_resource_uri("/firewall/sections", section_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_firewall_rules(self, section_id, rule_id=None):
        fw_rule_path = "/firewall/sections/%s/rules" % section_id
        endpoint = self.g_resource_uri(fw_rule_path, rule_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_firewall_section_stats(self, section_id, rule_id=None):
        if rule_id:
            stats_path = ("/firewall/sections/%s/rules/%s/stats"
                          % (section_id, rule_id))
        else:
            stats_path = "/firewall/sections/%s/stats" % (section_id)
        resp = self.nsxt.get(stats_path)
        return self.r_response(resp)

    def list_nets(self):
        lsws = self.get_logical_switches()
        lsw2 = []
        for sw in lsws:
            if self.is_os_resource(sw):
                lsw2.append(sw)
        return lsw2

    def list_ports(self):
        lports = self.get_logical_ports()
        lport2 = []
        for p in lports:
            if self.is_os_resource(p):
                lport2.append(p)
        return lport2

    def is_os_resource(self, obj):
        if 'tags' in obj:
            for tag in obj['tags']:
                if 'scope' in tag and tag['scope'].startswith('os-'):
                    return True
        return False
