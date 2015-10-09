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

import base64
import os

import itempest.lib.man_data as mdata
from oslo_log import log as oslog

from tempest_lib.common.utils import data_utils

from tempest.services.compute.json.flavors_client import FlavorsClient
from tempest.services.compute.json.images_client import ImagesClient
from tempest.services.compute.json.keypairs_client import KeyPairsClient
from tempest.services.compute.json.servers_client import ServersClient
from tempest.services.image.v1.json.image_client import ImageClient
from tempest.services.image.v2.json.image_client import ImageClientV2

LOG = oslog.getLogger(__name__)


def _g_flavors_client(mgr_or_client):
    if isinstance(mgr_or_client, FlavorsClient):
        return mgr_or_client
    return mgr_or_client.flavors_client


def _g_image_client(mgr_or_client):
    if isinstance(mgr_or_client, ImageClient):
        return mgr_or_client
    return mgr_or_client.image_client


def _g_image_v2_client(mgr_or_client):
    if isinstance(mgr_or_client, ImageClientV2):
        return mgr_or_client
    return mgr_or_client.image_client_v2


def _g_images_client(mgr_or_client):
    if isinstance(mgr_or_client, ImagesClient):
        return mgr_or_client
    return mgr_or_client.images_client


def _g_keypairs_client(mgr_or_client):
    if isinstance(mgr_or_client, KeyPairsClient):
        return mgr_or_client
    return mgr_or_client.keypairs_client


def _g_servers_client(mgr_or_client):
    if isinstance(mgr_or_client, ServersClient):
        return mgr_or_client
    return mgr_or_client.servers_client


def _g_kval(_dict, k):
    if k in _dict:
        return _dict[k]
    return None


def flavor_list(mgr_or_client, *args, **kwargs):
    flavor_client = _g_flavors_client(mgr_or_client)
    result = flavor_client.list_flavors(**kwargs)
    if 'flavors' in result:
        return result['flavors']
    return result


# image
# nova('image-create', 'cirros-0.3.3-x86_64', 'bare', 'vmdk',
#      location='http://10.34.57.161/images/cirros-0.3.3-x86_64-disk.vmdk')
def image_create(mgr_or_client, name, container_format, disk_format,
                 **kwargs):
    """Create a new image."""
    image_client = _g_image_v2_client(mgr_or_client)
    if 'is_public' in kwargs:
        is_public = kwargs.pop('is_public', True)
        kwargs['visibility'] = 'public' if is_public else 'private'
    file_path = kwargs.pop('file', None)
    img = image_client.create_image(name, container_format, disk_format,
                                    **kwargs)
    if file_path:
        image_file = open(file_path, 'rb')
        image_client.update_image(img['id'], data=image_file)
        img = image_show(mgr_or_client, img['id'])
    return img


def image_list(mgr_or_client, *args, **kwargs):
    image_client = _g_image_v2_client(mgr_or_client)
    result = image_client.list_images(*args, **kwargs)
    if 'images' in result:
        return result['images']
    return result


def image_delete(mgr_or_client, image_id, *args, **kwargs):
    image_client = _g_image_v2_client(mgr_or_client)
    return image_client.delete_image(image_id)


def image_meta(mgr_or_client, *args, **kwargs):
    raise (Exception("Not implemented yet!"))


def image_show(mgr_or_client, image_id, *args, **kwargs):
    image_client = _g_image_v2_client(mgr_or_client)
    # TODO(akang): what is the client and command?
    resp = image_client.show_image(image_id, *args, **kwargs)
    return resp


def keypair_list(mgr_or_client, *args, **kwargs):
    keypair_client = _g_keypairs_client(mgr_or_client)
    result = keypair_client.list_keypairs(**kwargs)
    if 'keypairs' in result:
        return result['keypairs']
    return result


