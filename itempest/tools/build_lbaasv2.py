import os
import platform

from itempest.commands import cmd_neutron_u1 as UQ
from tempest_lib.common.utils import data_utils

USERDATA_DIR = os.environ.get('USERDATA_DIR', '/opt/stack/data')


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


def make_ssh_key_pair(cmgr, my_name):
    hostname = platform.node().replace("-", "_").replace(".", "_")
    ssh_key_dir = os.path.join(USERDATA_DIR, 'lbaas_itempest')
    # os.makedirs(ssh_key_dir, 0755, exist_ok=True)
    if not os.path.exists(ssh_key_dir):
        os.makedirs(ssh_key_dir, 0755)
    ssh_key_name = hostname + "_" + my_name
    ssh_key_filename = os.path.join(ssh_key_dir, ssh_key_name)
    ssh_key_filename_pub = ssh_key_filename + ".pub"
    if os.path.exists(ssh_key_filename):
        os.remove(ssh_key_filename)
    if os.path.exists(ssh_key_filename_pub):
        os.remove(ssh_key_filename_pub)
    os.system('ssh-keygen -t rsa -f %s -N ""' % ssh_key_filename)
    keypair = cmgr.nova('keypair-add', ssh_key_name,
                        pub_key=ssh_key_filename_pub)
    return keypair


def setup_lbv2_simple(cmgr, x_name, **kwargs):
    # cmgr = osn.demo
    my_name = data_utils.rand_name(x_name)
    cidr = kwargs.pop('cidr', '10.199.99.0/24')
    n1, s1 = create_networks(cmgr, my_name, cidr)
    sg = UQ.create_security_group_loginable(cmgr.manager, my_name)
    # ssh keypair
    keypair = make_ssh_key_pair(cmgr, my_name)

    vm1 = create_server_on_network(cmgr, n1['id'],
                                   security_group_name_or_id=sg['name'],
                                   key_name=keypair['name'])
    vm2 = create_server_on_network(cmgr, n1['id'],
                                   security_group_name_or_id=sg['name'],
                                   key_name=keypair['name'])
    lbv2_env = dict(name=my_name,
                    keypair=keypair,
                    security_group=sg,
                    net1=n1, snet1=s1,
                    vm1=vm1, vm2=vm2)
    return lbv2_env


def teardown_lbv2_simple(cmgr, env_cfg):
    pass
