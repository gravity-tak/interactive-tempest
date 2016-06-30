import os
import sys
from itempest import load_our_solar_system as osn


def get_my_commands():
    try:
        cmd_kwargs = {}
        start_idx = sys.argv.index('--')
        for xarg in sys.argv[start_idx + 1:]:
            sp_idx = xarg.find('=')
            if sp_idx < 0:
                cmd_kwargs[xarg] = True
            else:
                k = xarg[:sp_idx]
                v = xarg[sp_idx + 1:]
                cmd_kwargs[k] = v
        return cmd_kwargs
    except:
        return {}


target = get_my_commands()
if 'halt' in target:
    import pdb;

    pdb.set_trace()

if 'project' in target:
    project_name = target.get('project')
    password = target.get('password', osn.os_password)
    project_cmgr = osn.get_mcli(project_name, password=password)
    from itempest.tools import build_lbaas_v2 as lbaasv2

    for mtype in ('HTTP', 'TCP', 'PING'):
        lb_name = "%s-lb2-%s" % (project_name.lower(), mtype)
        lbaasv2.build_os_lbaas(project_cmgr, lb_name,
                               monitor_type=mtype)
else:
    raise Exception(
        "project is required to launch create its lbaas environment.")
