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

from datetime import datetime
import os
import re
import subprocess
import sys
import time
import traceback

from oslo_log import log as oslog

import itempest.client_manager
from itempest.commands import cmd_glance, cmd_nova, cmd_keystone
from itempest.commands import cmd_neutron
from itempest.commands import cmd_neutron_u1
from itempest.commands import cmd_neutron_lbaas_v1r1 as cmd_neutron_lbaas_v1
from itempest.commands import cmd_neutron_lbaas_v2
from itempest.commands import cmd_neutron_qos
from itempest.services import load_balancer_v1_client
from itempest.services.lbaas import load_balancers_client
from itempest.services.lbaas import pools_client
from itempest.services.lbaas import listeners_client
from itempest.services.lbaas import members_client
from itempest.services.lbaas import health_monitors_client
from itempest.services.qos import base_qos


NOVA_SERVER_CMDS = ['action', 'list', 'show', 'update', 'rename', 'delete',
                    'start', 'stop' 'pause', 'lock',
                    'meta', 'migrate', 'rescue',
                    'list-secgroup', 'live-migrate']
CMD_LOG_MSG = "%s:%s %s args=%s kwargs=%s"
LOG_MESG = "%s:%s %s"
LOG_DEFAULT_FLAGS = int(os.environ.get('ITEMPEST_LOG_FLAGS', 0x01))

LOG = oslog.getLogger(__name__)


def log_cmd(log_header, cmd, s_arg, s_kwargs, flags):
    # the_time = time.strftime("%Y-%m-%d,%H:%M:%S")
    the_time = datetime.now().strftime("%Y-%m-%d,%H:%M:%S.%f")[:-3]
    if flags & 0x01:
        print(CMD_LOG_MSG % (log_header, the_time, cmd, s_arg, s_kwargs))
    if flags & 0x02:
        LOG.info(CMD_LOG_MSG, log_header, the_time, cmd, s_arg, s_kwargs)


def log_msg(mesg, log_header="OS-Message", flags=LOG_DEFAULT_FLAGS):
    the_time = datetime.now().strftime("%Y-%m-%d,%H:%M:%S.%f")[:-3]
    if flags & 0x01:
        print(LOG_MESG % (log_header, the_time, mesg))
    if flags & 0x02:
        LOG.info(LOG_MESG, log_header, the_time, mesg)


# For cmdline itself (not args and kwargs),
# option prefixed with -- is considered itself key-pair, and is always
# coded as --name=helo-holel, not --name helo-hotel.
# It does not support format of: --property hypervisor_type=qemu
# This command is wrong:
#    glance('image-update img-uuid --property architecture=arm')
def parse_cmdline(cmdline, *args, **kwargs):
    cmd_list = cmdline.split()
    cmd = re.sub("-", "_", cmd_list[0])
    arg_list = list(args)
    arg0_list = []
    ix = 1
    while (ix < len(cmd_list)):
        arg = cmd_list[ix]
        if arg.startswith("--"):
            ex = arg.find("=")
            if ex > 0:
                key = arg[2:ex]
                val = arg[(ex + 1):]
            else:
                ix += 1
                key = arg[2:]
                # default to True if not provided
                val = 'True'
            key = re.sub("-", "_", key)
            kwargs[key] = norm_it(val)
        else:
            arg0_list.append(arg)
        ix += 1
    return (cmd, (arg0_list + arg_list), kwargs)


def norm_it(val):
    lval = val.lower()
    if lval in ['false', 'f']:
        return False
    elif lval in ['true', 't']:
        return True
    elif lval.isdigit():
        return int(lval)
    return val


def command_wrapper(client_manager, cmd_module,
                    nova_flavor=False,
                    lbaasv1_flavor=False, lbaasv2_flavor=False,
                    qos_flavor=False,
                    log_header=None, verbose=True):
    """Usage Examples:

        from itempest import icreds
        from itempest.lib import cmd_neutron
        from itempest.lib import utils as U

        xadm = icreds.get_client_manager('http://10.34.57.116:5000/v2.0',
                                         'admin','openstack')
        # or xadm = icreds.get_os_manager(True)
        nadm = U.command_wrapper(xadm, cmd_neutron)
        nadm('net-list')
        nadm('net-create vx-lan')
        netwk = nadm('net-list --name=vx-lan)   # or
        netwk = nadm('net-list', name='vx-lan')
        nadm('net-delete', netwk[0]['id'])
        netwk = nadm('net-list', name='vx-lan')
    """
    cmd_module_list = (cmd_module if type(cmd_module) in (list, tuple)
                       else [cmd_module])
    module_name_list = [x.__name__ for x in cmd_module_list]
    log_flag = 1 if verbose else 0
    if type(log_header) in (str, unicode):
        log_flag |= 0x02
    else:
        log_header = "OS-Command"

    def os_command(cmd_line, *args, **kwargs):
        halt = kwargs.pop('debug', kwargs.pop('halt', False))
        cmd, arg_list, kwargs = parse_cmdline(cmd_line, *args, **kwargs)
        if nova_flavor and cmd in NOVA_SERVER_CMDS:
            cmd = 'server_' + cmd
        if lbaasv1_flavor and not cmd.startswith('lb_'):
            cmd = "lb_" + cmd
        if lbaasv2_flavor and cmd.startswith('lbaas_'):
            cmd = cmd[6:]
        if qos_flavor and cmd.startswith('qos_'):
            cmd = cmd[4:]
        for cmd_module in cmd_module_list:
            f_method = getattr(cmd_module, cmd, None)
            if f_method:
                break

        if f_method in [None]:
            raise Exception("Module in %s do not have command '%s'." %
                            (module_name_list, cmd))
        log_cmd(log_header, cmd, str(arg_list), str(kwargs), log_flag)
        _trace_me() if halt else None
        return f_method(client_manager, *arg_list, **kwargs)

    return os_command


