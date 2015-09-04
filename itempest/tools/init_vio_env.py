import copy
import ConfigParser
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

VIO1 = dict(
    gateway='10.158.57.253',
    nameservers=['8.8.8.8', '8.8.4.4'],
    nameservers_internal=['10.132.71.1', '10.132.71.2'],
    cidr='10.158.57.0/24',
    alloc_pools=[dict(start='10.158.57.20', end='10.158.57.34')],
)

VIO2 = dict(
    gateway='10.158.57.253',
    nameservers=['8.8.8.8', '8.8.4.4'],
    nameservers_internal=['10.132.71.1', '10.132.71.2'],
    cidr='10.158.57.0/24',
    alloc_pools=[dict(start='10.158.57.40', end='10.158.57.54')],
)

VIO3 = dict(
    gateway='10.158.57.253',
    nameservers=['8.8.8.8', '8.8.4.4'],
    nameservers_internal=['10.132.71.1', '10.132.71.2'],
    cidr='10.158.57.0/24',
    alloc_pools=[dict(start='10.158.57.60', end='10.158.57.74')],
)

# ConfigParser raise exception for session name as DEFAULT
vio1_internal_conf = {
    'compute': dict(
        flavor_ref=1, image_ref='',
        flavor_ref_alt=1, image_ref_alt='',
    ),
    'compute-admin': dict(
        username='admin', password='2os@VMware', tanant_name='admin',
    ),
    'network': dict(
        public_network_id='',
    ),
    'nsxv': dict(
        manager_uri='https://10.133.236.114',
        vdn_scope_id='vdnscope-1',
        vlan_physical_network='dvs-109',
        flat_network_alloc_pool='10.158.57.253 10.158.57.35 10.158.57.39 '
                                '10.158.57.0/24'
    ),
    'identity': dict(
        disable_ssl_certificate_validation=True,
        v2_admin_endpoint_type='adminURL',
        v2_public_endpoint_type='internalURL',
        uri_v3='http://10.133.236.20:35357/v3/',
        uri='http://10.133.236.20:35357/v2.0/',
    ),
}
vio2_internal_conf = {
    'compute': dict(
        flavor_ref=1, image_ref='',
        flavor_ref_alt=1, image_ref_alt='',
    ),
    'compute-admin': dict(
        username='admin', password='2os@VMware', tanant_name='admin',
    ),
    'network': dict(
        public_network_id='',
    ),
    'nsxv': dict(
        manager_uri='https://10.133.236.115',
        vdn_scope_id='vdnscope-1',
        vlan_physical_network='dvs-109',
        flat_network_alloc_pool='10.158.57.253 10.158.57.55 10.158.57.59 '
                                ' 10.158.57.0/24'
    ),
    'identity': dict(
        disable_ssl_certificate_validation=True,
        v2_admin_endpoint_type='adminURL',
        v2_public_endpoint_type='internalURL',
        uri_v3='http://10.133.236.60:35357/v3/',
        uri='http://10.133.236.60:35357/v2.0/',
    ),
}
vio3_internal_conf = {
    'compute': dict(
        flavor_ref=1, image_ref='',
        flavor_ref_alt=1, image_ref_alt='',
    ),
    'compute-admin': dict(
        username='admin', password='2os@VMware', tanant_name='admin',
    ),
    'network': dict(
        public_network_id='',
    ),
    'nsxv': dict(
        manager_uri='https://10.133.236.116',
        vdn_scope_id='vdnscope-1',
        vlan_physical_network='dvs-109',
        flat_network_alloc_pool='10.158.57.253 10.158.57.75 10.158.57.79 '
                                ' 10.158.57.0/24'
    ),
    'identity': dict(
        disable_ssl_certificate_validation=True,
        v2_admin_endpoint_type='adminURL',
        v2_public_endpoint_type='internalURL',
        uri_v3='http://10.133.236.40:35357/v3/',
        uri='http://10.133.236.40:35357/v2.0/',
    ),
}


