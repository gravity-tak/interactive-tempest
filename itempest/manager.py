
from tempest import exceptions
from tempest.lib import auth

class Manager(object):
    """tempest/manager.py depending on config to fectch uri.

    This class provides it method of identify the auth_provider
    """

    def __init__(self, credentials, os_auth_url,
                 disable_ssl_certificate_validation=True,
                 ca_certs=None, trace_requests=None,
                 pre_auth=True):
        self.credentials = credentials
        # Check if passed or default credentials are valid
        if not self.credentials.is_valid():
            raise exceptions.InvalidCredentials()

        dscv = disable_ssl_certificate_validation
        # Creates an auth provider for the credentials
        self.auth_provider = get_auth_provider(
            self.credentials, os_auth_url,
            disable_ssl_certificate_validation=dscv,
            ca_certs=ca_certs, trace_requests=trace_requests,
            pre_auth=pre_auth)
        self.auth_version = "v2" if os_auth_url.find("/v2") > 0 else "v3"


def get_auth_provider_class(credentials, os_auth_url):
    if isinstance(credentials, auth.KeystoneV3Credentials):
        return auth.KeystoneV3AuthProvider, os_auth_url
    else:
        return auth.KeystoneV2AuthProvider, os_auth_url


def get_auth_provider(credentials, os_auth_url,
                      disable_ssl_certificate_validation=True,
                      ca_certs=None, trace_requests=None,
                      pre_auth=True, **kwargs):
    default_params = {
        'disable_ssl_certificate_validation': disable_ssl_certificate_validation,
        'ca_certs': ca_certs,
        'trace_requests': trace_requests
    }
    if credentials is None:
        raise exceptions.InvalidCredentials(
            'Credentials must be specified')
    auth_provider_class, auth_url = get_auth_provider_class(
        credentials, os_auth_url)
    _auth_provider = auth_provider_class(credentials, os_auth_url,
                                         **default_params)
    if pre_auth:
        _auth_provider.set_auth()
    return _auth_provider