def keypair_add(mgr_or_client, name, **kwargs):
    """nova keypair-add my-vm01-key"""
    name = name or data_utils.rand_name('itempest')
    keypair_client = _g_keypairs_client(mgr_or_client)
    pub_key = kwargs.pop('pub_key', None)
    try:
        keypair = keypair_client.create_keypair(name, pub_key=pub_key)
    except Exception:
        post_body = {'name': name}
        if pub_key:
            post_body['public_key'] = pub_key
        keypair = keypair_client.create_keypair(**post_body)
    keypair = keypair['keypair'] if 'keypair' in keypair else keypair
    return keypair


def keypair_create(mgr_or_client, name, **kwargs):
    return keypair_add(mgr_or_client, name, **kwargs)


def keypair_delete(mgr_or_client, key_name):
    keypair_client = _g_keypairs_client(mgr_or_client)
    keypair = keypair_client.delete_keypair(key_name)
    return keypair


def keypair_show(mgr_or_client, key_name, **kwargs):
    keypair_client = _g_keypairs_client(mgr_or_client)
    keypair = keypair_client.show_keypair(key_name)
    return keypair


# server
def server_action(mgr_or_client, server_id, action_name, response_key,
                  **kwargs):
    server_client = _g_servers_client(mgr_or_client)
    return server_client.action(server_id, action_name, response_key,
                                **kwargs)


def list_all_servers(mgr_or_client, **kwargs):
    # nova list --all-tenants << you need to be an admin acct
    return server_list(mgr_or_client, all_tenants=1, **kwargs)


# nova list
# keyword search in nova is always regexp, not exact like neutron
# WARN: list_servers not accept key-value list, but dict
def server_list(mgr_or_client, **kwargs):
    """NOTE: servers_client.list_servers() accepts only one DICT argument.

        CLI: nova list --all-tenants
        API: server_list(mgr, all_tenants=1)
    """
    server_client = _g_servers_client(mgr_or_client)
    server_id = kwargs.pop('server_id', kwargs.pop('id', None))
    network_id = kwargs.pop('network_id', None)
    if (server_id and type(server_id) is str):
        if (network_id and type(network_id) is str):
            return server_list_addresses_by_network(server_client,
                                                    server_id, network_id)
        else:
            return server_list_addresses(server_client, server_id)
    # kill me; I though servers accept dict, now it accepts **kwargs
    servers = server_client.list_servers(**kwargs)
    return servers['servers']


def server_list_with_detail(mgr_or_client, *args, **kwargs):
    server_client = _g_servers_client(mgr_or_client)
    kwargs['detail'] = True
    # servers = server_client.list_servers_with_detail(kwargs)
    servers = server_client.list_servers(**kwargs)
    return servers['servers']


def server_list_addresses(mgr_or_client, server_id, **kwargs):
    server_client = _g_servers_client(mgr_or_client)
    servers = server_client.list_address(server_id)
    return servers['servers']


def server_list_addresses_by_network(mgr_or_client, server_id, network_id,
                                     **kwargs):
    server_client = _g_servers_client(mgr_or_client)
    servers = server_client.list_address(server_id, network_id)
    return servers['servers']


def server_list_metadata(mgr_or_client, server_id, **kwargs):
    server_client = _g_servers_client(mgr_or_client)
    servers = server_client.list_metadata(server_id)
    return servers['servers']


def server_set_metadata(mgr_or_client, server_id, meta,
                        no_metadata_field=False, **kwargs):
    raise (Exception("Not implemented yet!"))


def boot(mgr_or_client, name, *args, **kwargs):
    return server_create(mgr_or_client, name, *args, **kwargs)


