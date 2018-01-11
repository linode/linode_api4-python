from __future__ import absolute_import

from enum import Enum

import requests
from linode.errors import ApiError

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

    all = AllWrapper()

    class Linodes(Enum):
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
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

    def _login_uri(self, path):
        return "{}{}".format(self.base_url, path)

    def generate_login_url(self, scopes=None, redirect_uri=None):
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
        r = requests.post(self._login_uri("/oauth/token"), data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
        if r.status_code != 200:
            raise ApiError("OAuth token exchange failed", r)
        token = r.json()["access_token"]
        scopes = OAuthScopes.parse(r.json()["scopes"])
        return token, scopes

    def expire_token(self, token):
        r = requests.post(self._login_uri("/oauth/token/expire"),
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token": token,
            })

        if r.status_code != 200:
            raise ApiError("Failed to expire token!", r)
        return True
