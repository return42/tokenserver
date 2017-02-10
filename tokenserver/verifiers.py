import json
import warnings
import socket

from pyramid.threadlocal import get_current_registry
from zope.interface import implementer, Interface

import requests

from browserid.verifiers.local import LocalVerifier as LocalVerifier_
from browserid.errors import (InvalidSignatureError, ExpiredSignatureError,
                              AudienceMismatchError,InvalidIssuerError)
from browserid.errors import ConnectionError # pylint: disable=W0622
from browserid.supportdoc import SupportDocumentManager

import six

def get_verifier(registry=None):
    """returns the registered verifier, building it if necessary."""
    if registry is None:
        registry = get_current_registry()
    return registry.getUtility(IBrowserIdVerifier)


# This is to simplify the registering of the implementations using pyramid
# registry.
class IBrowserIdVerifier(Interface): # pylint: disable=E0239
    pass


# The default verifier from browserid
@implementer(IBrowserIdVerifier)
class LocalVerifier(LocalVerifier_):

    def __init__(self, **kwargs):
        """LocalVerifier constructor, with the following extra config options:

        :param ssl_certificate: The path to an optional ssl certificate to
            use when doing SSL requests with the BrowserID server.
            Set to True (the default) to use default certificate authorities.
            Set to False to disable SSL verification.
        """
        if "ssl_certificate" in kwargs:
            verify = kwargs["ssl_certificate"]
            kwargs.pop("ssl_certificate")
            if not verify:
                self._emit_warning()
        else:
            verify = None
        kwargs['supportdocs'] = SupportDocumentManager(verify=verify)
        super(LocalVerifier, self).__init__(**kwargs)

    def _emit_warning(self):
        """Emit a scary warning to discourage unverified SSL access."""
        msg = "browserid.ssl_certificate=False disables server's certificate"\
              "validation and poses a security risk. You should pass the path"\
              "to your self-signed certificate(s) instead. "\
              "For more information on the ssl_certificate parameter, see "\
              "http://docs.python-requests.org/en/latest/user/advanced/"\
              "#ssl-cert-verification"
        warnings.warn(msg, RuntimeWarning, stacklevel=2)


# A verifier that posts to a remote verifier service.
# The RemoteVerifier implementation from PyBrowserID does its own parsing
# of the assertion, and hasn't been updated for the new BrowserID formats.
# Rather than blocking on that work, we use a simple work-alike that doesn't
# do any local inspection of the assertion.
@implementer(IBrowserIdVerifier)
class RemoteVerifier(object):

    def __init__(self, audiences=None, trusted_issuers=None,
                 allowed_issuers=None, verifier_url=None, timeout=None):
        # Since we don't parse the assertion locally, we cannot support
        # list- or pattern-based audience strings.
        if audiences is not None:
            assert isinstance(audiences, six.string_types)
        self.audiences = audiences
        if isinstance(trusted_issuers, six.string_types):
            trusted_issuers = trusted_issuers.split()
        self.trusted_issuers = trusted_issuers
        if isinstance(allowed_issuers, six.string_types):
            allowed_issuers = allowed_issuers.split()
        self.allowed_issuers = allowed_issuers
        if verifier_url is None:
            verifier_url = "https://verifier.accounts.firefox.com/v2"
        self.verifier_url = verifier_url
        if timeout is None:
            timeout = 30
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = True

    def verify(self, assertion, audience=None):
        if audience is None:
            audience = self.audiences

        body = {'assertion': assertion, 'audience': audience}
        if self.trusted_issuers is not None:
            body['trustedIssuers'] = self.trusted_issuers
        headers = {'content-type': 'application/json'}
        try:
            response = self.session.post(self.verifier_url,
                                         data=json.dumps(body),
                                         headers=headers,
                                         timeout=self.timeout)
        except (socket.error, requests.RequestException) as e:
            msg = "Failed to POST %s. Reason: %s" % (self.verifier_url, str(e))
            raise ConnectionError(msg)

        if response.status_code != 200:
            raise ConnectionError('server returned invalid response code')
        try:
            data = json.loads(response.text)
        except ValueError:
            raise ConnectionError("server returned invalid response body")

        if data.get('status') != "okay":
            reason = data.get('reason', 'unknown error')
            if "audience mismatch" in reason:
                raise AudienceMismatchError(data.get("audience"), audience)
            if "expired" in reason or "issued later than" in reason:
                raise ExpiredSignatureError(reason)
            raise InvalidSignatureError(reason)
        if self.allowed_issuers is not None:
            issuer = data.get('issuer')
            if issuer not in self.allowed_issuers:
                raise InvalidIssuerError("Issuer not allowed: %s" % (issuer,))
        return data