# nova boot
def server_create(mgr_or_client, name, **kwargs):
    """Please see create_server_on_interface() and c_server()"""
    server_client = _g_servers_client(mgr_or_client)
    image_id = kwargs.pop('image_id', kwargs.pop('image', None))
    flavor_id = kwargs.pop('flavor_id', kwargs.pop('flavor', 2))
    wait_on_boot = kwargs.pop('wait_on_boot', True)
    if 'user_data' in kwargs:
        # Use absolute path for user_data, if you do not encode it.
        if os.path.isfile(kwargs['user_data']):
            # not encoded with base64 yet
            data = open(kwargs['user_data'], 'r').read()
            kwargs['user_data'] = base64.standard_b64encode(data)
    try:
        # commit#f2d436e changed to only use **kwargs
        server = server_client.create_server(
            name=name, imageRef=image_id, flavorRef=flavor_id, **kwargs)
    except Exception:
        server = server_client.create_server(
            name, image_id, flavor_id, **kwargs)
    server = server['server'] if 'server' in server else server
    if wait_on_boot:
        server_client.wait_for_server_status(
            server_id=server['id'], status='ACTIVE')
    # The instance retrieved on creation is missing network
    # details, necessitating retrieval after it becomes active to
    # ensure correct details.
    server = server_show(mgr_or_client, server['id'])
    return server


def server_add_security_group(mgr_or_client, server_id, name):
    server_client = _g_servers_client(mgr_or_client)
    return server_client.add_security_group(server_id, name)


def server_remove_security_group(mgr_or_client, server_id, name):
    server_client = _g_servers_client(mgr_or_client)
    return server_client.remove_security_group(server_id, name)


# nova delete
def server_delete(mgr_or_client, server_id, *args, **kwargs):
    servers_client = _g_servers_client(mgr_or_client)
    server = servers_client.delete_server(server_id, **kwargs)
    return server


# nova show
def server_show(mgr_or_client, server_id, *args, **kwargs):
    servers_client = _g_servers_client(mgr_or_client)
    try:
        server = servers_client.get_server(server_id, **kwargs)
    except Exception:
        server = servers_client.show_server(server_id, **kwargs)
    if 'server' in server:
        return server['server']
    return server


# nova start
def server_start(mgr_or_client, server_id, *args, **kwargs):
    servers_client = _g_servers_client(mgr_or_client)
    server = servers_client.start(server_id, **kwargs)
    return server


# nova stop
def server_stop(mgr_or_client, server_id, *args, **kwargs):
    servers_client = _g_servers_client(mgr_or_client)
    server = servers_client.stop(server_id, **kwargs)
    return server


# nova rename
def server_rename(mgr_or_client, server_id, new_name):
    servers_client = _g_servers_client(mgr_or_client)
    server = servers_client.update_server(server_id, name=new_name)
    return server


# nova reboot
def server_reboot(mgr_or_client, server_id, reboot_type):
    servers_client = _g_servers_client(mgr_or_client)
    server = servers_client.reboot(server_id, reboot_type)
    return server


# nova rename, ...
# kwargs are name, meta, accessIPv4, accessIPv6, disk_config
def server_update(mgr_or_client, server_id, **kwargs):
    servers_client = _g_servers_client(mgr_or_client)
    server = servers_client.update_server(server_id, **kwargs)
    return server


def server_console_url(mgr_or_client, server_id,
                       console_type='novnc'):
    """NOTE:

        CLI: nova get-vnc-console <sever_id> novnc
        API: server_console_url(xadm, server_id)
    """
    servers_client = _g_servers_client(mgr_or_client)
    body = servers_client.get_vnc_console(server_id, console_type)
    return body['url']


def server_get_console_output(mgr_or_client, server_id, length=None):
    servers_client = _g_servers_client(mgr_or_client)
    body = servers_client.get_console_output(server_id, length)
    return body


def server_get_password(mgr_or_client, server_id):
    servers_client = _g_servers_client(mgr_or_client)
    body = servers_client.get_password(server_id)
    return body


