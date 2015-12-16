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

from tempest_lib import exceptions as lib_exc


def _g_identity_client(mgr_or_client):
    return getattr(mgr_or_client, 'identity_client', mgr_or_client)


def _g_identity_v3_client(mgr_or_client):
    return getattr(mgr_or_client, 'identity_v3_client', mgr_or_client)


def _g_endpoint_client(mgr_or_client):
    return getattr(mgr_or_client, 'endpoints_client', mgr_or_client)


def _g_service_client(mgr_or_client):
    return getattr(mgr_or_client, 'service_client', mgr_or_client)


def _g_tenant_client(mgr_or_client):
    return getattr(mgr_or_client, 'tenants_client', mgr_or_client)


def _g_token_v3_client(mgr_or_client):
    return getattr(mgr_or_client, 'token_v3_client', mgr_or_client)


def _g_token_client(mgr_or_client):
    return getattr(mgr_or_client, 'token_client', mgr_or_client)


def _return_result(result, of_attr):
    if of_attr in result:
        return result[of_attr]
    return result


# endpoint
def endpoint_list(mgr_or_client, *args, **kwargs):
    _client = _g_endpoint_client(mgr_or_client)
    result = _client.list_endpoints(**kwargs)
    return _return_result(result, 'endpoints')


def endpoint_get(mgr_or_client, *args, **kwargs):
    _client = _g_endpoint_client(mgr_or_client)
    result = _client.list_endpoints(*args, **kwargs)
    return _return_result(result, 'endpoint')


# kw: region, force_enabled, enabled
def endpoint_create(mgr_or_client, service_id, interface, url, **kwargs):
    _client = _g_endpoint_client(mgr_or_client)
    result = _client.create_endpoints(service_id, interface, url,
                                              **kwargs)
    return _return_result(result, 'endpoint')


def endpoint_delete(mgr_or_client, *args, **kwargs):
    _client = _g_endpoint_client(mgr_or_client)
    return _client.list_endpoints(**kwargs)


# available kw: service_id, interface, url, region, enabled
def endpoint_update(mgr_or_client, endpoint_id, **kwargs):
    _client = _g_endpoint_client(mgr_or_client)
    return _client.update_endpoint(endpoint_id, **kwargs)


