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
#    distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See
#  the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from itempest.lib import utils

os_auth_url = os.environ.get('OS_AUTH_URL', 'http://10.8.3.1:5000/v2.0')
os_username = os.environ.get('OS_USERNAME', 'Earth')
os_password = os.environ.get('OS_PASSWORD', 'itempest8@OS')
os_tenant_name = os.environ.get('OS_TENANT_NAME', os_username)

tenant = utils.get_mimic_manager_cli(os_auth_url, os_username, os_password,
                                     os_tenant_name)
