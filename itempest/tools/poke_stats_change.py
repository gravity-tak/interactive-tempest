import time
from itempest.tools import build_lbaas_v2 as lbaas2
from itempest.lib import utils


def m_stats_change(nsxt_client, sect_id, rule_id, nsx_stats,
                   venus_stats=None, interval=2.5, poke_count=150):
    t0 = time.time()
    for cnt in range(poke_count):
        ss = nsxt_client.get_firewall_section_rule_stats(sect_id, rule_id)
        ss.pop('_schema', None)
        ss.pop('rule_id', None)
        msg = "#%02d %s" % (cnt, str(ss))
        utils.log_msg(msg, 'CHK-Stats')
        if ss.get('session_count') != nsx_stats.get('session_count'):
            e_time = (time.time() - t0)
            msg = "Take %d seconds for STATS to be updated" % int(e_time)
            utils.log_msg(msg, 'CHK-Stats')
            return e_time
        time.sleep(interval)
    tt = (time.time() - t0)
    raise Exception("After %d seconds, stats do not change!" % int(tt))


# support function of lbaas_v2
# nsxt_client = cmd_nsxt.NSXT('10.144.137.159', 'admin', 'Admin!23Admin')
# venus = osn.get_mcli('Venus')
# poke_http_stats_change(nsx, venus, 'venus-lb2-http', '172.24.4.6',
#   interval=5.0 poke_count=100)
def poke_http_stats_change(nsxt_client, cmgr, lb2_name, web_ip,
                           interval=5.0, poke_count=100):
    # lb2_name = 'venus-lb2-http'
    lb = cmgr.lbaas('loadbalancer-show', lb2_name)
    lb_port = cmgr.qsvc('port-show', lb['vip_port_id'])
    os_security_group_id = lb_port['security_groups'][0]
    _sgroup = cmgr.qsvc('security-group-show', os_security_group_id)
    msg = "os-security-group-id = %s" % (os_security_group_id)
    utils.log_msg(msg, 'CHK-Stats')

    sg_rules = _sgroup['security_group_rules']
    http_rule = [x for x in sg_rules if x['port_range_min'] >= 80][0]

    filters = {'os-neutron-secgr-id': os_security_group_id}
    fw_list = nsxt_client.list_firewall_sections(**filters)
    sect_id = fw_list[0].get('id')

    fw_rules = nsxt_client.get_firewall_section_rules(sect_id)
    rule = [x for x in fw_rules if x['display_name'] == http_rule.get('id')]
    rule_id = rule[0].get('id')

    msg = "NSX STATS is at section[%s] rule_id[%s]" % (sect_id, rule_id)
    utils.log_msg(msg, 'CHK-Stats')
    nsx_stats = nsxt_client.get_firewall_section_rule_stats(sect_id, rule_id)
    venus_stats = cmgr.lbaas('loadbalancer-stats', lb2_name)
    msg = "OS-LB2-Stats %s" % (str(venus_stats))
    utils.log_msg(msg, 'CHK-Stats')

    lbaas2.count_http_servers(web_ip)
    m_stats_change(nsxt_client, sect_id, rule_id, nsx_stats,
                   interval=interval, poke_count=poke_count)

    venus_stats = cmgr.lbaas('loadbalancer-stats', lb2_name)
    msg = "OS-LB2-Stats %s" % (str(venus_stats))
    utils.log_msg(msg, 'CHK-Stats')
