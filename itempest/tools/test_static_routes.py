import time

from itempest import load_our_solar_system as osn
from itempest.lib import utils
from itempest.tools import simple_tenant_networks as stn

# craete Tenant Earth's tempest client manager
earth_mgr = earth1 = earth2 = None


def c_env(ctype=0):
    global earth_mgr, earth1, earth2
    if ctype >=3 :
        jfile1 = 'itempest/data/topo-ubuntu-01.json'
        jfile2 = 'itempest/data/topo-ubuntu-02.json'
    elif ctype == 2 :
        jfile1 = 'itempest/data/topo-ubuntu-01.json'
        jfile2 = 'itempest/data/topo-cirros-02.json'
    elif ctype == 2 :
        jfile1 = 'itempest/data/topo-cirros-01.json'
        jfile2 = 'itempest/data/topo-ubuntu-02.json'
    else:
        jfile1 = 'itempest/data/topo-cirros-01.json'
        jfile2 = 'itempest/data/topo-cirros-02.json'
    earth_mgr = osn.icreds.get_client_manager(osn.auth_url,'Earth','itempest')
    earth1 = stn.SimpleTenantNetworks(earth_mgr, jfile1, prefix_name='earth1')
    earth2 = stn.SimpleTenantNetworks(earth_mgr, jfile2, prefix_name='earth2')
    return earth_mgr, earth1, earth2


def wait4servers_in_status(wait4=600, pause_time=10, status='ACTIVE'):
    for now in utils.run_till_timeout(wait4, pause_time):
        ss = earth1.nova('s-servers')
        if len(ss) == 1 and status in ss.keys():
            return True
    return False


def build_networks(wait4server=600, pause_time=15):
    earth1.build()
    earth2.build()
    s_up_running = wait4servers_in_status(wait4server, pause_time)
    return s_up_running
    
# TODO(akang): create static routes between earth1-router and earth2-router
