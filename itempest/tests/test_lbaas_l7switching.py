from itempest.tools import build_lbaas_l7 as ll7
from itempest.tools import build_lbaas_v2 as lbaas2
from itempest.lib import lib_net_aggr as netaggr


def test_lbaas_l7switching(cmgr, lb_name, image_name=None, platform='os'):
    lb_name = lb_name or 'cmgr-lb2-http'

    if platform == 'nsx':
        image_name = image_name or u'cirros-0.3.3-x86_64-disk'
        venus_lb2 = lbaas2.build_nsx_lbaas(cmgr, lb_name,
                                           image_name=image_name)
    else:
        image_name = image_name or "cirros-0.3.3-x86_64-ESX"
        venus_lb2 = lbaas2.build_os_lbaas(cmgr, lb_name,
                                          image_name=image_name)

    http_server_list = [x for x in venus_lb2['network']['servers']]

    netaggr.show_toplogy(cmgr)
    lbaas2.show_lbaas_tree(cmgr, lb_name)
    cmgr.lbaas('loadbalancer-status', lb_name)
    vip_public_ip = lbaas2.get_loadbalancer_floatingip(
        cmgr, lb_name)[1][u'floating_ip_address']

    net_name = venus_lb2['network']['network']['name']
    on_network_id = venus_lb2['network']['network']['id']
    # on_network_id = venus.qsvc('net-list', name=net_name)[0]['id']

    sg_id = venus_lb2['network']['security_group']['id']
    # sg_id = venus.qsvc('security-group-list', name=net_name)[0]['id']

    keypair_name = venus_lb2['network']['keypair_name']

    venus_lb2a = lbaas2.LB_NET.add_server_to_lb_network(
        cmgr, on_network_id, sg_id, ('A',),
        keypair_name=keypair_name, image_name=image_name)

    lb = cmgr.lbaas('loadbalancer-show', lb_name)
    lb_id = lb.get('id')
    vip_subnet_id = lb.get('vip_subnet_id')
    redirect_to_listener_id = lb.get('listeners')[0].get('id')
    l7_server_list = [x for x in venus_lb2a['servers']]

    l7_cfg = ll7.build_l7_switching(
        cmgr, vip_subnet_id, lb_id,
        redirect_to_listener_id, l7_server_list)

    ll7.run_l7_switching(http_server_list, vip_public_ip, '')
    ll7.run_l7_switching(http_server_list, vip_public_ip, 'v2/api')
    ll7.run_l7_switching(l7_server_list, vip_public_ip, 'api')
    ll7.run_l7_switching(l7_server_list, vip_public_ip, 'api/firewalls')

    return dict(
        name=lb_name, image_name=image_name,
        vip_public_ip=vip_public_ip, keypair_name=keypair_name,
        network_id=on_network_id, subnet_id=vip_subnet_id,
        security_group_id=sg_id,
        http_server_list=http_server_list,
        l7_server_list=l7_server_list, l7_pool=l7_cfg.get('pool')
    )