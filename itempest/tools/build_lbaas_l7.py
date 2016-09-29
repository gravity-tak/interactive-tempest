from itempest.lib import utils
from itempest.tools import build_lbaas_v2 as lbaas2


def test_lbaas_l7(cmgr, subnet_id, http_server_list, l7_server_list,
                  security_group_id, lb_name=None, lb_timeout=900,
                  protocol='HTTP', protocol_port=80, ip_version=4,
                  delay=4, max_retries=3, monitor_type="PING",
                  monitor_timeout=10, public_network_id=None, **kwargs):
    public_network_id = kwargs.pop('public_network_id', None)
    lb_name = lb_name if lb_name else lbaas2.data_utils.rand_name('lb2')
    load_balancer = cmgr.lbaas('loadbalancer-create', subnet_id,
                               name=lb_name)
    loadbalancer_id = load_balancer['id']
    cmgr.lbaas('loadbalancer_waitfor_active', loadbalancer_id,
               timeout=lb_timeout)
    fip = lbaas2.assign_floatingip_to_vip(cmgr, lb_name,
                                          public_network_id=public_network_id,
                                          security_group_id=security_group_id)
    lb_vip_address = fip.get('floating_ip_address')
    # create pool/listern/http_server_list for all http traffic
    listener1 = cmgr.lbaas('listener-create', name='listener1',
                           loadbalancer_id=loadbalancer_id, protocol=protocol,
                           protocol_port=protocol_port)
    cmgr.lbaas('loadbalancer_waitfor_active', loadbalancer_id,
               timeout=lb_timeout)
    pool1 = cmgr.lbaas('pool-create', name='pool1',
                       lb_algorithm='ROUND_ROBIN',
                       listener_id=listener1.get('id'), protocol=protocol)
    cmgr.lbaas('loadbalancer_waitfor_active', loadbalancer_id,
               timeout=lb_timeout)
    member1_list = []
    for sv_id in http_server_list:
        server = cmgr.nova('server-show', sv_id)
        fixed_ip_address = lbaas2.LB_NET.get_server_ip_address(server,
                                                               'fixed')
        member = cmgr.lbaas('member-create', pool1.get('id'),
                            subnet_id=subnet_id,
                            address=fixed_ip_address,
                            protocol_port=protocol_port)
        member1_list.append(member)
        cmgr.lbaas('loadbalancer_waitfor_active', loadbalancer_id,
                   timeout=lb_timeout)
    run_cnt = 10
    cnt_dict = lbaas2.count_http_servers(lb_vip_address, run_cnt)
    tot_cnt = 0
    for sn, cnt in cnt_dict.items():
        tot_cnt += cnt
    if (not tot_cnt == run_cnt):
        raise Exception("Expect %d responses, got %d" % (run_cnt, tot_cnt))

    build_l7_switching(cmgr, subnet_id, loadbalancer_id, listener1.get('id'),
                       l7_server_list, protocol=protocol,
                       protocol_port=protocol_port, lb_timeout=lb_timeout)

    # test l7 forwarding depending on URL prefix
    run_l7_switching(http_server_list, lb_vip_address, '')
    run_l7_switching(http_server_list, lb_vip_address, 'xapi')
    run_l7_switching(l7_server_list, lb_vip_address, 'api')


def build_l7_switching(cmgr, subnet_id, loadbalancer_id,
                       redirector_to_listener_id, l7_server_list,
                       protocol='HTTP', protocol_port=80,
                       pool_l7='pool-7',
                       lb_timeout=900):
    # build_l7_pool(loadbalancer_id):
    pool2 = cmgr.lbaas('pool-create', name=pool_l7,
                       lb_algorithm='ROUND_ROBIN',
                       loadbalancer_id=loadbalancer_id, protocol=protocol)
    cmgr.lbaas('loadbalancer_waitfor_active', loadbalancer_id,
               timeout=lb_timeout)
    member2_list = []
    for sv_id in l7_server_list:
        server = cmgr.nova('server-show', sv_id)
        fixed_ip_address = lbaas2.LB_NET.get_server_ip_address(server,
                                                               'fixed')
        member = cmgr.lbaas('member-create', pool2.get('id'),
                            subnet_id=subnet_id,
                            address=fixed_ip_address,
                            protocol_port=protocol_port)
        member2_list.append(member)
        cmgr.lbaas('loadbalancer_waitfor_active', loadbalancer_id,
                   timeout=lb_timeout)
    policy1 = cmgr.lbaas('l7policy-create', action="REDIRECT_TO_POOL",
                         redirect_pool_id=pool2.get('id'),
                         listener_id=redirector_to_listener_id,
                         name='policy1')
    cmgr.lbaas('l7rule-create', policy1.get('id'), type="PATH",
               compare_type="STARTS_WITH", value="/api")

    return dict(pool=pool2, members=member2_list, policy=policy1)


def run_l7_switching(on_server_list, lb_vip_address, url_path=''):
    resp_urls = lbaas2.count_http_servers(lb_vip_address, 2, url_path)
    if not url_responses_are_OK(resp_urls, on_server_list):
        utils.log_msg("http://%s/%s redirected to wrong pool",
                      (lb_vip_address, ''))


# the servers in tests will resopnse its OpenStack Server's name
def url_responses_are_OK(resp_urls, target_server_list):
    for url_resp, resp_cnt in resp_urls.items():
        if not url_resp in target_server_list:
            return False
    return True
