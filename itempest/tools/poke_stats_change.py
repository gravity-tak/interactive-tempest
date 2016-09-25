import time
from itempest.tools import build_lbaas_v2 as lbaas2
from itempest.lib import utils


def m_stats_change(nsxt_client, sect_id, rule_id, nsx_stats,
                   venus_stats=None, interval=2.5, poke_count=1000):
    t0 = time.time()
    for x in range(poke_count):
        ss = nsxt_client.get_firewall_section_rule_stats(sect_id, rule_id)
        if ss.get('session_count') != nsx_stats.get('session_count'):
            e_time = (time.time() - t0)
            ss.pop('u_schema', None)
            msg = "Take %d seconds for STATS to be updated" % int(e_time)
            utils.log_msg(msg, 'OS-Interval')
            return e_time
        ss.pop('u_schema', None)
        utils.log_msg(str(ss), 'OS-Interval')
        time.sleep(interval)
    tt = (time.time() - t0)
    raise Exception("After %d seconds, stats do not change!" % int(tt))


# support function of lbaas_v2
# nsxt_client = cmd_nsxt.NSXT('10.144.137.159', 'admin', 'Admin!23Admin')
# venus = osn.get_mcli('Venus')
# poke_http_stats_change(venus, nsx, venus_segroup_id, 'venus-lb2-http', '172.24.4.6')
def poke_http_stats_change(cmgr, nsxt_client, os_security_group_id,
                           lb2_name, web_ip, interval=2.5, poke_count=1000):
    # os_security_group_id= "35d23271-f317-464a-8456-60ff3387e15a"
    # lb2_name = 'venus-lb2-http'
    _sgroup = cmgr.qsvc('security-group-show', os_security_group_id)
    sg_rules = _sgroup['security_group_rules']
    http_rule = [x for x in sg_rules if x['port_range_min'] >= 80][0]

    filters = {'os-neutron-secgr-id': os_security_group_id}
    fw_list = nsxt_client.list_firewall_sections(**filters)
    sect_id = fw_list[0].get('id')

    fw_rules = nsxt_client.get_firewall_section_rules(sect_id)
    rule = [x for x in fw_rules if x['display_name'] == http_rule.get('id')]
    rule_id = rule[0].get('id')

    nsxt_client.get_firewall_section_rule_stats(sect_id, rule_id)

    nsx_stats = nsxt_client.get_firewall_section_rule_stats(sect_id, rule_id)
    venus_stats = cmgr.lbaas('loadbalancer-stats', lb2_name)

    lbaas2.count_http_servers(web_ip)
    m_stats_change(nsxt_client, sect_id, rule_id, nsx_stats,
                   interval=interval, poke_count=poke_count)
