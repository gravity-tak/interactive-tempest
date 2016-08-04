class TagValues(object):
    def __init__(self):
        self.flavors = ['gold', 'silver', 'brown']
        self.locations = ['east', 'south', 'west', 'north']
        self.owners = ['development', 'testing', 'production']
        self.abc = ['a', 'ab', 'abc']
        self.tags = (
            ['gold', 'east', 'production'],
            ['silver', 'west', 'testing'],
            ['brown', 'north', 'development', 'abc'],
            ['brown', 'south', 'testing', 'a'],
            ['gold', 'west', 'production', 'ab'],
            ['silver', 'north', 'testing'])


class TagNetworks(object):
    def __init__(self, manager, **kwargs):
        self.tags_client = manager.tags_client
        self.networks_client = manager.networks_client
        self.tags = []

    def network_add_tag(self, network_id, tag):
        self.tags_client.add_tag(resource_type='network',
                                 resource_id=network_id,
                                 tag=tag)
        network = self.networks_client.show_network(network_id)['network']
        return network

    def network_remove_tag(self, network_id, tag):
        self.tags_client.remove_tag(resource_type='network',
                                    resource_id=network_id,
                                    tag=tag)
        network = self.networks_client.show_network(network_id)['network']
        return network

    def network_replace_tags(self, network_id, tags=None):
        if tags is None:
            tags = ['a', 'ab', 'abc']
        req_body = dict(resource_type='network',
                        resource_id=network_id, tags=tags)
        self.tags_client.replace_tag(**req_body)
        network = self.networks_client.show_network(network_id)['network']
        return network


class TestTags(object):
    def __init__(self, cli_mgr):
        self.tagV = TagValues()
        self.cmgr = cli_mgr
        self.nets = {}
        self.G = {}
        for ix in range(0, len(self.tagV.tags)):
            net_name = "%s-tags-%02d" % (self.cmgr.tenant_name, ix)
            net = self.cmgr.qsvc('net-create', name=net_name)
            net_id = net['id']
            self.cmgr.tags('tag-replace',
                           resource_name='network',
                           resource_id=net_id,
                           tags=self.tagV.tags[ix])
            net = self.cmgr.qsvc('net-show', net_id)
            self.nets[net_id] = net
            for t in self.tagV.tags[ix]:
                if t in self.G:
                    self.G[t].update([net_id])
                else:
                    self.G[t] = set([net_id])


def find_a_n_b(a_n_b, dict_set_pool):
    sets = [s for k, s in dict_set_pool.items() if k in a_n_b]
    if len(sets) > 1:
        s = sets[0]
        for s1 in sets[1:]:
            s = s.intersection(s1)
        return s
    elif len(sets) == 1:
        return sets[0]
    return None


def find_any_a_n_b(a_n_b, dict_set_pool):
    sets = [s for k, s in dict_set_pool.items() if k in a_n_b]
    if len(sets) > 1:
        s = sets[0]
        for s1 in sets[1:]:
            s = s.union(s1)
        return s
    elif len(sets) == 1:
        return sets[0]
    return None
