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

import ConfigParser
import os

import init_vio_env as vio_env
from itempest.lib import utils

DEFAULT_IMAGE_NAME = os.environ.get('OS_IMAGE_NAME',
                                    'cirros-0.3.3-x86_64-disk')
DEFAULT_IMAGE_FILE = os.environ.get(
    'OS_IMAGE_FILE', '~/images/cirros-0.3.3-x86_64-disk.vmdk')
DEFAULT_PUBLIC_NETWORK_NAME = os.environ.get(
    'OS_PUBLIC_NETWORK_NAME', 'public')
os_auth_url = os.environ.get('OS_AUTH_URL', None)
os_username = os.environ.get('OS_USERNAME', 'demo')
os_password = os.environ.get('OS_PASSWORD', 'itempest8@OS')
os_tenant_name = os.environ.get('OS_TENANT_NAME', os_username)


# env_id is the var defining howto create subnet
# it is defined at vio_env module. Example:
# update_conf_by_id('VIO1')
def update_conf_by_id(env_id, cli_mgr=None, **kwargs):
    net_conf = getattr(vio_env, env_id)
    cli_mgr = cli_mgr if cli_mgr else get_mimic_manager_cli()
    return update_tempest_conf(cli_mgr, net_conf, **kwargs)


def update_vio1_tempest_conf(cli_mgr, tempest_conf=None,
                             net_conf=None, img_name=None, **kwargs):
    public_net_dict = net_conf if net_conf else vio_env.VIO1
    update_tempest_conf(cli_mgr, public_net_dict,
                        tempest_conf=tempest_conf, img_name=img_name,
                        **kwargs)


def update_vio2_tempest_conf(cli_mgr, tempest_conf=None,
                             net_conf=None, img_name=None, **kwargs):
    public_net_dict = net_conf if net_conf else vio_env.VIO2
    update_tempest_conf(cli_mgr, public_net_dict,
                        tempest_conf=tempest_conf, img_name=img_name,
                        **kwargs)


def update_vio3_tempest_conf(cli_mgr, tempest_conf=None,
                             net_conf=None, img_name=None, **kwargs):
    public_net_dict = net_conf if net_conf else vio_env.VIO3
    update_tempest_conf(cli_mgr, public_net_dict,
                        tempest_conf=tempest_conf, img_name=img_name,
                        **kwargs)


def find_tempest_conf():
    if 'TEMPEST_CONFIG_DIR' in os.environ:
        cdir = os.environ['TEMPEST_CONFIG_DIR']
    elif 'TEMPEST_ROOT_DIR' in os.environ:
        cdir = os.environ['TEMPEST_ROOT_DIR'] + "/etc"
    else:
        cdir = 'etc'
    if 'TEMPEST_CONFIG' in os.environ:
        cfile = os.environ['TEMPEST_CONFIG']
    else:
        cfile = 'tempest.conf'
    conf_file = os.path.join(cdir, cfile)
    return conf_file


def get_tempest_conf(cli_mgr, tempest_conf=None):
    tempest_conf = (tempest_conf if tempest_conf else
                    find_tempest_conf())
    if os.path.isfile(tempest_conf):
        return tempest_conf
    return None


def show_or_create_vmdk_image(cli_mgr, img_name=None, img_file=None):
    img_name = img_name if img_name else DEFAULT_IMAGE_NAME
    img_file = img_file if img_file else DEFAULT_IMAGE_FILE
    try:
        img = utils.fgrep(cli_mgr.nova('image-list'), name=img_name)[0]
    except Exception:
        property = dict(vmware_disktype='sparse',
                        vmware_adaptertype='ide')
        img = cli_mgr.nova('image-create', img_name, file=img_file,
                           container_format='bare', disk_format='vmdk',
                           is_public=True, property=property)
    return cli_mgr.nova('image-show', img['id'])


def update_tempest_conf(cli_mgr, public_net_dict, tempest_conf=None,
                        img_name=None, **kwargs):
    public_network_name = kwargs.pop('public_network_name',
                                     DEFAULT_PUBLIC_NETWORK_NAME)
    img_name = kwargs.pop('image_name', DEFAULT_IMAGE_NAME)
    img_file = kwargs.pop('image_file', DEFAULT_IMAGE_FILE)
    tempest_conf = get_tempest_conf(cli_mgr, tempest_conf)
    cp = ConfigParser.ConfigParser()
    cp.readfp(open(tempest_conf))
    # update compute.image_ref
    img = show_or_create_vmdk_image(cli_mgr,
                                    img_name=img_name, img_file=img_file)
    cp.set('compute', 'image_ref', img['id'])
    cp.set('compute', 'image_ref_alt', img['id'])
    # update network.public_network_id
    net = get_net_conf(cli_mgr, public_net_dict,
                       public_network_name)
    cp.set('network', 'public_network_id', net['id'])
    # save tempest.conf file
    sv_conf_name = "." + os.path.basename(tempest_conf) + ".sav"
    sv_tempest_conf = os.path.join(os.path.dirname(tempest_conf),
                                   sv_conf_name)
    os.rename(tempest_conf, sv_tempest_conf)
    # write conf to tempest_conf
    with open(tempest_conf, 'wb') as configfile:
        cp.write(configfile)
    return tempest_conf


def get_net_conf(cli_mgr, public_net_conf, xnet_name='public',
                 use_internal_dns=False):
    dns_nameservers = (public_net_conf['nameservers_internal']
                       if use_internal_dns else public_net_conf[
        'nameservers'])

    net, subnet = vio_env.show_or_create_external_network(
        cli_mgr, xnet_name,
        cidr=public_net_conf['cidr'],
        gateway_ip=public_net_conf['gateway'],
        dns_nameservers=dns_nameservers,
        allocation_pools=public_net_conf['alloc_pools'])

    net = cli_mgr.qsvc('net-list', name=xnet_name)[0]
    return net


def get_mimic_manager_cli(auth_url=None, username=None,
                          password=None, tenant_name=None):
    auth_url = auth_url if auth_url else os_auth_url
    username = username if username else os_username
    password = password if password else os_password
    tenant_name = tenant_name if tenant_name else username
    cli_mgr = utils.get_mimic_manager_cli(os_auth_url, os_username,
                                          os_password,
                                          os_tenant_name)
    return cli_mgr
