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

from tempest.services.identity.v2.json.identity_client \
    import IdentityClient
from tempest.services.identity.v3.json.endpoints_client \
    import EndPointClient
from tempest.services.identity.v3.json.identity_client \
    import IdentityV3Client
from tempest.services.identity.v3.json.service_client \
    import ServiceClient

from tempest_lib.services.identity.v2.token_client import TokenClient
from tempest_lib.services.identity.v3.token_client import V3TokenClient


def _g_identity_client(mgr_or_client):
    if isinstance(mgr_or_client, IdentityClient):
        return mgr_or_client
    return mgr_or_client.identity_client


def _g_identity_v3_client(mgr_or_client):
    if isinstance(mgr_or_client, IdentityV3Client):
        return mgr_or_client
    return mgr_or_client.identity_v3_client


def _g_endpoint_client(mgr_or_client):
    if isinstance(mgr_or_client, EndPointClient):
        return mgr_or_client
    return mgr_or_client.endpoints_client


def _g_service_client(mgr_or_client):
    if isinstance(mgr_or_client, ServiceClient):
        return mgr_or_client
    return mgr_or_client.service_client


def _g_token_v3_client(mgr_or_client):
    if isinstance(mgr_or_client, V3TokenClient):
        return mgr_or_client
    return mgr_or_client.token_v3_client


def _g_token_client(mgr_or_client):
    if isinstance(mgr_or_client, TokenClient):
        return mgr_or_client
    return mgr_or_client.token_client


# endpoint
def endpoint_list(mgr_or_client, *args, **kwargs):
    endpoint_client = _g_endpoint_client(mgr_or_client)
    return endpoint_client.list_endpoints(**kwargs)


def endpoint_get(mgr_or_client, *args, **kwargs):
    endpoint_client = _g_endpoint_client(mgr_or_client)
    return endpoint_client.list_endpoints(*args, **kwargs)


# kw: region, force_enabled, enabled
def endpoint_create(mgr_or_client, service_id, interface, url, **kwargs):
    endpoint_client = _g_endpoint_client(mgr_or_client)
    return endpoint_client.create_endpoints(service_id, interface, url,
                                            **kwargs)


def endpoint_delete(mgr_or_client, *args, **kwargs):
    endpoint_client = _g_endpoint_client(mgr_or_client)
    return endpoint_client.list_endpoints(**kwargs)


# available kw: service_id, interface, url, region, enabled
def endpoint_update(mgr_or_client, endpoint_id, **kwargs):
    endpoint_client = _g_endpoint_client(mgr_or_client)
    return endpoint_client.update_endpoint(endpoint_id, **kwargs)


def ext_list(mgr_or_client, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.list_extensions()


def role_list(mgr_or_client, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.list_roles(**kwargs)


def role_delete(mgr_or_client, role_id, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.delete_role(role_id)


def role_get(mgr_or_client, role_id, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.get_role(role_id)


def service_list(mgr_or_client, *args, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.list_services(**kwargs)


def service_get(mgr_or_client, service_id, *args, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.create_service(service_id, *args, **kwargs)


# service_create('ec2', 'ec2', description='EC2 Compatibility Layer')
def service_create(mgr_or_client, serv_type, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.create_service(serv_type, **kwargs)


def service_delete(mgr_or_client, service_id, *args, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.delete_service(service_id, **kwargs)


def service_update(mgr_or_client, service_id, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.update_service(service_id, **kwargs)


# tenant
def tenant_list(mgr_or_client, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.list_tenants()


def tenant_get(mgr_or_client, tenant_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.get_tenant(tenant_id)


def tenant_get_by_name(mgr_or_client, tenant_name, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.get_tenant_by_name(tenant_name)


def tenant_create(mgr_or_client, name, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.create_tenant(name, **kwargs)


def tenant_delete(mgr_or_client, tenant_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.delete_tenant(tenant_id, **kwargs)


def tenant_update(mgr_or_client, tenant_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.update_tenant(tenant_id, **kwargs)


def token_get(mgr_or_client, token_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.get_token(token_id, **kwargs)


def user_list(mgr_or_client, *args, **kwargs):
    tenant_id = kwargs.pop('tenant_id', None)
    if tenant_id:
        return user_list_of_tenant(mgr_or_client, tenant_id)
    identity_client = _g_identity_client(mgr_or_client)
    result = identity_client.get_users()
    return result


def user_list_of_tenant(mgr_or_client, tenant_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    result = identity_client.list_users_for_tenant(tenant_id)
    return result


def user_get(mgr_or_client, user_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.get_user(user_id)


def user_get_by_name(mgr_or_client, tenant_id, user_name, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.get_user_by_username(tenant_id, user_name)


def user_create(mgr_or_client, name, password, tenant_id, email,
                *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.create_user(name, password, tenant_id, email,
                                       **kwargs)


def user_delete(mgr_or_client, user_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.delete_user(user_id)


def user_update(mgr_or_client, user_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.update_user(user_id, **kwargs)


def user_role_list(mgr_or_client, tenant_id, user_id, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.list_user_roles(tenant_id, user_id, **kwargs)


def user_role_add(mgr_or_client, tenant_id, user_id, role_id):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.assign_user_role(tenant_id, user_id, role_id)


def user_role_remove(mgr_or_client, tenant_id, user_id, role_id):
    identity_client = _g_identity_client(mgr_or_client)
    return identity_client.delete_user_role(tenant_id, user_id, role_id)


# project
def project_list(mgr_or_client, *args, **kwargs):
    identity_client = _g_identity_v3_client(mgr_or_client)
    return identity_client.list_projects()


def project_get(mgr_or_client, project_id, *args, **kwargs):
    identity_client = _g_identity_v3_client(mgr_or_client)
    return identity_client.get_project(project_id)


# extra
def delete_tenant_users(mgr_or_client, tenant_id, *args, **kwargs):
    identity_client = _g_identity_client(mgr_or_client)
    u_list = identity_client.list_users_for_tenant(tenant_id)
    for u in u_list:
        identity_client.delete_user(u['id'])
    return identity_client.delete_tenant(tenant_id)
