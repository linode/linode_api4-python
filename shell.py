#!/usr/local/bin/python3
import linode
from linode import config
from linode.linode_client import LinodeClient

from os import path, makedirs
import code
import getpass


no_token_message = """You must have an oauth token to access the api.  To generate a token,
see documentation at developer.linode.com
"""

file_path = path.expanduser('~/.linode/api_token')
if not path.isfile(file_path):
    print(no_token_message)
    token = getpass.getpass('oauth token: ')
    if token:
        makedirs(path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(token)
    else:
        raise ValueError('You must have an oauth token to use the api shell')

api_token = open(file_path).read().rstrip()

base_path = path.expanduser('~/.linode/base_url')
base_url = None
if path.isfile(base_path):
    base_url = open(base_path).read().rstrip()

lc = LinodeClient(api_token, base_url=base_url)

banner="""## DEV MODE ##
>>> import linode
>>> from linode import LinodeClient
>>> lc = LinodeClient( ... )"""

code.interact(local=locals(), banner=banner)
