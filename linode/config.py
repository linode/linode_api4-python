from os import path

file_path = path.expanduser('~/.linode/api_token')
api_token = open(file_path).read().rstrip()

base_path = path.expanduser('~/.linode/base_url')
base_url = open(base_path).read().rstrip()