# add nova_flavor in command_wrapper, or use nova_wrapper instead
def nova_wrapper(client_manager, cmd_module):
    def nova_command(cmd_line, *args, **kwargs):
        cmd, arg_list, kwargs = parse_cmdline(cmd_line, *args, **kwargs)
        if cmd in NOVA_SERVER_CMDS:
            cmd = 'server_' + cmd
        try:
            f_method = getattr(cmd_module, cmd)
        except Exception:
            raise Exception("Module '%s' does not have command '%s'." %
                            (cmd_module.__name__, cmd))
        return f_method(client_manager, *arg_list, **kwargs)

    return nova_command


# Examples:
#   fgrep(qsvc('router-list'), router_type='exclu', distributed=True)
#   fgrep(qsvc('ext-list', alias='security')
def fgrep(tempest_resp_list, **kwargs):
    halt = kwargs.pop('halt', False)
    _trace_me() if halt else None
    if not isinstance(tempest_resp_list, list):
        return tempest_resp_list
    return field_grep(tempest_resp_list, kwargs, True)


# tempest_resp_l is passed by reference
def field_grep(tempest_resp_list, grep_dict, rm_ifnot_match=True):
    lx = len(tempest_resp_list) - 1
    while (lx >= 0):
        vd = tempest_resp_list[lx]
        matched = dict_is_matched(vd, grep_dict)
        if matched:
            if not rm_ifnot_match:
                tempest_resp_list.pop(lx)
        elif rm_ifnot_match:
            tempest_resp_list.pop(lx)
        lx -= 1
    return tempest_resp_list


def dict_is_matched(odict, mdict):
    matched = 0
    for key, val in mdict.items():
        if key in odict and grep_this(odict[key], val):
            matched += 1
    return matched == len(mdict)


def grep_this(target_val, wanted_val):
    if type(wanted_val) is str and re.search(wanted_val, target_val):
        return True
    if type(wanted_val) in [list, tuple]:
        for val in wanted_val:
            if type(val) is str and re.search(val, target_val):
                return True
    elif wanted_val == target_val:
        # don't know, just compare it, for example shared=True
        return True
    return False


def xfer_mdict_key(match_dict):
    mlist = []
    for key, val in match_dict.items():
        if re.search(r"[-_]match", key):
            mlist.append([key[0:-6], val, 1])
        else:
            mlist.append([key, val, 0])
    return mlist


def run_till_timeout(seconds_to_try, interval=5.0):
    now, end_time = time.time(), time.time() + seconds_to_try
    while now < end_time:
        yield now
        time.sleep(interval)
        now = time.time()


def ipaddr_is_reachable(ip_addr, duration=30, sleep_for=1,
                        show_progress=True):
    for t in run_till_timeout(duration, sleep_for):
        if ping_ipaddr(ip_addr, show_progress=show_progress):
            return True
    return False


