import json
from unittest import TestCase
from unittest.mock import patch
import requests
import json
import sys

from linode import LinodeClient

class MockResponse:
    def __init__(self, status_code, json):
        self.status_code = status_code
        self._json = json

    def json(self):
        return self._json

def mock_get(url, headers=None, data=None):
    """
    Loads the response from a JSON file
    """
    file_path = sys.path[0] + '/responses/GET/' + url + '.json'

    with open(file_path) as f:
        response = f.read()

    return MockResponse(200, json.loads(response))


class ClientBaseCase(TestCase):
    def setUp(self):
        self.client = LinodeClient('testing', base_url='/')

        self.get_patch = patch('linode.linode_client.requests.get',
                side_effect=mock_get)
        self.get_patch.start()

    def tearDown(self):
        self.get_patch.stop()
