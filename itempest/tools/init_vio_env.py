from itempest.lib import utils as U


TEST_IMAGES = {
    'ubuntu-14.04-x86_64': {
        'container_format': 'bare',
        'disk_format': 'vmdk',
        'location': 'http://10.34.57.171/images/ubuntu-14.04-x86_64.vmdk',
        'is_public': True,
    },
    'cirros-0.3.3-x86_64-disk': {
        'container_format': 'bare',
        'disk_format': 'vmdk',
        'location': 'http://10.34.57.161/images/cirros-0.3.3-x86_64-disk'
                    '.vmdk',
        'is_public': True,
    },
}

VIO2 = dict(
    gateway='10.158.57.253',
    nameservers=['8.8.8.8', '8.8.4.4'],
    nameservers_internal=['10.132.71.1', '10.132.71.2'],
    cidr='10.158.57.0/24',
    alloc_pools=[dict(start='10.158.57.40', end='10.158.57.54')],
)


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
    for image in image_list:
        if image['name'] == img_name:
            return image
    return {}


def init_vio2_env(os_auth_url, os_name, os_password,
                  os_tenant_name=None, **kwargs):
    user = U.get_commands(os_auth_url,
                          os_name, os_password,
                          os_tenant_name=os_tenant_name,
                          **kwargs)
    net = user.qsvc('net-list --name=public')
    if len(net) == 0:
        net = user.qsvc('net-create', 'public',
                        **{'router:external': True, 'shared': False})
    else:
        net = net[0]
    snet = user.qsvc('subnet-list --name=public-subnet')
    if len(snet) == 0:
        snet = user.qsvc('subnet-create', net['id'],
                         name='public-subnet',
                         cidr=VIO2['cidr'],
                         gateway_ip=VIO2['gateway'],
                         dns_nameservers=VIO2['nameservers'],
                         allocation_pools=VIO2['alloc_pools'],
                         enable_dhcp=False)
    else:
        snet = snet[0]
    img_list = []
    for img_name, img_dict in TEST_IMAGES.items():
        img_list.append(create_image(user.nova, img_name, **img_dict))
    return (net, snet, img_list)