# following commands are user-defined-commands
# user_data will be handled by server_created()
def create_server_on_interface(mgr_or_client, networks, image_id,
                               flavor=2, name=None, security_groups=None,
                               wait_on_boot=True, **kwargs):
    """Example:

        image_id = u'30aea0b3-ff23-4f9c-b7c8-cadeb91cc957' # cirros-0.3.3
        demo_net = vdemo('net-list', name='private')
        demo_svr = vdemo('c-server-on-interface', demo_net,
                         image_id=image_id, flavor=1,
                         name='demo-svr', wait_on_boot=False)
    """
    name = name or data_utils.rand_name('itempest-vm')
    # every user has a default security-group named default
    security_groups = security_groups or [{'name': 'default'}]
    if type(networks) is list:
        network_ifs = [{'uuid': nw['id']} for nw in networks]
    else:
        network_ifs = [{'uuid': networks['id']}]
    create_kwargs = {
        'networks': network_ifs,
        'security_groups': security_groups,
    }
    create_kwargs.update(kwargs)
    msg_p = "itempest creae-server-on-interface name=%s, image=%s"
    msg_p += ", flavor=%s, create_kwargs=%s"
    LOG.info(msg_p, name, image_id, flavor, str(create_kwargs))
    return server_create(mgr_or_client, name, image_id=image_id,
                         flavor=flavor, wait_on_boot=wait_on_boot,
                         **create_kwargs)


# nova('destroy-my-servers', name_startswith='page2-')
def destroy_my_servers(mgr_or_client, **kwargs):
    spattern = mdata.get_name_search_pattern(**kwargs)
    for s in server_list(mgr_or_client):
        # if spattern not provided, default is True
        if mdata.is_in_spattern(s['name'], spattern):
            server_delete(mgr_or_client, s['id'])


# admin priv required for ALL. or tenant's all servers
# nova('destroy-all-servers', name_startswith='page-')
def destroy_all_servers(mgr_or_client, **kwargs):
    spattern = mdata.get_name_search_pattern(**kwargs)
    for s in list_all_servers(mgr_or_client):
        if mdata.is_in_spattern(s['name'], spattern):
            server_delete(mgr_or_client, s['id'])


def status_server(mgr_or_client, *args, **kwargs):
    status = {}
    for s in server_list_with_detail(mgr_or_client, **kwargs):
        s_name = s['status']
        img = image_show(mgr_or_client, s['image']['id'])
        s_info = [s['id'], s['name'], img['name'],
                  _g_kval(s, 'security_groups')]
        if s_name in status:
            status[s_name].append(s_info)
        else:
            status[s_name] = [s_info]
    return status


# if qsvc has admin priv and want to see servers not created by admin
# qsvc('brief-server', all_tenants=1)
def brief_server(mgr_or_client, *args, **kwargs):
    status = {}
    kwargs['detail'] = True
    for server in server_list(mgr_or_client, **kwargs):
        s_name, s_info = info_server(mgr_or_client, server)
        status[s_name] = s_info
    return status


def info_server(mgr_or_client, server):
    if type(server) in (unicode, str):
        server = server_show(mgr_or_client, server)
    s_name = server['name']
    s_info = dict(id=server['id'],
                  status=server['status'],
                  security_groups=server['security_groups'])
    """
    addr_dict = {}
    for net_name, net_addr_info in server['addresses'].items():
        addr_dict[net_name] = dict()
        for adr in net_addr_info:
            # _type = adr['OS-EXT-IPS:type']
            _ver_type = "IPv%s-%s" % (adr['version'],
                                      adr['OS-EXT-IPS:type'])
            addr_dict[net_name][_ver_type] = adr['addr']
     """
    s_info['networks'] = mdata.get_server_address(server)
    img = image_show(mgr_or_client, server['image']['id'])
    s_info['image'] = img['name']
    return s_name, s_info


def get_server_fixed_ip_list(mgr_or_client, **kwargs):
    ip_list = []
    servers = brief_server(mgr_or_client)
    for s_name, s_info in servers.items():
        for if_name, if_info in s_info['networks'].items():
            if 'IPv4-fixed' in if_info:
                ip_list.append(if_info['IPv4-fixed'])
    return ip_list


def get_server_id_list(mgr_or_client, **kwargs):
    server_id_list = []
    servers = server_list(mgr_or_client)
    for server in servers:
        server_id_list.append(server['id'])
    return server_id_list