def build_tempest_conf(tempest_conf_fname, from_template,
                       conf_defaults=None, **kwargs):
    t_template = (
        from_template if type(from_template) in (str, unicode) else
        'itempest/_local/rc/vio/tempest-internal.conf.sample')
    conf_defaults = conf_defaults if type(conf_defaults) is dict else None
    cp = ConfigParser.ConfigParser()
    cp.readfp(open(t_template))
    for sess in kwargs.keys():
        if not cp.has_section(sess):
            cp.add_section(sess)
        for k, v in kwargs[sess].items():
            cp.set(sess, k, v)
    # update default; hacking
    if conf_defaults:
        for k,v in conf_defaults.items():
            cp._defaults[k] = str(v)
    # write conf to tempest_conf
    with open(tempest_conf_fname, 'wb') as configfile:
        cp.write(configfile)
    return tempest_conf_fname


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


# beaware cli_mgr is managing vio1
def init_vio1(cli_mgr, **kwargs):
    if 'tempest_conf' not in kwargs:
        kwargs['tempest_conf'] = 'itempest/etc/tempest-vio1-internal.conf'
    conf_defaults = dict(
        log_file='itempest-vio1-internal.log',
        lock_path='/opt/stack/data/itempest-vio1-internal',
    )
    return init_vio_tempest_env(cli_mgr, VIO1, vio1_internal_conf,
                                conf_defaults=conf_defaults, **kwargs)


# beaware cli_mgr is managing vio2
def init_vio2(cli_mgr, **kwargs):
    if 'tempest_conf' not in kwargs:
        kwargs['tempest_conf'] = 'itempest/etc/tempest-vio2-internal.conf'
    conf_defaults = dict(
        log_file='itempest-vio2-internal.log',
        lock_path='/opt/stack/data/itempest-vio2-internal',
    )
    return init_vio_tempest_env(cli_mgr, VIO2, vio2_internal_conf,
                                conf_defaults=conf_defaults, **kwargs)


# beaware cli_mgr is managing vio3
def init_vio3(cli_mgr, **kwargs):
    if 'tempest_conf' not in kwargs:
        kwargs['tempest_conf'] = 'itempest/etc/tempest-vio3-internal.conf'
    conf_defaults = dict(
        log_file='itempest-vio3-internal.log',
        lock_path='/opt/stack/data/itempest-vio3-internal',
    )
    return init_vio_tempest_env(cli_mgr, VIO3, vio3_internal_conf,
                                conf_defaults=conf_defaults, **kwargs)


# assume you run this def from parent of itempest dir
def init_vio_tempest_env(cli_mgr, vio_net_conf, conf_conf,
                         conf_defaults=None, **kwargs):
    xnet_name = kwargs.pop('public_net_name', 'public')
    xsubnet_name = kwargs.pop('public_subnet_name', 'public-subnet')
    use_internal_dns = kwargs.pop('use_internal_dns', False)
    img_name = kwargs.pop('image_name', 'cirros-0.3.3-x86_64-disk')
    from_template = kwargs.pop('tempest_sample',
                               'itempest/etc/tempest-internal.conf.sample')
    tempest_conf = kwargs.pop('tempest_conf',
                              'itempest/etc/itempest-internal.conf')
    net = cli_mgr.qsvc('net-list', name=xnet_name)
    if len(net) == 0:
        net = cli_mgr.qsvc('net-create', xnet_name,
                           **{'router:external': True, 'shared': False})
    else:
        net = net[0]
    snet = cli_mgr.qsvc('subnet-list', name=xsubnet_name)
    if len(snet) == 0:
        dns_nameservers = (
            vio_net_conf['nameservers_internal'] if use_internal_dns else
            vio_net_conf['nameservers'])
        snet = cli_mgr.qsvc('subnet-create', net['id'],
                            name=xsubnet_name,
                            cidr=vio_net_conf['cidr'],
                            gateway_ip=vio_net_conf['gateway'],
                            dns_nameservers=dns_nameservers,
                            allocation_pools=vio_net_conf['alloc_pools'],
                            enable_dhcp=False)
    else:
        snet = snet[0]
    # let it fail, if not found
    img = U.fgrep(cli_mgr.nova('image-list'), name=img_name)[0]
    vio_iconf = copy.deepcopy(conf_conf)
    vio_iconf['compute']['image_ref'] = img['id']
    vio_iconf['compute']['image_ref_alt'] = img['id']
    vio_iconf['network']['public_network_id'] = net['id']
    conf_name = build_tempest_conf(tempest_conf, from_template,
                                   conf_defaults, **vio_iconf)
    net = cli_mgr.qsvc('net-list', name=xnet_name)[0]
    return (conf_name, net)
