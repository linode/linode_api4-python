from __future__ import absolute_import

from datetime import datetime, timedelta
from enum import Enum

import requests

from linode_api4.errors import ApiError

try:
    from urllib.parse import urlparse
    from urllib.parse import urlencode
    from urllib.parse import urlunparse
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urlparse import urlunparse

class AllWrapper():
    def __repr__(self):
        return '*'

class OAuthScopes:
    """
    Represents the OAuth Scopes available to an application.  In general, an
    application should request no more scopes than it requires.  This class
    should be treated like a Enum, and used as follows::

       required_scopes = [OAuthScopes.Linodes.all, OAuthScopes.Domains.read_only]

    Lists of OAuth Scopes are accepted when calling the :any:`generate_login_url`
    method of the :any:`LinodeLoginClient`.

    All contained enumerations of OAuth Scopes have two levels, "read_only" and
    "read_write".  "read_only" access grants you the ability to get resources and
    of that type, but not to change, create, or delete them.  "read_write" access
    allows to full access to resources of the requested type.  In the above
    example, you are requesting access to view, modify, create, and delete
    Linodes, and to view Domains.
    """

    #: If necessary, an application may request all scopes by using OAuthScopes.all
    all = AllWrapper()

    class Linodes(Enum):
        """
        Access to Linodes
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "linodes:*"
            return "linodes:{}".format(self.name)

    class Domains(Enum):
        """
        Access to Domains
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "domains:*"
            return "domains:{}".format(self.name)

    class StackScripts(Enum):
        """
        Access to private StackScripts
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "stackscripts:*"
            return "stackscripts:{}".format(self.name)

    class Users(Enum):
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "users:*"
            return "users:{}".format(self.name)

    class NodeBalancers(Enum):
        """
        Access to NodeBalancers
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "nodebalancers:*"
            return "nodebalancers:{}".format(self.name)

    class Tokens(Enum):
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "tokens:*"
            return "tokens:{}".format(self.name)

    class IPs(Enum):
        """
        Access to IPs and networking managements
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "ips:*"
            return "ips:{}".format(self.name)

    class Tickets(Enum):
        """
        Access to view, open, and respond to Support Tickets
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "tickets:*"
            return "tickets:{}".format(self.name)

    class Clients(Enum):
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "clients:*"
            return "clients:{}".format(self.name)

    class Account(Enum):
        """
        Access to the user's account, including billing information, tokens
        management, user management, etc.
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "account:*"
            return "account:{}".format(self.name)

    class Events(Enum):
        """
        Access to a user's Events
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "events:*"
            return "events:{}".format(self.name)

    class Volumes(Enum):
        """
        Access to Block Storage Volumes
        """
        view = 0
        create = 1
        modify = 2
        delete = 3
        all = 4

        def __repr__(self):
            if(self.name == 'all'):
                return "volumes:*"
            return "volumes:{}".format(self.name)

    _scope_families = {
        'linodes': Linodes,
        'domains': Domains,
        'stackscripts': StackScripts,
        'users': Users,
        'tokens': Tokens,
    }

    @staticmethod
    def parse(scopes):
        ret = []

        # special all-scope case
        if scopes == '*':
            return [ getattr(OAuthScopes._scope_families[s], 'all')
                    for s in OAuthScopes._scope_families ]

        for scope in scopes.split(','):
            resource = access = None
            if ':' in scope:
                resource, access = scope.split(':')
            else:
                resource = scope
                access = '*'

            parsed_scope = OAuthScopes._get_parsed_scope(resource, access)
            if parsed_scope:
                ret.append(parsed_scope)

        return ret

    @staticmethod
    def _get_parsed_scope(resource, access):
        resource = resource.lower()
        access = access.lower()
        if resource in OAuthScopes._scope_families:
            if access == '*':
                access = 'delete'
            if hasattr(OAuthScopes._scope_families[resource], access):
                return getattr(OAuthScopes._scope_families[resource], access)

        return None

    @staticmethod
    def serialize(scopes):
        ret = ''
        if not type(scopes) is list:
            scopes = [ scopes ]
        for scope in scopes:
            ret += "{},".format(repr(scope))
        if ret:
            ret = ret[:-1]
        return ret

