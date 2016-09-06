import json
import os
import re
import platform
import tempfile

from itempest.lib import lib_networks as NET
from itempest.lib import remote_client

from tempest.lib.common.utils import data_utils
from tempest.common import waiters

USERDATA_DIR = os.environ.get('USERDATA_DIR', '/opt/stack/data')
BACKEND_RESPONSE = ('echo -ne "HTTP/1.1 200 OK\r\nContent-Length: %d\r\n'
                    'Connection: close\r\nContent-Type: text/html; '
                    'charset=UTF-8\r\n\r\n%s\r\n"; cat >/dev/null')
NC_PROCNAME_PATTERN = """^\s*(\d+)\s+cirros.* nc .*script"""
CHECK_NC_EXISTING_CMD = """ps aux | grep "nc.*script" """


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


def keypair_to_tempfile_json(keypair):
    """return tempfile of the keypair being stored."""
    prefix = "os-keypair-" + keypair['name']
    temp = tempfile.mkstemp(dir="/tmp", prefix=prefix, suffix=".json")
    os.write(temp[0], json.dumps(keypair))
    return temp[1]


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
    image_id = kwargs.pop('image_id', None)
    image_name = kwargs.pop('image_name', None)
    flavor_id = kwargs.pop('flavor_id', 1)
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
    kp_filename = keypair_to_tempfile_json(keypair)
    servers = {}
    for sid in range(1, (num_servers + 1)):
        server_name = "%s-%d" % (my_name, sid)
        server = NET.create_server_on_network(
            cmgr, network['id'], security_group_name_or_id=sg['id'],
            key_name=keypair['name'], server_name=server_name,
            image_id=image_id, image_name=image_name,
            flavor_id=flavor_id, wait_on_boot=False)
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
        keypair=keypair, kp_filename=kp_filename,
        security_group=sg,
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


# refer to scripts/lbs/README.txt to manually start web servers
def start_webservers(lb_cfg, **kwargs):
    keypair = lb_cfg['keypair']
    private_key = keypair['private_key']
    username = lb_cfg.get('username', 'cirros')
    # password = lb_cfg.get('password', 'cubswin:)')
    if kwargs.get('debug', kwargs.get('halt', False)):
        import pdb;
        pdb.set_trace()

    for (server_id, serv_fip) in lb_cfg['servers'].items():
        server = serv_fip['server']
        floatingip = serv_fip['fip']
        server_name = server['name']
        server_ip = floatingip['floating_ip_address']
        vm_fixed_ip = floatingip['fixed_ip_address']
        result = start_web_service(server_name, server_ip, username,
                                   private_key, lb_cfg['port'])
    return result


def start_server_web_service(cmgr, server_id_or_name, server_private_key,
                             username, server_port=80):
    server = cmgr.nova('server-show', server_id_or_name)
    sv_ip = {'fixed_ip': None, 'floating_ip': None}
    for sv_interface in server['addresses']:
        for addr in server['addresses'][sv_interface]:
            if 'OS-EXT-IPS:type' in addr:
                if addr['OS-EXT-IPS:type'] == 'fixed':
                    sv_ip['fixed'] = addr['addr']
                elif addr['OS-EXT-IPS:type'] == 'floating':
                    sv_ip['floating'] = addr['addr']
        if sv_ip['fixed'] and sv_ip['floating']:
            break
    if not sv_ip['floating']:
        raise Exception(
            'server[%s] does not have floatingip.' % server_id_or_name)

    server_name = server['name']
    server_ip = sv_ip['floating']
    return start_web_service(server_name, server_ip, username,
                             server_private_key, server_port)


def start_web_service(server_name, server_ip, username, server_private_key,
                      server_port=80):
    ssh_client = remote_client.RemoteClient(server_ip,
                                            username,
                                            pkey=server_private_key)
    ssh_client.validate_authentication()
    web_server_script = '/tmp/script'
    with tempfile.NamedTemporaryFile() as script:
        script.write(BACKEND_RESPONSE % (2 + len(server_name), server_name))
        script.flush()
        with tempfile.NamedTemporaryFile() as key:
            key.write(server_private_key)
            key.flush()
            remote_client.copy_file_to_host(script.name,
                                            web_server_script,
                                            server_ip,
                                            username, key.name)
    return start_netcat_server(ssh_client, web_server_script, server_port)


def start_netcat_server(ssh_client,
                        web_server_script="/tmp/script",
                        server_port=80):
    # Start netcat
    start_server = ('while true; do '
                    'sudo nc -ll -p %(port)s -e sh %(server_script)s; '
                    'done > /dev/null &')
    cmd = start_server % {'port': server_port,
                          'server_script': web_server_script}

    ssh_client.exec_command(cmd, with_prologue='')
    result = ssh_client.exec_command(CHECK_NC_EXISTING_CMD, with_prologue='')
    return result


def stop_netcat_server(ssh_client):
    result = ssh_client.exec_command(CHECK_NC_EXISTING_CMD, with_prologue='')
    for line in result.split("\n"):
        m = re.search(NC_PROCNAME_PATTERN, line, re.I)
        if m:
            nc_pid = m.group(1)
            kill_cmd = "sudo kill %s" % nc_pid
            ssh_client.exec_command(kill_cmd, with_prologue='')
    result = ssh_client.exec_command(CHECK_NC_EXISTING_CMD, with_prologue='')
    return result


def status_netcat_server(ssh_client):
    result = ssh_client.exec_command(CHECK_NC_EXISTING_CMD, with_prologue='')
    return result


def start_pyhttp_server(ssh_client, hostname, port):
    start_pyhttp_cmd = """NL=`echo -ne '\015'`
HNAME="{hostname}"
screen -m -d -S nsx-tempest -t tempest
screen -S nsx-tempest -p tempest -X logfile /tmp/lbaas-log.txt
screen -S nsx-tempest -p tempest -X log on
screen -S nsx-tempest -p tempest -X stuff "cd /tmp && echo \"$HNAME\" > /tmp/index.html && python -m SimpleHTTPServer {port} $NL"
""".format(hostname=hostname, port=port)
    ssh_client.exec_command(start_pyhttp_cmd, with_prologue='')
    return start_pyhttp_cmd


def stop_pyhttp_server(ssh_client):
    cmd = "screen -S nsx-tempest -X kill"
    ssh_client.exec_command(cmd)


def status_web_service(server_ip, username, server_private_key):
    ssh_client = remote_client.RemoteClient(server_ip,
                                            username,
                                            pkey=server_private_key)
    ssh_client.validate_authentication()
    return status_netcat_server(ssh_client)


def stop_web_service(server_ip, username, server_private_key):
    ssh_client = remote_client.RemoteClient(server_ip,
                                            username,
                                            pkey=server_private_key)
    ssh_client.validate_authentication()
    return stop_netcat_server(ssh_client)


def restart_web_service(server_ip, username, server_private_key,
                        web_server_script='/tmp/script',
                        server_port=80, stop_first=True):
    ssh_client = remote_client.RemoteClient(server_ip,
                                            username,
                                            pkey=server_private_key)

    ssh_client.validate_authentication()
    if stop_first:
        stop_netcat_server(ssh_client)
    return start_netcat_server(ssh_client, web_server_script, server_port)
