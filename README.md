# interactive-tempest
itempest, Tempest addon-on to explore OpenStack resources interactively

You need the tempest repository which is the SDK for itempest.
Refer to docs/Tempest-Installation-Guide.txt to install Tempest without devstack at Ubuntu or Mac OS.X.

# Attention
Current implemenation required you to source rc files.
The sample rc files are at itempest/rc directory.

Before you enter python interpreter, you should enter your rc file.

_local and .rc will be ignored by git so you can put your local files there.

# Example of sourcing tempest rc file:
source _local/rc/sunrc
tools/with_env.sh ipython

# Using itempest
Technical speaking, itempest get a tenant's tempest clients manager which are used to access various OpenStack services.
To mimic Openstack clients syntax, function command_wrapper is used to wrap clients manager.
Example of using this package is given as following:

from itempest import load_our_solar_system as osn

page_mgr = osn.icreds.get_client_manager(osn.auth_url, 'Page', 'itempest')

npage = osn.utils.command_wrapper(page_mgr, [osn.cmd_nova], True)

npage('image-list')

qpage = osn.utils.command_wrapper(page_mgr, [osn.cmd_neutron])

qpage('net-list')

from itempest.tools import simple_tenant_networks as stn

page1 = stn.SimpleTenantNetworks(page_mgr, 'itempest/data/topo-ubuntu-01.json', prefix_name='page1')

page2 = stn.SimpleTenantNetworks(page_mgr, 'itempest/data/topo-ubuntu-02.json', prefix_name='page2')

page1.build()

page1.qsvc('net-list')

page1.qsvc('net-list --name=public')

page1.nova('router-list')

page1.nova('server-list')

page1.nova('server-list', detail=True)

page1.nova('server-list', detail=True, name='page1-worker-bee')

# user define commands
page1.nova('status-server')

page1.nova('brief-vserver')

page2.build()

# Programing Note:
Modules are used to code services command, for example, cmd_nova.py for Nova, cmd_neutron.py for Neutron and are at itempest/lib directory. However command modules can be put any places as long as python can access it as part of a package.

The command modules provided to command_wrapper is a list which mean you can create your own command module and be procesed by each service you want to use.

# TODO list
1. User defined commands can be in a different module. command_wrapper() can accept multiple command modules.
2. modify itempest_creds.py to only use auth.py at tempest_lib
3. remove tempest_auth.py from lib