class LinodeLoginClient:
    def __init__(self, client_id, client_secret,
                 base_url="https://login.linode.com"):
        """
        Create a new LinodeLoginClient.  These clients do not make any requests
        on creation, and can safely be created and thrown away as needed.

        For complete usage information, see the :doc:`OAuth guide<../guides/oauth>`.

        :param client_id: The OAuth Client ID for this client.
        :type client_id: str
        :param client_secret: The OAuth Client Secret for this client.
        :type client_secret: str
        :param base_url: The URL for Linode's OAuth server.  This should not be
                         changed.
        :type base_url: str
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

    def _login_uri(self, path):
        return "{}{}".format(self.base_url, path)

    def generate_login_url(self, scopes=None, redirect_uri=None):
        """
        Generates a url to send users so that they may authenticate to this
        application.  This url is suitable for redirecting a user to.  For
        example, in `Flask`_, a login route might be implemented like this::

           @app.route("/login")
           def begin_oauth_login():
               login_client = LinodeLoginClient(client_id, client_secret)
               return redirect(login_client.generate_login_url())

        .. _Flask:: http://flask.pocoo.org

        :param scopes: The OAuth scopes to request for this login.
        :type scopes: list
        :param redirect_uri: The requested redirect uri.  The login service
                             enforces that this is under the registered redirect
                             path.
        :type redirect_uri: str

        :returns: The uri to send users to for this login attempt.
        :rtype: str
        """
        url = self.base_url + "/oauth/authorize"
        split = list(urlparse(url))
        params = {
            "client_id": self.client_id,
            "response_type": "code", # needed for all logins
        }
        if scopes:
            params["scopes"] = OAuthScopes.serialize(scopes)
        if redirect_uri:
            params["redirect_uri"] = redirect_uri
        split[4] = urlencode(params)
        return urlunparse(split)

    def finish_oauth(self, code):
        """
        Given an OAuth Exchange Code, completes the OAuth exchange with the
        authentication server.  This should be called once the user has already
        been directed to the login_uri, and has been sent back after successfully
        authenticating.  For example, in `Flask`_, this might be implemented as
        a route like this::

           @app.route("/oauth-redirect")
           def oauth_redirect():
               exchange_code = request.args.get("code")
               login_client = LinodeLoginClient(client_id, client_secret)

               token, scopes = login_client.finish_oauth(exchange_code)

               # store the user's OAuth token in their session for later use
               # and mark that they are logged in.

               return redirect("/")

        .. _Flask: http://flask.pocoo.org

        :param code: The OAuth Exchange Code returned from the authentication
                     server in the query string.
        :type code: str

        :returns: The new OAuth token, and a list of scopes the token has, when
                  the token expires, and a refresh token that can generate a new
                  valid token when this one is expired.
        :rtype: tuple(str, list)

        :raise ApiError: If the OAuth exchange fails.
        """
        r = requests.post(self._login_uri("/oauth/token"), data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })

        if r.status_code != 200:
            raise ApiError("OAuth token exchange failed", status=r.status_code, json=r.json())

        token = r.json()["access_token"]
        scopes = OAuthScopes.parse(r.json()["scopes"])
        expiry = datetime.now() + timedelta(seconds=r.json()['expires_in'])
        refresh_token = r.json()['refresh_token']

        return token, scopes, expiry, refresh_token

    def refresh_oauth_token(self, refresh_token):
        """
        Some tokens are generated with refresh tokens (namely tokens generated
        through an OAuth Exchange).  These tokens may be renewed, or "refreshed",
        with the auth server, generating a new OAuth Token with a new (later)
        expiry.  This method handles refreshing an OAuth Token using the refresh
        token that was generated at the time of its issuance, and returns a new
        OAuth token and refresh token for the same client and user.

        :param refresh_token: The refresh token returned for the OAuth Token we
                              are renewing.
        :type refresh_token: str

        :returns: The new OAuth token, and a list of scopes the token has, when
                  the token expires, and a refresh token that can generate a new
                  valid token when this one is expired.
        :rtype: tuple(str, list)

        :raise ApiError: If the refresh fails..
        """
        r = requests.post(self._login_uri("/oauth/token"), data={
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        })

        if r.status_code != 200:
            raise ApiError("Refresh failed", r)

        token = r.json()["access_token"]
        scopes = OAuthScopes.parse(r.json()["scopes"])
        expiry = datetime.now() + timedelta(seconds=r.json()['expires_in'])
        refresh_token = r.json()['refresh_token']

        return token, scopes, expiry, refresh_token

    def expire_token(self, token):
        """
        Given a token, makes a request to the authentication server to expire
        it immediately.  This is considered a responsible way to log out a
        user.  If you simply remove the session your application has for the
        user without expiring their token, the user is not _really_ logged out.

        :param token: The OAuth token you wish to expire
        :type token: str

        :returns: If the expiration attempt succeeded.
        :rtype: bool

        :raises ApiError: If the expiration attempt failed.
        """
        r = requests.post(self._login_uri("/oauth/token/expire"),
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token": token,
            })

        if r.status_code != 200:
            raise ApiError("Failed to expire token!", r)
        return True
