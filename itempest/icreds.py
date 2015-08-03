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

from oslo_log import log as logging

from tempest import clients
from tempest.common import cred_provider
from tempest.common import isolated_creds
from tempest import config

from tempest_lib import auth as l_auth
from tempest_lib.common.utils import data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


# this class requires correct [compute-admin] and [identity] in tempest.conf
class ItempestCreds(isolated_creds.IsolatedCreds):
    """ItempestIsoLatedCreds overwirtes IsolatedCreds so that its credentail
    type of admin, primary and alt will create project/user name from provided
    param with_name and suffixed with -A for admin, -P for primary and -T for
    alt.  If with_name is not provided at calling get_xxx_creds() then name
    will be used.
    """

    def __init__(self, name, identity_version=None,
                 password='itempest', num_of_users=1,
                 network_resources=None, cleanup_atexit=False):
        # super create self.cred_client
        self.password = password
        super(ItempestCreds, self).__init__(identity_version,
                                            name,
                                            network_resources)
        self.num_of_users = num_of_users
        self.cleanup_atexit = cleanup_atexit

    def __del__(self):
        if self.cleanup_atexit:
            self.clear_isolated_creds()

    def _create_creds(self, with_name, suffix="", admin=False, roles=None):
        """Create credentials with specific name:
        project_name = with_name + suffix
        username = with_name
        """
        project_name = with_name + suffix
        project_desc = project_name + "-desc " + self.password
        project = self.creds_client.create_project(
            name=project_name, description=project_desc)

        user_list = self._create_project_users(project, self.num_of_users,
                                               is_admin=admin, roles=roles)
        creds = self.creds_client.get_credentials(user_list[0], project,
                                                  self.password)
        return cred_provider.TestResources(creds)

    def _create_project_users(self, project,
                              num_of_users=1, is_admin=False, roles=None):
        user_list = [self._create_user(project,
                                       roles=roles, admin=is_admin)]
        for uid in range(1, num_of_users, 1):
            user_list.append(self._create_user(project, roles, uid,
                                               admin=is_admin))
        return user_list

    def _create_user(self, project, roles=None, uid=0, admin=False,
                     group_name=None):
        username = (project['name'] +
                    (("-%s" % group_name) if group_name else ""))
        username = (username + (("-%s" % uid) if uid > 0 else ""))
        email = username + "@itempest.net"
        user = self.creds_client.create_user(
            username, self.password, project, email)
        if admin:
            self.creds_client.assign_user_role(user, project,
                                               CONF.identity.admin_role)
        # Add roles specified in config file
        for conf_role in CONF.auth.tempest_roles:
            self.creds_client.assign_user_role(user, project, conf_role)
        # Add roles requested by caller
        if roles:
            for role in roles:
                self.creds_client.assign_user_role(user, project, role)
        return user

    def get_credentials(self, credential_type,
                        with_name=None, create_network=False):
        # default we don't create network, unless specified
        if self.isolated_creds.get(str(credential_type)):
            credentials = self.isolated_creds[str(credential_type)]
        else:
            if credential_type in ['primary', 'alt', 'admin']:
                is_admin = (credential_type == 'admin')
                credentials = self._create_creds(with_name,
                                                 admin=is_admin)
            else:
                credentials = self._create_creds(with_name,
                                                 roles=credential_type)
            self.isolated_creds[str(credential_type)] = credentials
            # Maintained until tests are ported
            LOG.info("Acquired isolated creds:\n credentials: %s"
                     % credentials)
            if create_network:
                # tempest_lib will change CONF attributes into input
                # parameters per conversation with Andrea Frittoli
                # at 2015-05 summit
                network, subnet, router = self._create_network_resources(
                    credentials.tenant_id)
                credentials.set_resources(network=network,
                                          subnet=subnet,
                                          router=router)
                LOG.info("Created isolated network resources for : \n"
                         + " credentials: %s" % credentials)
        return credentials

    def get_primary_creds(self, with_name=None, create_network=False):
        with_name = with_name or self.name + "-P"
        return self.get_credentials('primary', with_name=with_name)

    def get_alt_creds(self, with_name=None, create_network=False):
        with_name = with_name or self.name + "-T"
        return self.get_credentials('alt', with_name=with_name)

    def get_admin_creds(self, with_name=None, create_network=False):
        with_name = with_name or self.name + "-A"
        return self.get_credentials('admin', with_name=with_name)

    def get_creds_by_roles(self, roles, force_new=False, with_name=None):
        """Check parent class for changes"""
        roles = list(set(roles))
        exist_creds = self.isolated_creds.get(str(roles))
        if exist_creds and force_new:
            new_index = str(roles) + '-' + str(len(self.isolated_creds))
            self.isolated_creds[new_index] = exist_creds
            del self.isolated_creds[str(roles)]
        with_name = with_name or data_utils.rand_name(self.name)
        return self.get_credentials(roles, with_name=with_name)


# devstack create two users: admin and demo
# assume both have same password
#   admin_mgr = get_client_manager(OS_AUTH_URL, OS_USERNAME, OS_PASSWORD)
#   demo_mgr = get_client_manager(OS_AUTH_URL, OS_USERNAME, OS_PASSWORD)
# network_client from get_client_manager() using:
#    tempest/services/network/network_client_base.py
# this cause some commands not available. See diff from:
#    tempest/services/network/json/network_client.py
# This method with default values don't require correct user/password in
# tempest.conf, however the API in uri must be correct!
def get_client_manager(os_auth_url, username, password,
                       tenant_name=None,
                       fill_in=False, identity_version='v2',
                       **kwargs):
    cm_conf = dict(
        username=username,
        password=password,
        fill_in=fill_in,
        tenant_name=(tenant_name if tenant_name else username),
        disable_ssl_certificate_validation=True)
    cmgr = None
    cm_conf.update(kwargs)
    l_creds = l_auth.get_credentials(os_auth_url, **cm_conf)
    cmgr = clients.Manager(l_creds)
    return cmgr


# Following functions require tempest.conf with correct admin
# information.
# adm_mgr = get_os_manager(True)
# demo_mgr = get_os_manager()
def get_os_manager(is_admin=False):
    if is_admin:
        mgr = clients.AdminManager()
    else:
        mgr = clients.Manager()
    return mgr


def create_test_projects(name, password='itemepst8@OS', **kwargs):
    creds = ItempestCreds(name, password=password)
    creds_a = creds.get_admin_creds()
    creds_p = creds.get_primary_creds()
    creds_t = creds.get_alt_creds()
    return (creds_a, creds_p, creds_t)


def create_primary_project(name, password='itempest8@OS',
                           num_of_users=1,
                           **kwargs):
    creds = ItempestCreds(name, password=password,
                          num_of_users=num_of_users, **kwargs)
    p = creds.get_primary_creds(name)
    return p


def create_admin_project(name, password='itempest8@OS', **kwargs):
    creds = ItempestCreds(name, password=password, **kwargs)
    p = creds.get_admin_creds(name)
    return p


# adm_mgr = get_os_manager(True)
# users = create_project_users(adm_mgr, 'Earth', 3)
def create_project_users(adm_mgr, project_name, num_of_users,
                         group_name=None):
    p = adm_mgr.identity_client.get_tenant_by_name(project_name)

    proj_cred = ItempestCreds(project_name)
    user_list = []
    for uid in range(1, num_of_users):
        user_list.append(proj_cred._create_user(p, uid=uid,
                                                group_name=group_name))
    return user_list
