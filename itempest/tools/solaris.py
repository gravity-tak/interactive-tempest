import os
import traceback

from itempest import icreds
from itempest.lib import utils


tenant_max_instances = os.environ.get('OS_TENANT_MAX_INSTANCES', 20)


def create_solaris(adm, os_auth_url, halt=False,
                   password="itempest8@OS"):
    if halt:
        import pdb;
        pdb.set_trace()

    # get-or-create Sun solaris system's admin Sun
    try:
        tenant = utils.fgrep(adm.keys('tenant-list'), name=r'^Sun$')
        if len(tenant) < 1:
            Sun = icreds.create_admin_project('Sun', password)
        sun = utils.get_mimic_manager_cli(os_auth_url, 'Sun', password)
    except Exception:
        tb_str = traceback.format_exc()
        mesg = ("ERROR creating/retriving Admin user[%s]:\n%s" % (
            'Sun', tb_str))
        utils.log_msg(mesg)

    # our solar system has 8 planets'
    sun_planets = ['Mercury', 'Venus', 'Earth', 'Mars',
                   'Jupiter', 'Satun', 'Uranus', 'Neptune']
    dwarf_planets = ["Haumea", "Eris", "Ceres", "Pluto", "Makemake"]
    tenants = {}
    for planet in sun_planets + dwarf_planets + ["Moon"]:
        tenant = utils.fgrep(adm.keys('tenant-list'), name=planet)
        if len(tenant) < 1:
            # tenant not exist, create it; default password=itempest
            tenant = icreds.create_primary_project(planet, password)
            try:
                tenant = adm.keys('tenant_get_by_name', planet)
                tenants[planet] = tenant
                # by default tenant can only have instances=10
                adm.nova('quota-update', tenant['id'],
                         instances=tenant_max_instances)
                adm.qsvc('quota-incr-by', tenant['id'], 2)
            except Exception:
                pass
        else:
            tenants[planet] = tenant[0]
    return tenants