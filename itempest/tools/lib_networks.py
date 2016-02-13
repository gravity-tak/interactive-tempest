from tempest_lib.common.utils import data_utils


def create_router_and_add_interfaces(cmgr, name, net_list):
    name = name or data_utils.rand_name('itempz-r')
    router = cmgr.qsvc('router-create', name)
    cmgr.qsvc('router-gateway-set', router['id'],
              get_public_network_id(cmgr))
    for network, subnet in net_list:
        cmgr.qsvc('router-interface-add', router['id'], subnet['id'])
    return router


def create_server_on_network(cmgr, network_id, server_name=None,
                             image_id=None, flavor_id=1,
                             security_group_name_or_id=None,
                             wait_on_boot=False, **kwargs):
    server_name = server_name or data_utils.rand_name('itempz-sv')
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


def create_floatingip_for_server(cmgr, server,
                                 public_network_id=None, **kwargs):
    public_network_id = public_network_id or get_public_network_id(cmgr)
    result = UQ.create_floatingip_for_server(
        cmgr.manager, public_network_id, server['id'])
    return result


def get_public_network_id(cmgr):
    pub_net = cmgr.qsvc('net-external-list')[0]
    return pub_net['id']


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

