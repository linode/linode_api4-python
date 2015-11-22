from datetime import timedelta

# The api token we are using to requests
api_token = None

# The URL to reach the API at
base_url = "http://api.linode.com/v1"

# The interval to reload volatile properties
volatile_refresh_timeout = timedelta(seconds=15)

# Turn off raising errors on failed API requests
mute_errors=False

def initialize(token):
    """
    A graceful way to set the api token
    """
    global api_token
    api_token = token
