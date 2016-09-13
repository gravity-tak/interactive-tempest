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

    def get_cluster(self):
        resp = self.nsxt.get("/cluster")
        return resp.json()

    def get_nodes(self, node_id=None):
        endpoint = self.g_resource_uri("/cluster/nodes", node_id)
        resp = self.nsxt.get(endpoint)
        return resp.json().get('results')

    def get_node_status(self, node_id):
        resp = self.nsxt.get("/cluster/nodes/%s/status" % node_id)
        return resp.json()

    def get_logical_switches(self, lswitch_id=None):
        endpoint = self.g_resource_uri("/logical-switch", lswitch_id)
        resp = self.nsxt.get(endpoint)
        return resp.json().get('results')

    def get_logical_ports(self, lport_id=None):
        endpoint = self.g_resource_uri("/logical-ports", lport_id)
        resp = self.nsxt.get(endpoint)
        return resp.json().get('results')

    def get_lswitch_ports(self, lswitch_id):
        lsws = self.get_logical_ports()
        lsw2 = [sw for sw in lsws if sw['logical_switch_id'] == lswitch_id]
        return lsw2
