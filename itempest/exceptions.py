
class TempestException(Exception):
    """Base Tempest Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = "An unknown exception occurred"

    def __init__(self, *args, **kwargs):
        super(TempestException, self).__init__()
        try:
            self._error_string = self.message % kwargs
        except Exception:
            # at least get the core message out if something happened
            self._error_string = self.message
        if len(args) > 0:
            # If there is a non-kwarg parameter, assume it's the error
            # message or reason description and tack it on to the end
            # of the exception message
            # Convert all arguments into their string representations...
            args = ["%s" % arg for arg in args]
            self._error_string = (self._error_string +
                                  "\nDetails: %s" % '\n'.join(args))

    def __str__(self):
        return self._error_string


class NotFound(ClientRestClientException):
    message = "Object not found"


class Unauthorized(ClientRestClientException):
    message = 'Unauthorized'


class Forbidden(ClientRestClientException):
    message = "Forbidden"


class TimeoutException(OtherRestClientException):
    message = "Request timed out"


class BadRequest(ClientRestClientException):
    message = "Bad request"

class SSHTimeout(TempestException):
    message = ("Connection to the %(host)s via SSH timed out.\n"
               "User: %(user)s, Password: %(password)s")


class SSHExecCommandFailed(TempestException):
    """Raised when remotely executed command returns nonzero status."""
    message = ("Command '%(command)s', exit status: %(exit_status)d, "
               "stderr:\n%(stderr)s\n"
               "stdout:\n%(stdout)s")
