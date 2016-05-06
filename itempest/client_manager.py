from tempest.lib import auth as l_auth
from tempest import clients

__author__ = 'akang'


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
    halt = kwargs.pop('halt', False)
    cm_conf = dict(
        username=username,
        password=password,
        identity_version=identity_version,
        fill_in=fill_in,
        tenant_name=(tenant_name if tenant_name else username),
        disable_ssl_certificate_validation=True)
    cmgr = None
    cm_conf.update(kwargs)
    if halt:
        import pdb;
        pdb.set_trace()
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
