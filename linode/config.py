from datetime import timedelta

api_token = None
base_url = "http://api.linode.com/v1"
volatile_refresh_timeout = timedelta(seconds=15)

def initialize(token):
    global api_token
    api_token = token
