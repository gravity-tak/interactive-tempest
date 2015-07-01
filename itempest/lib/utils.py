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

import re
import time

from oslo_log import log as oslog


NOVA_SERVER_CMDS = ['action', 'list', 'show', 'update', 'rename', 'delete',
                    'start', 'stop' 'pause', 'lock',
                    'meta', 'migrate', 'rescue',
                    'list-secgroup', 'live-migrate']
CMD_LOG_MSG = "OSCMD=%s args=%s kwargs=%s"

LOG = oslog.getLogger(__name__)


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
            arg_list.append(arg)
        ix += 1
    return (cmd, arg_list, kwargs)


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
                    log_cmd=None, verbose=None):
    """Usage Examples:

        from itempest import itempest_creds as icreds
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

    def os_command(cmd_line, *args, **kwargs):
        cmd, arg_list, kwargs = parse_cmdline(cmd_line, *args, **kwargs)
        if nova_flavor and cmd in NOVA_SERVER_CMDS:
            cmd = 'server_' + cmd
        for cmd_module in cmd_module_list:
            f_method = getattr(cmd_module, cmd, None)
            if f_method:
                break

        if f_method in [None]:
            raise Exception("Module in %s do not have command '%s'." %
                            (module_name_list, cmd))
        if verbose:
            print(CMD_LOG_MSG % (cmd, str(arg_list), str(kwargs)))
        if log_cmd:
            LOG.info(CMD_LOG_MSG, cmd, str(arg_list), str(kwargs))
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


# tempest_resp_l is passed by reference
def fgrep(tempest_resp_l, match_dict, keep_it=True):
    lx = len(tempest_resp_l) - 1
    while (lx >= 0):
        vd = tempest_resp_l[lx]
        matched = dict_is_matched(vd, match_dict)
        if matched:
            if not keep_it:
                tempest_resp_l.pop(lx)
        elif keep_it:
            tempest_resp_l.pop(lx)
        lx -= 1
    return tempest_resp_l


def dict_is_matched(odict, mdict):
    matched = 0
    for key, val in mdict.items():
        if key in odict and (
           (type(val) is str and odict[key] == val) or
           (type(val) in [list, tuple] and odict[key] in val)):
            matched += 1
    return matched == len(mdict)


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
