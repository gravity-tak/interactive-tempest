from oslo_log import log as logging
import six
import shlex
import subprocess

from tempest.common.utils.linux import remote_client as os_linux_client
from tempest import config
from tempest.lib import exceptions

CONF = config.CONF
LOG = logging.getLogger(__name__)


class RemoteClient(os_linux_client.RemoteClient):
    def exec_command(self, cmd, with_prologue=None):
        # Shell options below add more clearness on failures,
        # path is extended for some non-cirros guest oses (centos7)
        if isinstance(with_prologue, six.string_types):
            # Allow users bypassing default behavior programmatically.
            # If and only if with_prologue is instance of string.
            # Known issue is that the netcat program will fail
            # with prologue of value "set -o pipefail"
            cmd = with_prologue + " " + cmd
        else:
            cmd = CONF.validation.ssh_shell_prologue + " " + cmd
        LOG.debug("Remote command: %s" % cmd)
        return self.ssh_client.exec_command(cmd)


def copy_file_to_host(file_from, dest, host, username, pkey):
    dest = "%s@%s:%s" % (username, host, dest)
    cmd = "scp -v -o UserKnownHostsFile=/dev/null " \
          "-o StrictHostKeyChecking=no " \
          "-i %(pkey)s %(file1)s %(dest)s" % {'pkey': pkey,
                                              'file1': file_from,
                                              'dest': dest}
    args = shlex.split(cmd.encode('utf-8'))
    subprocess_args = {'stdout': subprocess.PIPE,
                       'stderr': subprocess.STDOUT}
    proc = subprocess.Popen(args, **subprocess_args)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise exceptions.CommandFailed(cmd,
                                       proc.returncode,
                                       stdout,
                                       stderr)
    return stdout
