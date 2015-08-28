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
from itempest.lib import cmd_keystone
from itempest.lib import cmd_nova
from itempest.lib import cmd_neutron
from itempest.lib import cmd_neutron_u1


# import load_our_solar_system as osn
# delete_tenants(osn.tenants)
def delete_tenants(tenant_pool):
    for tenant_name in tenant_pool:
        keys('delete-tenant-by-name', tenant_name)


def get_user_commands(user_name, user_password, tenant_name=None):
    tenant_name = tenant_name if tenant_name else user_name
    user_mgr = icreds.get_client_manager(os_auth_url, user_name,
                                         user_password,
                                         tenant_name=tenant_name)
    qsvc = utils.command_wrapper(user_mgr,
                                 [cmd_neutron, cmd_neutron_u1],
                                 log_header="OS-Neutron")
    # nova list/show/.. will be prefixed with server_
    nova = utils.command_wrapper(user_mgr, cmd_nova, True,
                                 log_header="OS-Nova")
    keys = utils.command_wrapper(user_mgr, cmd_keystone,
                                 log_header="OS-Keystone")
    return (user_mgr, qsvc, nova, keys)


# sun-has-8-planets, earth-is-the-3rd and has-1-moon
os_auth_url = os.environ.get('OS_AUTH_URL', 'http://10.8.3.1:5000/v2.0')
os_password = os.environ.get('OS_PASSWORD', 'itempest8@OS')

# accounts created by devstack
(admin_mgr, qsvc, nova, keys) = get_user_commands('admin', os_password)
try:
    # not every Openstack and devstack create demo project/tenant
    (demo_mgr, d_qsvc, d_nova, d_keys) = get_user_commands(
        'demo', os_password)
except Exception:
    pass

# get-or-create Sun solaris system's admin Sun
try:
    tenant = utils.fgrep(keys('tenant-list'), name=r'^Sun$')
    if len(tenant) < 1:
        Sun = icreds.create_admin_project('Sun', 'itempest8@OS')
    (sun_mgr, s_qsvc, s_nova, s_keys) = get_user_commands('Sun',
                                                          'itempest8@OS')
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
    tenant = utils.fgrep(keys('tenant-list'), name=planet)
    if len(tenant) < 1:
        # tenant not exist, create it; default password=itempest
        tenant = icreds.create_primary_project(planet)
        tenants[planet] = keys('tenant_get_by_name', planet)
    else:
        tenants[planet] = tenant[0]
