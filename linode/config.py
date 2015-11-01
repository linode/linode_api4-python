from os import path
from datetime import timedelta

file_path = path.expanduser('~/.linode/api_token')
api_token = open(file_path).read().rstrip()

base_path = path.expanduser('~/.linode/base_url')
base_url = open(base_path).read().rstrip()

volatile_refresh_timeout = timedelta(seconds=15)
