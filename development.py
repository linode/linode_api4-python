#!/usr/local/bin/python3
import linode
from linode import config

from os import path
import code

file_path = path.expanduser('~/.linode/api_token')
api_token = open(file_path).read().rstrip()

base_path = path.expanduser('~/.linode/base_url')
base_url = open(base_path).read().rstrip()

config.api_token = api_token
config.base_url = base_url

banner="""## DEV MODE ##
>>> import linode"""

code.interact(local=locals(), banner=banner)
