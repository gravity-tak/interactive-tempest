import os
import platform
import tempfile
import urllib2

from itempest.commands import cmd_neutron_u1 as UQ
from tempest_lib.common.utils import data_utils

from tempest.common import commands
from tempest.common.utils.linux import remote_client
from tempest.common import waiters

USERDATA_DIR = os.environ.get('USERDATA_DIR', '/opt/stack/data')
BACKEND_RESPONSE = ('echo -ne "HTTP/1.1 200 OK\r\nContent-Length: 7\r\n'
                    'Connection: close\r\nContent-Type: text/html; '
                    'charset=UTF-8\r\n\r\n%s"; cat >/dev/null')


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
    router = cmgr.qsvc('router-create', network_name)
    cmgr.qsvc('router-gateway-set', router['id'],
              get_public_network_id(cmgr))
    cmgr.qsvc('router-interface-add', router['id'], subnet['id'])
    return (router, network, subnet)


def create_server_on_network(cmgr, network_id, server_name=None,
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


def make_ssh_keypair_external(cmgr, my_name):
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
    # ERROR at adding ssk_key generated externally
    keypair = cmgr.nova('keypair-add', ssh_key_name,
                        pub_key=ssh_key_filename_pub)
    return keypair


def make_ssh_keypair(cmgr, my_name):
    hostname = platform.node().replace("-", "_").replace(".", "_")
    ssh_key_name = hostname + "_" + my_name
    keypair = cmgr.nova('keypair-create', ssh_key_name)
    return keypair


def get_public_network_id(cmgr):
    pub_net = cmgr.qsvc('net-external-list')[0]
    return pub_net['id']


def create_floatingip_for_server(cmgr, server, public_network_id=None,
                                 **kwargs):
    public_network_id = public_network_id or get_public_network_id(cmgr)
    result = UQ.create_floatingip_for_server(
        cmgr.manager, public_network_id, server['id'])
    return result


def assign_floatingip_to_vip(cmgr, env_cfg, **kwargs):
    pass


def setup_lbv2_simple(cmgr, x_name, **kwargs):
    # cmgr = osn.demo
    username = kwargs.pop('username', 'cissors')
    my_name = data_utils.rand_name(x_name)
    cidr = kwargs.pop('cidr', '10.199.99.0/24')
    port = kwargs.pop('port', 80)
    router, network, subnet = create_networks(cmgr, my_name, cidr)
    sg = UQ.create_security_group_loginable(cmgr.manager, my_name)
    # ssh keypair
    keypair = make_ssh_keypair(cmgr, my_name)

    vm1 = create_server_on_network(cmgr, network['id'],
                                   security_group_name_or_id=sg['name'],
                                   key_name=keypair['name'],
                                   wait_on_boot=False)
    vm2 = create_server_on_network(cmgr, network['id'],
                                   security_group_name_or_id=sg['name'],
                                   key_name=keypair['name'],
                                   wait_on_boot=True)
    # servers need in status=ACTIVE before assign floatingip to them
    public_network_id = get_public_network_id(cmgr)
    fip2 = create_floatingip_for_server(cmgr, vm2, public_network_id)
    vm1 = cmgr.nova('server-show', vm1['id'])
    fip1 = create_floatingip_for_server(cmgr, vm1, public_network_id)
    lbv2_env = dict(name=my_name,
                    username=username,
                    keypair=keypair,
                    security_group=sg,
                    router=router,
                    port=port,
                    network=network,
                    subnet=subnet,
                    server1=vm1, fip1=fip1,
                    server2=vm2, fip2=fip2)
    return lbv2_env


def teardown_lbv2_simple(cmgr, env_cfg, **kwargs):
    E = env_cfg
    server_list = [x['id'] for x in (E['server1'], E['server2'])]
    for obj_id in server_list:
        cmgr.nova('server-delete-silent', obj_id)
    # make sure servers are deleted
    for obj_id in server_list:
        waiters.wait_for_server_termination(cmgr.manager.servers_client,
                                            obj_id)
    for obj in (E['fip1'], E['fip2']):
        cmgr.qsvc('floatingip-delete', obj['id'])
    UQ.delete_this_router(cmgr.manager, E['router'])
    cmgr.qsvc('net-delete', E['network']['id'])


def start_webservers(cmgr, server, env_cfg, **kwargs):
    keypair = env_cfg['keypair']
    private_key = keypair['private_key']
    password = None
    net = env_cfg['network']
    username = env_cfg['username']
    for (sv_key, fip_key) in (('server1', 'fip1'), ('server2', 'fip2')):
        server = env_cfg[sv_key]
        floatingip = env_cfg[fip_key]
        server_name = server['name']
        server_ip = floatingip['floating_ip_address']
        vm_fixed_ip = floatingip['fixed_ip_address']
        ssh_client = remote_client.RemoteClient(server_ip,
                                                username,
                                                pkey=private_key,
                                                password=password)
        with tempfile.NamedTemporaryFile() as script:
            script.write(BACKEND_RESPONSE % server_name)
            script.flush()
            with tempfile.NamedTemporaryFile() as key:
                key.write(private_key)
                key.flush()
                commands.copy_file_to_host(script.name,
                                           "/tmp/script",
                                           server_ip,
                                           username, key.name)

        # Start netcat
        start_server = ('while true; do '
                        'sudo nc -ll -p %(port)s -e sh /tmp/%(script)s; '
                        'done > /dev/null &')
        cmd = start_server % {'port': env_cfg['port'],
                              'script': 'script1'}

        ssh_client.exec_command(cmd)
