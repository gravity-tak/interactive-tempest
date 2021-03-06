from itempest import load_our_solar_system as osn
from itempest.lib import lib_net_aggr as netaggr
from itempest.lib import lib_networks
# create lb network and servers
from itempest.tools import build_lbaas_networks as lb_net
from itempest.tools import build_lbaas_v1 as lbaasv1

username = 'Venus'
password = "itempest8@OS"
test_prefix = 'lb-venus'
venus = osn.utils.get_mimic_manager_cli(osn.os_auth_url, username, password)
lb_core_network = lb_net.setup_lb_network_and_servers(venus, test_prefix)
lb_net.start_webservers(lb_core_network)

netaggr.show_toplogy(venus)
web_servers = [server
               for server_id, server
               in lb_core_network['servers'].items()]
subnet = lb_core_network['subnet']
mem_address_list = [wserv['fip']['fixed_ip_address'] for wserv in web_servers]
port = lb_core_network['port']
security_group_id = lb_core_network['security_group']['id']

# create lbaas load-balancer, listener, pool, monitor, member
lb_v = lbaasv1.create_lbv1(venus, subnet, mem_address_list,
                           prefix=test_prefix,
                           protocol_port=port, ip_version=4)
lb_vip = lb_v['vip']
vip_fip = lbaasv1.assign_floatingip_to_vip(
    venus, lb_vip, security_group_id=security_group_id)
# sshc = lib_networks.create_ssh_client(vip_fip["floating_ip_address”])
web_ip = vip_fip["floating_ip_address"]

# http "VIP address" for round-robin effects
ctx = lbaasv1.count_http_servers(web_ip, 10)