def ping_ipaddr(ip_addr, show_progress=True):
    cmd_line = ["ping", "-c3", ip_addr]
    if show_progress:
        log_msg('exec subprocess: %s' % cmd_line)
    proc = subprocess.Popen(cmd_line,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    data_stdout, data_stderr = proc.communicate()
    # if ip_addr is pinable, the return code is 0
    addr_reachable = (proc.returncode == 0)
    if not addr_reachable:
        mesg = ("ip_addr[%s] is not reachable:\nstdout=%s\nstderr=%s"
                % (ip_addr, data_stdout, data_stderr))
        log_msg(mesg)
    return addr_reachable


# port_list = qsvc('port-list')
# port_by_network = listdict_as_dict(port_list, 'network_id')
# server_list = nova('server-list')
# server_by_name = listdict_as_dict(server_list, 'name')
def listdict_as_dict(list_dict, col):
    dicts = {}
    for d in list_dict:
        if col not in d:
            continue
        dkey = d[col]
        # bwaware dkey==u'' for example network:dhcp
        if dkey in dicts:
            dicts[dkey].append(d)
        else:
            dicts[dkey] = [d]
    return dicts


def get_last_trace():
    return traceback.extract_tb(sys.last_traceback)


def print_trace(tracemsg=None):
    tracemsg = tracemsg or get_last_trace()
    for msg in tracemsg:
        print("line#%s @file: %s\n  %s\n    %s" %
              (msg[1], msg[0], msg[2], msg[3]))


def _trace_me():
    import pdb
    pdb.set_trace()


class AttrContainer(object):
    def __init__(self, **kwargs):
        for k, v in (kwargs.items()):
            setattr(self, k, v)

    def __eq__(self, other):
        return str(self) == str(other)


# iadm = utils.get_mimic_manager_cli('http://10.33.75.103:5000/v2.0', 'admin', 'openstack')
def get_mimic_manager_cli(os_auth_url, os_username, os_password,
                          os_tenant_name=None, identity_version='v2',
                          **kwargs):
    lbaasv1 = kwargs.pop('lbaasv1', True)
    lbaasv2 = kwargs.pop('lbaasv2', True)
    manager = itempest.client_manager.get_client_manager(
        os_auth_url, os_username, os_password, tenant_name=os_tenant_name,
        identity_version=identity_version, **kwargs)
    return get_mimic_manager_cli_with_client_manager(manager,
                                                     lbaasv1=lbaasv1,
                                                     lbaasv2=lbaasv2)


def get_mimic_manager_cli_with_client_manager(manager, lbaasv1=True,
                                              lbaasv2=False):
    qsvc = get_qsvc_command(manager)
    nova = get_nova_command(manager)
    keys = get_keys_command(manager)
    lbv1 = get_lbv1_command(manager)
    lbaas = get_lbaas_commands(manager)
    qos = get_neutron_qos_commands(manager)
    mcli = AttrContainer(manager=manager,
                         qsvc=qsvc,
                         nova=nova,
                         keys=keys,
                         lbv1=lbv1,
                         lbaas=lbaas,
                         qos=qos)
    try:
        # Are there other ways to validate the user's admin previledge?
        mcli.roles = manager.roles_client.list_roles()['roles']
        mcli.is_admin = True
    except Exception:
        mcli.roles = None
        mcli.is_admin = None
    return mcli


def get_glance_command(client_mgr, log_header="OS-Glance", **kwargs):
    return command_wrapper(client_mgr, cmd_glance,
                           log_header=log_header)


def get_qsvc_command(client_mgr, log_header="OS-Neutron", **kwargs):
    return command_wrapper(client_mgr,
                           [cmd_neutron, cmd_neutron_u1],
                           log_header=log_header)


def get_nova_command(client_mgr, log_header="OS-Nova", **kwargs):
    return command_wrapper(client_mgr, cmd_nova, nova_flavor=True,
                           log_header=log_header)


def get_keys_command(client_mgr, log_header="OS-Keystone", **kwargs):
    return command_wrapper(client_mgr, cmd_keystone,
                           log_header=log_header)


def get_lbv1_command(client_mgr, log_header="OS-LBaasV1", **kwargs):
    setattr(client_mgr, 'lbs_client',
            load_balancer_v1_client.get_client(client_mgr))
    return command_wrapper(client_mgr, cmd_neutron_lbaas_v1,
                           lbaasv1_flavor=True, log_header=log_header)


def _get_lbv1_command(client_mgr, log_header="OS-LBaasV1", **kwargs):
    if cmd_neutron_lbaas_v1:
        return command_wrapper(client_mgr, cmd_neutron_lbaas_v1,
                               log_header=log_header)
    else:
        return None


def get_lbaas_commands(client_mgr, log_header='OS-LBaasV2', **kwargs):
    setattr(client_mgr, 'load_balancers_client',
            load_balancers_client.get_client(client_mgr))
    setattr(client_mgr, 'pools_client',
            pools_client.get_client(client_mgr))
    setattr(client_mgr, 'listeners_client',
            listeners_client.get_client(client_mgr))
    setattr(client_mgr, 'members_client',
            members_client.get_client(client_mgr))
    setattr(client_mgr, 'health_monitors_client',
            health_monitors_client.get_client(client_mgr))
    return command_wrapper(client_mgr, cmd_neutron_lbaas_v2,
                           lbaasv2_flavor=True, log_header=log_header)


def get_neutron_qos_commands(client_mgr, log_header="OS-Neutron-QoS",
                             **kwargs):
    setattr(client_mgr, 'qos_client',
            base_qos.BaseQosClient(client_mgr))
    return command_wrapper(client_mgr, cmd_neutron_qos,
                           qos_flavor=True, log_header=log_header)