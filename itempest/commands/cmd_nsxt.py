import re

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

    def get_firewall_rule_state(self, rule_id):
        rule_state_path = "/firewall/rules/%s/state" % rule_id
        resp = self.nsxt.get(rule_state_path)
        return self.r_response(resp)

    def get_firewall_sections(self, section_id=None):
        endpoint = self.g_resource_uri("/firewall/sections", section_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_firewall_section_rules(self, section_id, rule_id=None):
        fw_rule_path = "/firewall/sections/%s/rules" % section_id
        endpoint = self.g_resource_uri(fw_rule_path, rule_id)
        resp = self.nsxt.get(endpoint)
        return self.r_response(resp)

    def get_firewall_section_rule_stats(self, section_id, rule_id):
        stats_path = ("/firewall/sections/%s/rules/%s/stats"
                      % (section_id, rule_id))
        resp = self.nsxt.get(stats_path)
        return self.r_response(resp)

    def get_firewall_section_state(self, section_id):
        state_path = "/firewall/sections/%s/state" % (section_id)
        resp = self.nsxt.get(state_path)
        return self.r_response(resp)

    def list_nets(self, **filters):
        lsws = self.get_logical_switches()
        lsw2 = [x for x in lsws if
                os_scope_filter(x.get('tags'), **filters)]
        return lsw2

    def list_ports(self, **filters):
        lports = self.get_logical_ports()
        lport2 = [x for x in lports if
                  os_scope_filter(x.get('tags'), **filters)]
        return lport2

    def list_firewall_sections(self, **filters):
        sections = self.get_firewall_sections()
        sg_list = [x for x in sections if
                   os_scope_filter(x.get('tags'), **filters)]
        return sg_list

    def list_firewall_section_rules(self, section_id, **filters):
        s_rules = self.get_firewall_section_rules(section_id)
        return s_rules

    def list_project_nets(self, os_project_name, **filters):
        filters['os-project-name'] = os_project_name
        return self.list_nets(**filters)

    def list_project_ports(self, os_project_name, **filters):
        filters['os-project-name'] = os_project_name
        return self.list_ports(**filters)

    def list_project_router_interface_ports(self, os_project_name, **filters):
        filters['os-project-name'] = os_project_name
        filters['os-neutron-rport-id'] = '.*'
        return self.list_ports(**filters)

    def list_server_ports(self, **filters):
        # os-instance-uuid is OS's server uuid
        if 'os-instance-uuid' not in filters:
            filters['os-instance-uuid'] = '.*'
        return self.list_ports(**filters)

    def list_project_firewall_sections(self, os_project_name, **filters):
        filters['os-project-name'] = os_project_name
        return self.list_firewall_sections(**filters)

    def list_project_security_groups(self, os_project_name, **filters):
        fw_lists = self.list_project_firewall_sections(os_project_name)
        sgs = {}
        for fw in fw_lists:
            sg_id = get_os_security_group_id(fw)
            if sg_id:
                sgs[sg_id] = fw
        return sgs

    def show_project_security_group(self, os_project_name,
                                    os_security_group_id):
        fw_list = self.list_project_firewall_sections(os_project_name)
        for fw in fw_list:
            sg_id = get_os_security_group_id(fw)
            if sg_id == os_security_group_id:
                return fw
        return None


# generic filtering method to an object is created by OS
def os_scope_filter(tags, **filters):
    if type(tags) not in (list, tuple):
        return False
    if 'os-api-version' not in filters:
        filters['os-api-version'] = ".*"
    c_true = 0
    for elm in tags:
        scope = elm.get('scope')
        if scope in filters and re.search(filters[scope], elm.get('tag')):
            c_true += 1
    if c_true == len(filters):
        return True
    return False


# use this method if faster to determine an object is created by OS
def is_os_resource(obj):
    if 'tags' in obj:
        for tag in obj['tags']:
            if 'scope' in tag and tag['scope'].startswith('os-'):
                return True
    return False


# handy methods to get/find specific object is OS source type
def find_os_id(obj, scope_id):
    if 'tags' in obj:
        for elm in obj.get('tags'):
            if scope_id == elm.get('scope'):
                return elm.get('tag')
    return None

def get_os_net_id(obj):
    return find_os_id(obj, 'os-neutron-net-id')


def get_os_port_id(obj):
    return find_os_id(obj, 'os-neutron-dport-id')


def get_os_project_id(obj):
    return find_os_id(obj, 'os-project-id')


def get_os_project_name(obj):
    return find_os_id(obj, 'os-project-name')


def get_os_security_group_id(obj):
    return find_os_id(obj, 'os-neutron-secgr-id')
