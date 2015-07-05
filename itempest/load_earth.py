# Copyright 2015 OpenStack Foundation
# Copyright 2015 VMware.
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

from itempest import itempest_creds as icreds
from itempest.lib import utils
from itempest.lib import cmd_keystone
from itempest.lib import cmd_nova
from itempest.lib import cmd_neutron


auth_url = os.environ.get('OS_AUTH_URL', 'http://10.8.3.1:5000/v2.0')
os_password = os.environ.get('OS_PASSWORD', 'openstack')

# accounts created by devstack
# admin_mgr = icreds.get_client_manager(auth_url, 'admin', os_password)
demo_mgr = icreds.get_client_manager(auth_url, 'demo', os_password)

qdemo = utils.command_wrapper(demo_mgr, cmd_neutron)
# nova list/show/.. will be prefixed with server_
ndemo = utils.command_wrapper(demo_mgr, cmd_nova, True)
kdemo = utils.command_wrapper(demo_mgr, cmd_keystone)

tenant_name = 'Earth'
tenant_password = 'itempest'
earth_mgr = icreds.get_client_manager(auth_url, tenant_name,
                                      password=tenant_password)
