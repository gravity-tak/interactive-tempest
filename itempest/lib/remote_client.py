from oslo_log import log as logging
import six

from tempest.common.utils.linux import remote_client as os_linux_client
from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


class RemoteClient(os_linux_client.RemoteClient):
    def exec_command(self, cmd, with_prologue=None):
        # Shell options below add more clearness on failures,
        # path is extended for some non-cirros guest oses (centos7)
        if isinstance(with_prologue, six.string_types):
            # Allow users bypassing default behavior programmatically.
            # If and only if prologue is instance of string.
            # Known issue is that the netcat program will fail
            # with prologue of value "set -o pipefail"
            cmd = with_prologue + " " + cmd
        else:
            cmd = CONF.validation.ssh_shell_prologue + " " + cmd
        LOG.debug("Remote command: %s" % cmd)
        return self.ssh_client.exec_command(cmd)
