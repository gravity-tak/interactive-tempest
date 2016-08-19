from itempest import load_our_solar_system as osn
from itempest.lib import lib_networks as NETS

demo = osn.get_mcli('demo', password='openstack')
pub = demo.qsvc('net-show public')
mynet = demo.qsvc('net-show private')

fip_list = []
for ix in range(6):
    fip = demo.qsvc('floatingip-create', pub['id'])
    fip_list.append(fip)

from operator import itemgetter

fip2_list = sorted(fip_list, key=itemgetter('floating_ip_address'),
                   reverse=True)

demo_sg = NETS.create_security_group_loginable(demo, 'demo_sg_login')
demo_img = demo.nova('image-list', name=u'cirros-0.3.3-x86_64-disk')[0]

server_list = []
for ix in range(6):
    sv_name = 'demo-sv-%d' % ix
    server = NETS.create_server_on_network(demo, mynet['id'], sv_name,
                                           image_id=demo_img['id'],
                                           security_group_name_or_id=demo_sg[
                                               'id'],
                                           wait_on_boot=False)
    server_list.append(server)

# waitfor all servers become ACTIVE
fip3 = {}
for ix in range(6):
    fip = NETS.associate_floatingip_to_server(demo, fip_list[ix],
                                              server_list[ix])
    fip3[fip.get('floating_ip_address')] = fip_list
