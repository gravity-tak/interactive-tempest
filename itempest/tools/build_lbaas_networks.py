import os
import platform
import shlex
import subprocess
import tempfile

from itempest.lib import lib_networks as NET
from itempest.lib import remote_client
from tempest.lib.common.utils import data_utils

# from tempest.common.utils.linux import remote_client as os_remote_client
from tempest.common import waiters
from tempest import exceptions


USERDATA_DIR = os.environ.get('USERDATA_DIR', '/opt/stack/data')
BACKEND_RESPONSE = ('echo -ne "HTTP/1.1 200 OK\r\nContent-Length: %d\r\n'
                    'Connection: close\r\nContent-Type: text/html; '
                    'charset=UTF-8\r\n\r\n%s\r\n"; cat >/dev/null')


def create_networks(cmgr, network_name, cidr, **kwargs):
    router_type = kwargs.pop('router_type', 'shared')
    public_network_id = kwargs.pop('public_network_id', None)
    network, subnet = NET.create_mtz_networks(cmgr, cidr,
                                              name=network_name,
                                              **kwargs)
    net_list = [(network, subnet)]
    router = NET.create_router_and_add_interfaces(
        cmgr, network_name, net_list,
        public_network_id=public_network_id, router_type=router_type)
    return (router, network, subnet)


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


# lb_env = setup_lb_servers(venus, "lbv2", num_servers=2)
def setup_lb_network_and_servers(cmgr, x_name, **kwargs):
    num_servers = kwargs.pop('num_servers', 2)
    username = kwargs.pop('username', 'cirros')
    password = kwargs.pop('password', 'cubswin:)')
    my_name = data_utils.rand_name(x_name)
    cidr = kwargs.pop('cidr', '10.199.88.0/24')
    port = kwargs.pop('port', 80)
    public_network_id = kwargs.pop('public_network_id', None)
    # NSX-v plugin need to use exclusive router for its lbaas env
    # Overwrite it if your env requiring a different type
    router_type = kwargs.pop('router_type', 'exclusive')
    router, network, subnet = create_networks(cmgr, my_name, cidr,
                                              router_type=router_type,
                                              **kwargs)
    sg = NET.create_security_group_loginable(cmgr, my_name, http=True)
    # ssh keypair
    keypair = make_ssh_keypair(cmgr, my_name)

    servers = {}
    for sid in range(1, (num_servers + 1)):
        server_name = "%s-%d" % (my_name, sid)
        server = NET.create_server_on_network(
            cmgr, network['id'], security_group_name_or_id=sg['id'],
            key_name=keypair['name'], server_name=server_name,
            wait_on_boot=False)
        servers[server['id']] = dict(server=server, fip=None)

    # servers need in status=ACTIVE before assign floatingip to them
    # vm1 should be active by now
    for server_id in servers.keys():
        waiters.wait_for_server_status(
            cmgr.manager.servers_client, server_id, 'ACTIVE')

    for server_id, server in servers.items():
        server['fip'] = NET.create_floatingip_for_server(cmgr, server_id,
                                                         public_network_id)
        server['server'] = cmgr.nova('server-show', server_id)

    lb_env = dict(
        name=my_name, username=username, password=password,
        keypair=keypair, security_group=sg,
        router=router, port=port, network=network, subnet=subnet,
        servers=servers)
    return lb_env


def teardown_lb_servers(cmgr, env_cfg, **kwargs):
    E = env_cfg
    server_list = [x['id'] for x in (E['server1'], E['server2'])]
    for obj_id in server_list:
        cmgr.nova('server-delete-silent', obj_id)
    # make sure all servers are terminated.
    for obj_id in server_list:
        waiters.wait_for_server_termination(cmgr.manager.servers_client,
                                            obj_id)
    for obj in (E['fip1'], E['fip2']):
        cmgr.qsvc('floatingip-delete', obj['id'])
    NET.delete_this_router(cmgr, E['router'])
    cmgr.qsvc('net-delete', E['network']['id'])


def start_webservers(lb_cfg, **kwargs):
    keypair = lb_cfg['keypair']
    private_key = keypair['private_key']
    username = lb_cfg.get('username', 'cirros')
    # password = lb_cfg.get('password', 'cubswin:)')

    for (server_id, serv_fip) in lb_cfg['servers'].items():
        server = serv_fip['server']
        floatingip = serv_fip['fip']
        server_name = server['name']
        server_ip = floatingip['floating_ip_address']
        vm_fixed_ip = floatingip['fixed_ip_address']

        ssh_client = remote_client.RemoteClient(server_ip,
                                                username,
                                                pkey=private_key)
        ssh_client.validate_authentication()
        web_server_script = '/tmp/script'
        with tempfile.NamedTemporaryFile() as script:
            script.write(BACKEND_RESPONSE % (2+len(server_name), server_name))
            script.flush()
            with tempfile.NamedTemporaryFile() as key:
                key.write(private_key)
                key.flush()
                copy_file_to_host(script.name,
                                  web_server_script,
                                  server_ip,
                                  username, key.name)
        # Start netcat
        start_server = ('while true; do '
                        'sudo nc -ll -p %(port)s -e sh %(server_script)s; '
                        'done > /dev/null &')
        cmd = start_server % {'port': lb_cfg['port'],
                              'server_script': web_server_script}

        ssh_client.exec_command(cmd)


def copy_file_to_host(file_from, dest, host, username, pkey):
    dest = "%s@%s:%s" % (username, host, dest)
    cmd = "scp -v -o UserKnownHostsFile=/dev/null " \
          "-o StrictHostKeyChecking=no " \
          "-i %(pkey)s %(file1)s %(dest)s" % {'pkey': pkey,
                                              'file1': file_from,
                                              'dest': dest}
    args = shlex.split(cmd.encode('utf-8'))
    subprocess_args = {'stdout': subprocess.PIPE,
                       'stderr': subprocess.STDOUT}
    proc = subprocess.Popen(args, **subprocess_args)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise exceptions.CommandFailed(cmd,
                                       proc.returncode,
                                       stdout,
                                       stderr)
    return stdout