def ext_list(mgr_or_client, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    result = _client.list_extensions()
    return _return_result(result, 'extensions')


def role_list(mgr_or_client, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    result = _client.list_roles(**kwargs)
    return _return_result(result, 'roles')


def role_delete(mgr_or_client, role_id, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    return _client.delete_role(role_id)


def role_get(mgr_or_client, role_id, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    try:
        result = _client.get_role(role_id)
    except Exception:
        result = _client.show_role(role_id)
    return _return_result(result, 'role')


def service_list(mgr_or_client, *args, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    result = service_client.list_services(**kwargs)
    return _return_result(result, 'services')


def service_get(mgr_or_client, service_id, *args, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    result = service_client.create_service(service_id, *args, **kwargs)
    return _return_result(result, 'service')


# service_create('ec2', 'ec2', description='EC2 Compatibility Layer')
def service_create(mgr_or_client, serv_type, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    result = service_client.create_service(serv_type, **kwargs)
    return _return_result(result, 'service')


def service_delete(mgr_or_client, service_id, *args, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.delete_service(service_id, **kwargs)


def service_update(mgr_or_client, service_id, **kwargs):
    service_client = _g_service_client(mgr_or_client)
    return service_client.update_service(service_id, **kwargs)


# tenant
def tenant_list(mgr_or_client, *args, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    result = _client.list_tenants()
    return _return_result(result, 'tenants')


def tenant_get(mgr_or_client, tenant_id, *args, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    try:
        result = _client.get_tenant(tenant_id)
    except Exception:
        result = _client.show_tenant(tenant_id)
    return _return_result(result, 'tenant')


def tenant_get_by_name(mgr_or_client, tenant_name, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    try:
        return _client.get_tenant_by_name(tenant_name)
    except Exception:
        # command removed
        tenants = _client.list_tenants()['tenants']
        for tenant in tenants:
            if tenant['name'] == tenant_name:
                return tenant
    raise lib_exc.NotFound('No such tenant')


def tenant_create(mgr_or_client, name, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    result = _client.create_tenant(name, **kwargs)
    return _return_result(result, 'tenant')


def tenant_delete(mgr_or_client, tenant_id, *args, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    return _client.delete_tenant(tenant_id, **kwargs)


def tenant_update(mgr_or_client, tenant_id, *args, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    return _client.update_tenant(tenant_id, **kwargs)


def token_get(mgr_or_client, token_id, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    try:
        return _client.get_token(token_id, **kwargs)
    except Exception:
        return _client.show_token(token_id)


def user_list(mgr_or_client, *args, **kwargs):
    tenant_id = kwargs.pop('tenant_id', None)
    if tenant_id:
        return user_list_of_tenant(mgr_or_client, tenant_id)
    _client = _g_identity_client(mgr_or_client)
    try:
        result = _client.get_users()
    except:
        result = _client.list_users()
    return _return_result(result, 'users')


def user_list_of_tenant(mgr_or_client, tenant_id, *args, **kwargs):
    _client = _g_tenant_client(mgr_or_client)
    try:
        result = _client.list_users_for_tenant(tenant_id)
    except Exception:
        result = _client.list_tenant_users(tenant_id)
    return _return_result(result, 'users')


def user_show(mgr_or_client, user_id, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    result = _client.show_user(user_id)
    return _return_result(result, 'user')


def user_get(mgr_or_client, user_id, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    try:
        result = _client.get_user(user_id)
    except Exception:
        result = user_show(mgr_or_client, user_id)
    return _return_result(result, 'user')


def user_get_by_name(mgr_or_client, tenant_id, user_name, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    try:
        return _client.get_user_by_username(tenant_id, user_name)
    except:
        # command revmoed
        users = user_list_of_tenant(mgr_or_client, tenant_id)
        for user in users:
            if user['name'] == user_name:
                return user
    return lib_exc.NotFound('No such user')


def user_create(mgr_or_client, name, password, tenant_id, email,
                *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    result = _client.create_user(name, password, tenant_id, email,
                                         **kwargs)
    return _return_result(result, 'user')


def user_delete(mgr_or_client, user_id, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    return _client.delete_user(user_id)


def user_update(mgr_or_client, user_id, *args, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    return _client.update_user(user_id, **kwargs)


def user_role_list(mgr_or_client, tenant_id, user_id, **kwargs):
    _client = _g_identity_client(mgr_or_client)
    result = _client.list_user_roles(tenant_id, user_id, **kwargs)
    return _return_result(result, 'roles')


def user_role_add(mgr_or_client, tenant_id, user_id, role_id):
    _client = _g_identity_client(mgr_or_client)
    return _client.assign_user_role(tenant_id, user_id, role_id)


def user_role_remove(mgr_or_client, tenant_id, user_id, role_id):
    _client = _g_identity_client(mgr_or_client)
    return _client.delete_user_role(tenant_id, user_id, role_id)


# project - identity v3
def project_list(mgr_or_client, *args, **kwargs):
    _client = _g_identity_v3_client(mgr_or_client)
    result = _client.list_projects()
    return _return_result(result, 'projects')


def project_get(mgr_or_client, project_id, *args, **kwargs):
    _client = _g_identity_v3_client(mgr_or_client)
    result = _client.get_project(project_id)
    return _return_result(result, 'project')


def project_create(mgr_or_client, name, **kwargs):
    _client = _g_identity_v3_client(mgr_or_client)
    return _client.create_project(name, **kwargs)


def project_delete(mgr_or_client, project_id, **kwargs):
    _client = _g_identity_v3_client(mgr_or_client)
    return _client.delete_project(project_id, **kwargs)


# user defined commands
def delete_tenant_users(mgr_or_client, tenant_id, *args, **kwargs):
    tenant = tenant_get(mgr_or_client, tenant_id)
    u_list = user_list_of_tenant(mgr_or_client, tenant['id'])
    for u in u_list:
        user_delete(mgr_or_client, u['id'])
    return tenant_delete(mgr_or_client, tenant['id'])


def delete_tenant_by_name(mgr_or_client, tenant_name, *args, **kwargs):
    tenant = tenant_get_by_name(mgr_or_client, tenant_name)
    u_list = user_list_of_tenant(mgr_or_client, tenant['id'])
    for u in u_list:
        user_delete(mgr_or_client, u['id'])
    tenant_delete(mgr_or_client, tenant['id'])
    try:
        tenant_get_by_name(mgr_or_client, tenant_name)
        return False
    except Exception:
        return True
