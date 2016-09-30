from itempest.tools import build_lbaas_l7 as ll7
from itempest.tools import build_lbaas_v2 as lbaas2
from itempest.lib import lib_net_aggr as netaggr
from itempest.lib import lib_networks as NETS


def test_lbaas_l7switching(cmgr, lb_name, image_name=None, platform='os',
                           **kwargs):
    lb_name = lb_name or 'cmgr-lb2-http'
    build_cfg = dict(groupid=1, group_num_sever=2, num_servers=4)
    build_cfg.update(**kwargs)
    if platform == 'nsx':
        image_name = image_name or u'cirros-0.3.3-x86_64-disk'
        lb2_config = lbaas2.build_nsx_lbaas(
            cmgr, lb_name, image_name=image_name, **kwargs)
    else:
        image_name = image_name or "cirros-0.3.3-x86_64-ESX"
        lb2_config = lbaas2.build_os_lbaas(
            cmgr, lb_name, image_name=image_name, **kwargs)
    keypair = lb2_config['network']['keypair']
    security_group_id = lb2_config['network']['security_gropu'].get('id')
    http_server_id_list = lb2_config.get('group_server_id_list')
    l7_server_id_list = lb2_config.get('other_server_id_list')

    netaggr.show_toplogy(cmgr)
    lbaas2.show_lbaas_tree(cmgr, lb_name)
    cmgr.lbaas('loadbalancer-status', lb_name)
    vip_public_ip = lbaas2.get_loadbalancer_floatingip(
        cmgr, lb_name)[1][u'floating_ip_address']

    lb = cmgr.lbaas('loadbalancer-show', lb_name)
    lb_id = lb.get('id')
    vip_subnet_id = lb.get('vip_subnet_id')
    redirect_to_listener_id = lb.get('listeners')[0].get('id')

    l7_cfg = ll7.build_l7_switching(
        cmgr, vip_subnet_id, lb_id,
        redirect_to_listener_id, l7_server_id_list)

    ll7.run_l7_switching(http_server_id_list, vip_public_ip, '')
    ll7.run_l7_switching(http_server_id_list, vip_public_ip, 'v2/api')
    ll7.run_l7_switching(l7_server_id_list, vip_public_ip, 'api')
    ll7.run_l7_switching(l7_server_id_list, vip_public_ip, 'api/firewalls')

    return dict(
        name=lb_name, image_name=image_name, keypair=keypair,
        vip_public_ip=vip_public_ip,
        subnet_id=vip_subnet_id,
        security_group_id=security_group_id,
        http_server_list=http_server_id_list,
        l7_server_list=l7_server_id_list, l7_pool=l7_cfg.get('pool')
    )


def cleanup_lbaas_l7switching(adm_mgr, cmgr):
    lbaas2.delete_all_lbaas(cmgr)
    NETS.destroy_all_resources(adm_mgr, tenant_id=cmgr.tenant_id)
