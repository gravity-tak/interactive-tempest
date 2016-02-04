from tempest_lib.common.utils import data_utils


def create_networks(cmgr, network_name, cidr, **kwargs):
    network_cfg = {}
    for k in kwargs.keys():
        if k.find('provider') >= 0 or k.find(
                'vlan-transparent') >= 0 or k.find('router:external') >= 0:
            network_cfg[k] = kwargs.pop(k)
    network = cmgr.qsvc('net-create', name=network_name, **network_cfg)
    subnet = cmgr.qsvc('subnet-create', network['id'], cidr,
                       name=network_name, **kwargs)
    network = cmgr.qsvc('net-show', network['id'])
    return (network, subnet)


def create_server_on_interface(cmgr, network_id, server_name=None,
                               image_id=None, flavor_id=1,
                               security_group_name_or_id=None,
                               wait_on_boot=False, **kwargs):
    server_name = server_name or data_utils.rand_name('lbv2-sv')
    security_group_name_or_id = security_group_name_or_id or 'default'
    network = cmgr.qsvc('net-show', network_id)
    create_kwargs = {
        'networks': [{'uuid': network['id']}],
        'security_groups': [{'name': security_group_name_or_id}],
    }
    image_id = get_image_id(cmgr, image_id)
    flavor_id = get_flavor_id(cmgr, flavor_id)
    create_kwargs.update(**kwargs)
    return cmgr.nova('server_create', server_name, image_id=image_id,
                     flavor_id=flavor_id, wait_on_boot=wait_on_boot,
                     **create_kwargs)


def get_flavor_id(cmgr, flavor=None):
    if type(flavor) is int:
        return flavor
    if type(flavor) in (str, unicode) and flavor.isdigit():
        return int(flavor)
    for f in cmgr.nova('flavor-list'):
        if f['name'].find(flavor) >= 0:
            return int(f['id'])
    return 1


def get_image_id(cmgr, image_name=None):
    image_list = cmgr.nova('image-list')
    image_name = image_name or 'cirros'
    for image in image_list:
        if image['name'] == image_name:
            return image['id']
    for image in image_list:
        if image['name'].find(image_name) >= 0:
            return image['id']
    return None


def create_lbv2_simple(cmgr):
    # cmgr = osn.demo
    n1,s1 = blb.create_networks(cmgr, 'lbv2-net', '10.199.99.0/24')
    v1 = blb.create_server_on_network(cmgr, n1['id'])
    v2 = blb.create_server_on_network(cmgr, n1['id'])
    return(n1,s1,v1,v2)
