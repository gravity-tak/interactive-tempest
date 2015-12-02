# Copyright 2015 OpenStack Foundation
# Copyright 2015 VMware Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import traceback

from itempest import icreds
from itempest.lib import utils
from itempest.tools import simple_tenant_networks as stn


# import load_our_solar_system as osn
# delete_tenants(osn.tenants)
def delete_tenants(tenant_pool):
    for tenant_name in tenant_pool:
        adm.keys('delete-tenant-by-name', tenant_name)


def get_mcli(tenant_name, **kwargs):
    psw = kwargs.pop('password', 'itempest8@OS')
    mcli_mgr = utils.get_mimic_manager_cli(os_auth_url, tenant_name, psw)
    return mcli_mgr


def get_stn(mcli_mgr, jfile, prefix):
    return stn.SimpleTenantNetworks(mcli_mgr.manager, jfile, prefix=prefix)


# sun-has-8-planets, earth-is-the-3rd and has-1-moon
os_auth_url = os.environ.get('OS_AUTH_URL', 'http://10.8.3.1:5000/v2.0')
os_password = os.environ.get('OS_PASSWORD', 'itempest8@OS')
tenant_max_instances = os.environ.get('OS_TENANT_MAX_INSTANCES', 20)

# accounts created by devstack
adm = utils.get_mimic_manager_cli(os_auth_url, 'admin', os_password)
try:
    # not every Openstack and devstack create demo project/tenant
    demo = utils.get_mimic_manager_cli(os_auth_url, 'demo', os_password)
except Exception:
    pass

# get-or-create Sun solaris system's admin Sun
try:
    tenant = utils.fgrep(adm.keys('tenant-list'), name=r'^Sun$')
    if len(tenant) < 1:
        Sun = icreds.create_admin_project('Sun', 'itempest8@OS')
    sun = utils.get_mimic_manager_cli(os_auth_url, 'Sun', 'itempest8@OS')
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
        tenant = icreds.create_primary_project(planet)
        tenant = adm.keys('tenant_get_by_name', planet)
        tenants[planet] = tenant
        # by default tenant can only have instances=10
        adm.nova('quota-update', tenant['id'], instances=tenant_max_instances)
        try:
            adm.qsvc('quota-incr-by', tenant['id'], 2)
        except Exception:
            pass
    else:
        tenants[planet] = tenant[0]
