from itempest.lib import cmd_glance
from itempest.lib import cmd_keystone
from itempest.lib import cmd_neutron
from itempest.lib import cmd_neutron_u1
from itempest.lib import cmd_nova
from itempest.lib import utils as U

from itempest import icreds


test_images = {
    'ubuntu-14.04-x86_64': {
        'container_format': 'bare',
        'disk_format': 'vmdk',
        'location': 'http://10.34.57.171/images/ubuntu-14.04-x86_64.vmdk',
        'is_public': True,
    },
    'cirros-0.3.3-x86_64-disk': {
        'container_format': 'bare',
        'disk_format': 'vmdk',
        'location': 'http://10.34.57.161/images/cirros-0.3.3-x86_64-disk.vmdk',
        'is_public': True,
    },
}

vio2 = dict(
    gateway='10.158.57.253',
    nameservers=['8.8.8.8', '8.8.4.4'],
    nameservers_internal=['10.132.71.1', '10.132.71.2'],
    cidr='10.158.57.0/24',
    alloc_pools=[dict(start='10.158.57.40', end='10.158.57.54')],
)


class InfoBase(object):
    def __init__(self, **kwargs):
        for k,v in (kwargs.items()):
            setattr(self, k, v)

    def __eq__(self, other):
        return str(self) == str(other)


def get_commands(os_auth_url, os_name, os_password,
                 os_tenant_name=None, *kwargs):
    client_mgr = icreds.get_client_mgr(os_auth_url,
                                           os_name, os_password,
                                           tenant_name=os_tenant_name,
                                           **kwargs)
    qsvc = get_qsvc_command(client_mgr)
    nova = get_nova_command(client_mgr)
    keys = get_keys_command(client_mgr)
    return (client_mgr, qsvc, nova, keys)


def get_glance_command(client_mgr, log_cmd="OS-Glance", **kwargs):
    return U.command_wrapper(client_mgr, cmd_glance,
                             log_cmd=log_cmd)

def get_qsvc_command(client_mgr, log_cmd="OS-Neutron", **kwargs):
    return U.command_wrapper(client_mgr,
                             [cmd_neutron, cmd_neutron_u1],
                             log_cmd=log_cmd)

def get_nova_command(client_mgr, log_cmd="OS-Nova", **kwargs):
    return U.command_wrapper(client_mgr, cmd_nova,
                             log_cmd=log_cmd)

def get_keys_command(client_mgr, log_cmd="OS-Keystone", **kwargs):
    return U.command_wrapper(client_mgr, cmd_keystone,
                             log_cmd=log_cmd)

def create_image(glance, img_name, **create_kwargs):
    exact_img_name = r"\^%s\$" % img_name
    imgs = U.fgrep(glance('image-list'), name=exact_img_name)
    if len(imgs) > 0:
        return imgs[0]
    container_format = create_kwargs.pop('container_format', 'bare')
    # TODO(akang): properies are wrong, how to get correct values?
    disk_format = create_kwargs.pop('disk_format', 'raw')
    if disk_format == 'vmdk':
        create_kwargs['property'] = dict(
            vmware_disktype='sparse',
            vmware_adaptertype='ide')
    img = glance('image-create', img_name, container_format, disk_format,
               **create_kwargs)
    return img


def get_image(nova, img_name):
    image_list = nova('image-list')
    if image in image_list:
        if image['name'] == img_name:
            return image_list
    return {}


def init_vio2_env(os_auth_url, os_name, os_password,
                  os_tenant_name=None, **kwargs):
    client_mgr = icreds.get_client_manager(os_auth_url,
                                          os_name, os_password,
                                          tenant_name=os_tenant_name,
                                          **kwargs)
    qsvc = get_qsvc_command(client_mgr)
    nova = get_nova_command(client_mgr)
    glance = get_glance_command(client_mgr)

    # let's consider net-create-or-show
    # why not net-list-or-create, because it imply result of list-of-dict
    net = qsvc('net-list --name=public')
    if len(net) == 0:
        net = qsvc('net-create', 'public',
                   **{'router:external': True, 'shared':False})
    else:
        net = net[0]
    snet = qsvc('subnet-list --name=public-subnet')
    if len(snet) == 0:
        snet = qsvc('subnet-create', net['id'],
                    name='public-subnet',
                    cidr=vio2['cidr'],
                    gateway_ip=vio2['gateway'],
                    dns_nameservers=vio2['nameservers'],
                    allocation_pools=vio2['alloc_pools'],
                    enable_dhcp=False)
    else:
        snet = snet[0]
    img_list = []
    for img_name, img_dict in test_images.items():
        img_list.append(create_image(glance, img_name, **img_dict))
    return (net, snet, img_list)
