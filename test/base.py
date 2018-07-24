import json
from unittest import TestCase

from mock import patch

from linode_api4 import LinodeClient

from .fixtures import TestFixtures

FIXTURES = TestFixtures()

class MockResponse:
    def __init__(self, status_code, json, headers={}):
        self.status_code = status_code
        self._json = json
        # Headers is a dict, do not want to use a getter here
        self.headers = headers

    def json(self):
        return self._json


def load_json(url):
    """
    Returns a dict from a .json file living in /test/response/GET/{url}.json

    :param url: The URL being accessed whose JSON is to be returned

    :returns: A dict containing the loaded JSON from that file
    """
    formatted_url = url

    while formatted_url.startswith('/'):
        formatted_url = formatted_url[1:]

    return FIXTURES.get_fixture(formatted_url)


def mock_get(url, headers=None, data=None):
    """
    Loads the response from a JSON file
    """
    response = load_json(url)

    return MockResponse(200, response)


class MethodMock:
    """
    This class is used to mock methods on requests and store the parameters
    and headers it was called with.
    """
    def __init__(self, method, return_dct):
        """
        Creates and initiates a new MethodMock with the given details

        :param method: The HTTP method we are mocking
        :param return_dct: The python dct to returned, or the URL for a JSON
            file to return
        """
        self.method = method
        if isinstance(return_dct, dict):
            self.return_dct = return_dct
        elif isinstance(return_dct, str):
            self.return_dct = load_json(return_dct)
        else:
            raise TypeError('return_dct must be a dict or a URL from which the '
                            'JSON could be loaded')

    def __enter__(self):
        """
        Begins the method mocking
        """
        self.patch = patch(
            'linode_api4.linode_client.requests.Session.'+self.method,
            return_value=MockResponse(200, self.return_dct)
        )
        self.mock = self.patch.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Removed the mocked method
        """
        self.patch.stop()

    @property
    def call_args(self):
        """
        A shortcut to accessing the underlying mock object's call args
        """
        return self.mock.call_args

    @property
    def call_data_raw(self):
        """
        A shortcut to access the raw call data, not parsed as JSON
        """
        return self.mock.call_args[1]['data']


    @property
    def call_url(self):
        """
        A shortcut to accessing the URL called on the underlying mock.  We
        chop off the first character because our testing base_url has a leading
        / we don't want to see.
        """
        return self.mock.call_args[0][0][1:]

    @property
    def call_data(self):
        """
        A shortcut to getting the data param this was called with.  Removes all
        keys whose values are None
        """
        data = json.loads(self.mock.call_args[1]['data'])

        return { k: v for k, v in data.items() if v is not None }

    @property
    def call_headers(self):
        """
        A shortcut to getting the headers param this was called with
        """
        return self.mock.call_args[1]['headers']


class ClientBaseCase(TestCase):
    def setUp(self):
        self.client = LinodeClient('testing', base_url='/')

        self.get_patch = patch('linode_api4.linode_client.requests.Session.get',
                side_effect=mock_get)
        self.get_patch.start()

    def tearDown(self):
        self.get_patch.stop()


    def mock_get(self, return_dct):
        """
        Returns a MethodMock mocking a GET.  This should be used in a with
        statement.

        :param return_dct: The JSON that should be returned from this GET

        :returns: A MethodMock object who will capture the parameters of the
            mocked requests
        """
        return MethodMock('get', return_dct)

    def mock_post(self, return_dct):
        """
        Returns a MethodMock mocking a POST.  This should be used in a with
        statement.

        :param return_dct: The JSON that should be returned from this POST

        :returns: A MethodMock object who will capture the parameters of the
            mocked requests
        """
        return MethodMock('post', return_dct)

    def mock_put(self, return_dct):
        """
        Returns a MethodMock mocking a PUT.  This should be used in a with
        statement.

        :param return_dct: The JSON that should be returned from this PUT

        :returns: A MethodMock object who will capture the parameters of the
            mocked requests
        """
        return MethodMock('put', return_dct)

    def mock_delete(self):
        """
        Returns a MethodMock mocking a DELETE.  This should be used in a with
        statement.

        :param return_dct: The JSON that should be returned from this DELETE

        :returns: A MethodMock object who will capture the parameters of the
            mocked requests
        """
        return MethodMock('delete', {})
