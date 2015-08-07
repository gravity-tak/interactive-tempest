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

import netaddr
import os

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions

from tempest.services.network.json.network_client import NetworkClient

import man_data as mdata


NET_CONSTANTS = {
    'dns_list': ['8.8.8.8', '8.8.4,4'],
    'host_routes': [{
        'destination': os.environ.get('HOST_ROUTES_DEST', '10.20.0.0/32'),
        'nexthop': os.environ.get('HOST_ROUTES_NEXTHOP', '10.100.1.1')}],
    }


def _g_net_client(mgr_or_client):
    if isinstance(mgr_or_client, NetworkClient):
        return mgr_or_client
    return mgr_or_client.network_client


def ext_list(mgr_or_client,
             *args, **kwargs):
    """CLI list all extensions:

        neutron ext-list
    """
    net_client = _g_net_client(mgr_or_client)
    result = net_client.list_extensions()
    return result['extensions']

# network
def network_create(mgr_or_client, name=None, tenant_id=None, **kwargs):
    return net_create(mgr_or_client,
                      name=name, tenant_id=tenant_id,
                      **kwargs)


def net_create(mgr_or_client, name=None, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    name = name or data_utils.rand_name('itempest-network')
    result = net_client.create_network(name=name, **kwargs)
    return result['network']


def network_list(mgr_or_client, *args, **kwargs):
    return net_list(mgr_or_client, *args, **kwargs)


# net_list(xadm, name='public')
def net_list(mgr_or_client, *args, **kwargs):
    """CLI Examples:

        neutron net-list
        neutron net-list --tenant-id e926a5b12756476da297fea7d930fb05
    """
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_networks(*args, **kwargs)
    return body['networks']


def net_external_list(mgr_or_client, *args, **kwargs):
    """CLI Examples:

        neutron net-external-list
        neutron net-list --router:exgternal True
    """
    kwargs['router:external'] = True
    return net_list(mgr_or_client, *args, **kwargs)


def network_list_on_dhcp_agent(mgr_or_client, *args, **kwargs):
    return net_list_on_dhcp_agent(mgr_or_client, *args, **kwargs)


# what is this?
def net_list_on_dhcp_agent(mgr_or_client, *args, **kwargs):
    """List the networks on a DHCP agent."""
    return net_list(mgr_or_client, *args, **kwargs)


def network_delete(mgr_or_client, network_id, *args, **kwargs):
    return net_delete(mgr_or_client, network_id, *args, **kwargs)


def net_delete(mgr_or_client, network_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_network(
        network_id, *args, **kwargs)
    return body


def network_show(mgr_or_client, network_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    return net_show(net_client, network_id, *args, **kwargs)


def net_show(mgr_or_client, network_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_network(network_id, *args, **kwargs)
    return body['network']


def network_update(mgr_or_client, network_id, *args, **kwargs):
    return net_update(mgr_or_client, network_id, *args, **kwargs)


def net_update(mgr_or_client, network_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    return net_client.update_network(network_id, *args, **kwargs)


# subnet
def subnet_create(mgr_or_client, network_id, cidr,
                  **kwargs):
    net_client = _g_net_client(mgr_or_client)
    name = kwargs.pop('name', None) or data_utils.rand_name('itempest-subnet')
    ip_version = kwargs.pop('ip_version', None) or 4
    subnet = dict(
        name=name,
        ip_version=ip_version,
        network_id=network_id,
        cidr=cidr,
        **kwargs
    )
    result = net_client.create_subnet(**subnet)
    return result['subnet']


def subnet_create_safe(mgr_or_client, network_id,
                       **kwargs):
    net_client = _g_net_client(mgr_or_client)
    # tenant_id = kwargs.pop('tenant_id', None) or _g_tenant_id(net_client)
    tenant_id = kwargs.pop('tenant_id', None)
    name = kwargs.pop('name', None) or data_utils.rand_name('itempest-subnet')
    tenant_network_mask_bits = kwargs.pop('mask_bits', None) or 26
    tenant_network_cidr = kwargs.pop('cidr', None) or '192.168.123.0/24'
    pfix = tenant_network_cidr.find("/")
    if pfix > 0:
        _mask_bits = int(tenant_network_cidr[(pfix + 1):])
        if tenant_network_cidr and tenant_network_cidr < _mask_bits:
            pass
        else:
            tenant_network_mask_bits = _mask_bits
    else:
        tenant_network_cidr += ("/%s" % tenant_network_mask_bits)
    ip_version = kwargs.pop('ip_version', None) or 4

    def cidr_in_use(cidr, tenant_id):
        """
        :return True if subnet with cidr already exist in tenant
            False else
        """
        cidr_in_use = subnet_list(net_client, tenant_id=tenant_id, cidr=cidr)
        return len(cidr_in_use) != 0

    tenant_cidr = netaddr.IPNetwork(tenant_network_cidr)
    result = None
    # Repeatedly attempt subnet creation with sequential cidr
    # blocks until an unallocated block is found.
    for subnet_cidr in tenant_cidr.subnet(tenant_network_mask_bits):
        str_cidr = str(subnet_cidr)
        if cidr_in_use(str_cidr, tenant_id=tenant_id):
            continue

        subnet = dict(
            name=name,
            ip_version=ip_version,
            network_id=network_id,
            # tenant_id=tenant_id,
            cidr=str_cidr,
            **kwargs
        )
        try:
            if tenant_id:
                # BUG?, non admin cannot provide tenant_id even it is it's ID
                # subnet.pop('tenant_id')
                subnet['tenant_id'] = tenant_id
            result = net_client.create_subnet(**subnet)
            break
        except exceptions.Conflict as e:
            is_overlapping_cidr = 'overlaps with another subnet' in str(e)
            if not is_overlapping_cidr:
                raise
    return result['subnet']


def subnet_list(mgr_or_client, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_subnets(*args, **kwargs)
    return body['subnets']


def subnet_show(mgr_or_client, subnet_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_subnet(subnet_id, **kwargs)
    return body['subnet']


def subnet_delete(mgr_or_client, subnet_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_subnet(subnet_id, **kwargs)
    return body


def subnet_update(mgr_or_client, subnet_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_subnet(subnet_id, **kwargs)
    return body['subnet']


# floatingip - support ip4 only
def floatingip_create(mgr_or_client, public_network_id,
                      **kwargs):
    net_client = _g_net_client(mgr_or_client)
    result = net_client.create_floatingip(
        floating_network_id=public_network_id,
        **kwargs)
    return result['floatingip']


def floatingip_associate(mgr_or_client, floatingip_id, server_id,
                         **kwargs):
    net_client = _g_net_client(mgr_or_client)
    result = net_client.associate_floating_ip_to_server(
        floatingip_id, server_id)
    return result


def floatingip_disassociate(mgr_or_client, floatingip_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    result = net_client.update_floatingip(
        floatingip_id, port_id=None)
    return result


def floatingip_list(mgr_or_client, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_floatingips(*args, **kwargs)
    return body['floatingips']


def floatingip_show(mgr_or_client, floatingip_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_floatingip(floatingip_id,
                                      *args, **kwargs)
    return body['floatingip']


def floatingip_delete(mgr_or_client, floatingip_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_floatingip(floatingip_id,
                                        *args, **kwargs)
    return body


def floatingip_update(mgr_or_client, floatingip_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    return net_client.update_floatingip(floatingip_id, **kwargs)


# port
def port_create(mgr_or_client, network_id,
                name=None, tenant_id=None, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    name = name or data_utils.rand_name('itempest-port')
    tenant_id = tenant_id or _g_tenant_id(net_client)
    result = net_client.create_port(
        name=name, network_id=network_id, tenant_id=tenant_id)
    return result['port']


def port_list(mgr_or_client, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_ports(*args, **kwargs)
    return body['ports']


def port_show(mgr_or_client, port_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_port(port_id, *args, **kwargs)
    return body['port']


def port_delete(mgr_or_client, port_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_port(port_id, *args, **kwargs)
    return body


def port_update(mgr_or_client, port_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_port(port_id, *args, **kwargs)
    return body['port']


# security-group
def security_group_create(mgr_or_client,
                          name=None, tenant_id=None, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    name = name or data_utils.rand_name('itempest-sg')
    tenant_id = tenant_id or _g_tenant_id(net_client)
    desc = (kwargs.pop('desc', None) or
            kwargs.pop('description', None) or
            (name + " description"))
    sg_dict = dict(name=name, description=desc, tenant_id=tenant_id)
    result = net_client.create_security_group(**sg_dict)
    return result['security_group']


def security_group_list(mgr_or_client, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_security_groups(*args, **kwargs)
    return body['security_groups']


def security_group_show(mgr_or_client, security_group_id,
                        *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_security_group(security_group_id,
                                          *args, **kwargs)
    return body['security_group']


def security_group_delete(mgr_or_client, security_group_id,
                          *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_security_group(security_group_id,
                                            *args, **kwargs)
    return body


def security_group_update(mgr_or_client, security_group_id,
                          *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_security_group(security_group_id,
                                            *args, **kwargs)
    return body['security_group']


# security-group-rule
def security_group_rule_create(mgr_or_client, security_group_id,
                               tenant_id=None, skip_None=True, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    tenant_id = tenant_id or _g_tenant_id(net_client)
    rule_dict = dict(security_group_id=security_group_id,
                     tenant_id=tenant_id)
    for k, v in kwargs.items():
        if skip_None and v is None:
            continue
        rule_dict[k] = v
    return net_client.create_security_group_rule(**rule_dict)


# router
def router_create(mgr_or_client, name, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.create_router(name, *args, **kwargs)
    return body['router']


def router_list(mgr_or_client, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_routers(*args, **kwargs)
    return body['routers']


def router_list_on_l3_agent(mgr_or_client, *args, **kwargs):
    """List the routers on a L3 agent."""
    raise("Not implemented yet!")


def router_show(mgr_or_client, router_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_router(router_id, *args, **kwargs)
    return body['router']


def router_delete(mgr_or_client, router_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_router(router_id, *args, **kwargs)
    return body


def router_update(mgr_or_client, router_id, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_router(router_id, **kwargs)
    return body['router']


# extra routes (static routes) only available from router_update
def router_update_extra_routes_future(mgr_or_client, router_id,
                                      nexthop, destination):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_extra_routes(router_id,
                                          nexthop, destination)
    return body['router']

# NOT AVAILABLE NOW!
# fixed by https://bugs.launchpad.net/tempest/+bug/1468600
def router_update_extra_routes(mgr_or_client, router_id, routes):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_extra_routes(router_id,
                                          routes)
    return body['router']


def router_delete_extra_routes(mgr_or_client, router_id):
    net_client = _g_net_client(mgr_or_client)
    return net_client.delete_extra_routes(router_id)


# user-defined-command
def router_add_extra_route(mgr_or_client, router_id,
                           nexthop, destination):
    net_client = _g_net_client(mgr_or_client)
    extra_route = dict(nexthop=nexthop, destination=destination)
    # TODO(akang): retrieve from router_id, and update with extra_route
    body = net_client.update_extra_routes(router_id,
                                          nexthop, destination)
    return body['router']


# router sub-commands
def router_gateway_clear(mgr_or_client, router_id, *args, **kwargs):
    """Remove an external network gateway from a router."""
    net_client = _g_net_client(mgr_or_client)
    return net_client.update_router(router_id,
                                    external_gateway_info=dict())


# depending on your OS neutron policy, you might need to use admin-priv
# user to set enable_snat=(True|False)
def router_gateway_set(mgr_or_client, router_id, external_network_id,
                       **kwargs):
    """Set the external network gateway for a router."""
    net_client = _g_net_client(mgr_or_client)
    external_gateway_info = dict(network_id=external_network_id)
    en_snat = 'enable_snat'
    if en_snat in kwargs:
        external_gateway_info[en_snat] = kwargs.pop(en_snat)
    return net_client.update_router(
        router_id,
        external_gateway_info=external_gateway_info)


# user defined command
# this command might need admin priv for mgr_or_client
def router_gateway_snat_set(mgr_or_client, router, enable):
    net_client = _g_net_client(mgr_or_client)
    external_gateway_info = router['external_gateway_info']
    external_gateway_info['enable_snat'] = enable
    return net_client.update_router(
        router['id'],
        external_gateway_info=external_gateway_info)


# user-defined-command
def router_gateway_port_show(mgr_or_client, router_id):
    ports = router_port_list(mgr_or_client, router_id)
    for port in ports:
        if port['device_owner'] == u'network:router_gateway':
            return port
    return None


# user-defined-command
def router_gateway_ipaddr_get(mgr_or_client, router_id):
    port = router_gateway_port_show(mgr_or_client, router_id)
    for fips in port['fixed_ips']:
        if 'ip_address' in fips:
            return fips['ip_address']
    return None


def router_interface_add(mgr_or_client, router_id, subnet_id,
                         *args, **kwargs):
    """Add an internal network interface to a router."""
    net_client = _g_net_client(mgr_or_client)
    try:
        return net_client.add_router_interface_with_subnbet_id(
            router_id,
            subnet_id=subnet_id)
    except Exception:
        return netclient_do(net_client,
                            'add_router_interface_with_subnet_id',
                            router_id,
                            subnet_id=subnet_id)


def router_interface_delete(mgr_or_client, router_id, subnet_id,
                            *args, **kwargs):
    """Remove an internal network interface from a router."""
    net_client = _g_net_client(mgr_or_client)
    try:
        return net_client.remove_router_interface_with_subnbet_id(
            router_id,
            subnet_id=subnet_id)
    except Exception:
        return netclient_do(net_client,
                            'remove_router_interface_with_subnet_id',
                            router_id,
                            subnet_id=subnet_id)


# CLI : neutron router-port-list <router-name-or-id>
def router_interface_list(mgr_or_client, router_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    try:
        result = net_client.list_router_interfaces(router_id)
    except Exception:
        result = netclient_do(net_client,
                              'list_router_interfaces',
                              router_id)
    return result['ports']


def router_port_list(mgr_or_client, router_id, *args, **kwargs):
    """List ports that belong to a given tenant, with specified router."""
    return router_interface_list(mgr_or_client, router_id, **kwargs)


# quota
def quota_list(mgr_or_client, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.list_quotas(**kwargs)
    return body['quotas']


def quota_show(mgr_or_client, tenant_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.show_quota(tenant_id, **kwargs)
    return body['quota']


def quota_update(mgr_or_client, tenant_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.update_quota(tenant_id, **kwargs)
    return body['quota']


def quota_delete(mgr_or_client, tenant_id, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    body = net_client.delete_quota(tenant_id, **kwargs)
    return body


# user defined command
def quota_incr_by(mgr_or_client, tenant_id, multi_by=2, **kwargs):
    qta = quota_show(mgr_or_client, tenant_id)
    for k in qta.keys():
        qta[k] *= multi_by
    return quota_update(mgr_or_client, tenant_id, **qta)


########################################################################
# TEMPORARY solution, keep here until I know why and fix it:
# Methods in class NetworkClientJSON were not being called. However its
# parent calss NetworkClientBase's method __getattr__ is used to
# determine which method should be called.
def netclient_do(mgr_or_client, method_name, *args, **kwargs):
    net_client = _g_net_client(mgr_or_client)
    nc_method = getattr(net_client, method_name, None)
    if nc_method is None:
        raise Exception("Method[%s] is not defined at instance[%s]" %
                        method_name, str(net_client))
    results = nc_method(*args, **kwargs)
    return results


def _g_tenant_id(os_client):
    try:
        return os_client.tenant_id
    except Exception:
        # should not come over here.
        return os_client.rest_client.tenant_id
