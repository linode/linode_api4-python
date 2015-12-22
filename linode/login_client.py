import urllib.parse
import requests
from .api import ApiError

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
        split = list(urllib.parse.urlparse(url))
        params = {
            "client_id": self.client_id,
        }
        if scopes:
            params["scopes"] = scopes
        if redirect_uri:
            params["redirect_uri"] = redirect_uri
        split[4] = urllib.parse.urlencode(params)
        return urllib.parse.urlunparse(split)

    def finish_oauth(self, code):
        r = requests.post(self._login_uri("/oauth/token"), data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
        if r.status_code != 200:
            raise ApiError("OAuth token exchange failed", r)
        token = r.json()["access_token"]
        scopes = r.json()["scopes"]
        return token, scopes
