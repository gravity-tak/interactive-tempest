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

# build network resources so we can run tempest tests
# 1. external network
# 2. images
"""
NSX Controller: 10.133.236.14-16
VXLAN-Pool: 192.168.1.14-16

VIO-2 Network
Mgmt Network (VM Network): 10.133.236.40-10.133.236.59
        Gateway: 10.133.239.253       DNS: 10.132.71.1, 10.132.71.2
Ext Network: 10.158.57.14-10.158.57.15
        Gateway: 10.158.57.253       DNS: 10.132.71.1, 10.132.71.2
Public VIP: 10.158.57.16
Public Network: 10.158.57.40-10.158.57.59
"""

from itempest.lib import cmd_neutron
from itempest.lib import cmd_nova
from itempest.lib import utils as U

class InitTempestEnv(object):
    def __init__(self, user_name, user_password,
                 tenant_name=None, **kwargs):
        self.mgr = icreds.get_client_manager(user_name, user_password,
                                             tenant_name=tenant_name,
                                             **kwargs)
        self.nova = U.command_wrapper(self.mgr, cmd_nova, True,
                                      log_cmd='OS-Nova')
        self.qsvc = U.command_wrapper(self.mgr, cmd_neutron,
                                      log_cmd='OS-Neutron')

    def create_external_network(self, name, network_cidr, ip_version=4,
                           **kwargs):
        net = qsvc('net-create', name,
             **{'router:external': True, 'shared':False})
        sname = name + "-subnet"
        snet = qsvc('subnet-create', net['id'], network_cidr,
                    ip_version=ip_version, name=sname,
                    **kwargs)
        net = qsvc('net-show', net['id'])
        snet = qsvc('subnet-show', snet['id'])
        return (net, snet)

    def create_image(self, name, location):
        pass