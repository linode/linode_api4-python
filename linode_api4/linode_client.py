from __future__ import annotations

import json
import logging
from importlib.metadata import version
from typing import BinaryIO, Tuple
from urllib import parse

import requests
from requests.adapters import HTTPAdapter, Retry

from linode_api4.errors import ApiError, UnexpectedResponseError
from linode_api4.groups import (
    AccountGroup,
    BetaProgramGroup,
    DatabaseGroup,
    DomainGroup,
    ImageGroup,
    LinodeGroup,
    LKEGroup,
    LongviewGroup,
    NetworkingGroup,
    NodeBalancerGroup,
    ObjectStorageGroup,
    PollingGroup,
    ProfileGroup,
    RegionGroup,
    SupportGroup,
    TagGroup,
    VolumeGroup,
    VPCGroup,
)
from linode_api4.objects import Image, and_
from linode_api4.objects.filtering import Filter

from .common import SSH_KEY_TYPES, load_and_validate_keys
from .paginated_list import PaginatedList
from .util import drop_null_keys

package_version = version("linode_api4")

logger = logging.getLogger(__name__)


class LinearRetry(Retry):
    """
    Linear retry is a subclass of Retry that uses a linear backoff strategy.
    This is necessary to maintain backwards compatibility with the old retry system.
    """

    def get_backoff_time(self):
        return self.backoff_factor


class LinodeClient:
    def __init__(
        self,
        token,
        base_url="https://api.linode.com/v4",
        user_agent=None,
        page_size=None,
        retry=True,
        retry_rate_limit_interval=1.0,
        retry_max=5,
        retry_statuses=None,
        ca_path=None,
    ):
        """
        The main interface to the Linode API.

        :param token: The authentication token to use for communication with the
                      API.  Can be either a Personal Access Token or an OAuth Token.
        :type token: str
        :param base_url: The base URL for API requests.  Generally, you shouldn't
                         change this.
        :type base_url: str
        :param user_agent: What to append to the User Agent of all requests made
                           by this client.  Setting this allows Linode's internal
                           monitoring applications to track the usage of your
                           application.  Setting this is not necessary, but some
                           applications may desire this behavior.
        :type user_agent: str
        :param page_size: The default size to request pages at.  If not given,
                                  the API's default page size is used.  Valid values
                                  can be found in the API docs, but at time of writing
                                  are between 25 and 500.
        :type page_size: int
        :param retry: Whether API requests should automatically be retries on known
                      intermittent responses.
        :type retry: bool
        :param retry_rate_limit_interval: The amount of time to wait between HTTP request
                                          retries.
        :type retry_rate_limit_interval: Union[float, int]
        :param retry_max: The number of request retries that should be attempted before
                          raising an API error.
        :type retry_max: int
        :type retry_statuses: List of int
        :param retry_statuses: Additional HTTP response statuses to retry on.
                               By default, the client will retry on 408, 429, and 502
                               responses.
        :param ca_path: The path to a CA file to use for API requests in this client.
        :type ca_path: str
        """
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token
        self.page_size = page_size
        self.ca_path = ca_path

        retry_forcelist = [408, 429, 502]

        if retry_statuses is not None:
            retry_forcelist.extend(retry_statuses)

        # Ensure the max retries value is valid
        if not isinstance(retry_max, int):
            raise ValueError("retry_max must be an int")

        self.retry = retry
        self.retry_rate_limit_interval = float(retry_rate_limit_interval)
        self.retry_max = retry_max
        self.retry_statuses = retry_forcelist

        # Initialize the HTTP client session
        self.session = requests.Session()

        self._retry_config = LinearRetry(
            total=retry_max if retry else 0,
            status_forcelist=self.retry_statuses,
            respect_retry_after_header=True,
            backoff_factor=self.retry_rate_limit_interval,
            raise_on_status=False,
            # By default, POST is not an allowed method.
            # We should explicitly include it.
            allowed_methods={"DELETE", "GET", "POST", "PUT"},
        )
        retry_adapter = HTTPAdapter(max_retries=self._retry_config)

        self.session.mount("http://", retry_adapter)
        self.session.mount("https://", retry_adapter)

        #: Access methods related to Linodes - see :any:`LinodeGroup` for
        #: more information
        self.linode = LinodeGroup(self)

        #: Access methods related to your user - see :any:`ProfileGroup` for
        #: more information
        self.profile = ProfileGroup(self)

        #: Access methods related to your account - see :any:`AccountGroup` for
        #: more information
        self.account = AccountGroup(self)

        #: Access methods related to networking on your account - see
        #: :any:`NetworkingGroup` for more information
        self.networking = NetworkingGroup(self)

        #: Access methods related to support - see :any:`SupportGroup` for more
        #: information
        self.support = SupportGroup(self)

        #: Access information related to the Longview service - see
        #: :any:`LongviewGroup` for more information
        self.longview = LongviewGroup(self)

        #: Access methods related to Object Storage - see :any:`ObjectStorageGroup`
        #: for more information
        self.object_storage = ObjectStorageGroup(self)

        #: Access methods related to LKE - see :any:`LKEGroup` for more information.
        self.lke = LKEGroup(self)

        #: Access methods related to Managed Databases - see :any:`DatabaseGroup` for more information.
        self.database = DatabaseGroup(self)

        #: Access methods related to NodeBalancers - see :any:`NodeBalancerGroup` for more information.
        self.nodebalancers = NodeBalancerGroup(self)

        #: Access methods related to Domains - see :any:`DomainGroup` for more information.
        self.domains = DomainGroup(self)

        #: Access methods related to Tags - See :any:`TagGroup` for more information.
        self.tags = TagGroup(self)

        #: Access methods related to Volumes - See :any:`VolumeGroup` for more information.
        self.volumes = VolumeGroup(self)

        #: Access methods related to Regions - See :any:`RegionGroup` for more information.
        self.regions = RegionGroup(self)

        #: Access methods related to Images - See :any:`ImageGroup` for more information.
        self.images = ImageGroup(self)

        #: Access methods related to VPCs - See :any:`VPCGroup` for more information.
        self.vpcs = VPCGroup(self)

        #: Access methods related to Event polling - See :any:`PollingGroup` for more information.
        self.polling = PollingGroup(self)

        #: Access methods related to Beta Program - See :any:`BetaProgramGroup` for more information.
        self.beta = BetaProgramGroup(self)

    @property
    def _user_agent(self):
        return "{}python-linode_api4/{} {}".format(
            "{} ".format(self._add_user_agent) if self._add_user_agent else "",
            package_version,
            requests.utils.default_user_agent(),
        )

    def load(self, target_type, target_id, target_parent_id=None):
        """
        Constructs and immediately loads the object, circumventing the
        lazy-loading scheme by immediately making an API request.  Does not
        load related objects.

        For example, if you wanted to load an :any:`Instance` object with ID 123,
        you could do this::

           loaded_linode = client.load(Instance, 123)

        Similarly, if you instead wanted to load a :any:`NodeBalancerConfig`,
        you could do so like this::

           loaded_nodebalancer_config = client.load(NodeBalancerConfig, 456, 432)

        :param target_type: The type of object to create.
        :type target_type: type
        :param target_id: The ID of the object to create.
        :type target_id: int or str
        :param target_parent_id: The parent ID of the object to create, if
                                 applicable.
        :type target_parent_id: int, str, or None

        :returns: The resulting object, fully loaded.
        :rtype: target_type
        :raise ApiError: if the requested object could not be loaded.
        """
        result = target_type.make_instance(
            target_id, self, parent_id=target_parent_id
        )
        result._api_get()

        return result

    def _api_call(
        self, endpoint, model=None, method=None, data=None, filters=None
    ):
        """
        Makes a call to the linode api.  Data should only be given if the method is
        POST or PUT, and should be a dictionary
        """
        if not self.token:
            raise RuntimeError("You do not have an API token!")

        if not method:
            raise ValueError("Method is required for API calls!")

        if model:
            endpoint = endpoint.format(
                **{k: parse.quote(str(v)) for k, v in vars(model).items()}
            )

        url = "{}{}".format(self.base_url, endpoint)
        headers = {
            "Authorization": "Bearer {}".format(self.token),
            "Content-Type": "application/json",
            "User-Agent": self._user_agent,
        }

        if filters:
            headers["X-Filter"] = json.dumps(filters)

        body = None
        if data is not None:
            body = json.dumps(data)

        response = method(
            url,
            headers=headers,
            data=body,
            verify=self.ca_path or self.session.verify,
        )

        warning = response.headers.get("Warning", None)
        if warning:
            logger.warning("Received warning from server: {}".format(warning))

        if 399 < response.status_code < 600:
            j = None
            error_msg = "{}: ".format(response.status_code)
            try:
                j = response.json()
                if "errors" in j.keys():
                    for e in j["errors"]:
                        msg = e.get("reason", "")
                        field = e.get("field", None)

                        error_msg += "{}{}; ".format(
                            f"[{field}] " if field is not None else "",
                            msg,
                        )
            except:
                pass
            raise ApiError(error_msg, status=response.status_code, json=j)

        if response.status_code != 204:
            j = response.json()
        else:
            j = None  # handle no response body

        return j

    def _get_objects(
        self, endpoint, cls, model=None, parent_id=None, filters=None
    ):
        # handle non-default page sizes
        call_endpoint = endpoint
        if self.page_size is not None:
            call_endpoint += "?page_size={}".format(self.page_size)

        response_json = self.get(call_endpoint, model=model, filters=filters)

        if not "data" in response_json:
            raise UnexpectedResponseError(
                "Problem with response!", json=response_json
            )

        if "pages" in response_json:
            formatted_endpoint = endpoint
            if model:
                formatted_endpoint = formatted_endpoint.format(**vars(model))
            return PaginatedList.make_paginated_list(
                response_json,
                self,
                cls,
                parent_id=parent_id,
                page_url=formatted_endpoint[1:],
                filters=filters,
            )
        return PaginatedList.make_list(
            response_json["data"], self, cls, parent_id=parent_id
        )

    def get(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.get, **kwargs)

    def post(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.post, **kwargs)

    def put(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.put, **kwargs)

    def delete(self, *args, **kwargs):
        return self._api_call(*args, method=self.session.delete, **kwargs)

    def __setattr__(self, key, value):
        # Allow for dynamic updating of the retry config
        handlers = {
            "retry_rate_limit_interval": lambda: setattr(
                self._retry_config, "backoff_factor", value
            ),
            "retry": lambda: setattr(
                self._retry_config, "total", self.retry_max if value else 0
            ),
            "retry_max": lambda: setattr(
                self._retry_config, "total", value if self.retry else 0
            ),
            "retry_statuses": lambda: setattr(
                self._retry_config, "status_forcelist", value
            ),
        }

        handler = handlers.get(key)
        if hasattr(self, "_retry_config") and handler is not None:
            handler()

        super().__setattr__(key, value)

    def image_create(self, disk, label=None, description=None):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.images.create(...) <.ImageGroup.create>` for all new projects.
        """
        return self.images.create(disk, label=label, description=description)

    def image_create_upload(
        self, label: str, region: str, description: str = None
    ) -> Tuple[Image, str]:
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.images.create_upload(...) <.ImageGroup.create_upload>`
                  for all new projects.
        """

        return self.images.create_upload(label, region, description=description)

    def image_upload(
        self, label: str, region: str, file: BinaryIO, description: str = None
    ) -> Image:
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.images.upload(...) <.ImageGroup.upload>` for all new projects.
        """
        return self.images.upload(label, region, file, description=description)

    def nodebalancer_create(self, region, **kwargs):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use
                  :meth:`LinodeClient.nodebalancers.create(...) <.NodeBalancerGroup.create>`
                  for all new projects.
        """
        return self.nodebalancers.create(region, **kwargs)

    def domain_create(self, domain, master=True, **kwargs):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.domains.create(...) <.DomainGroup.create>` for all
                  new projects.
        """
        return self.domains.create(domain, master=master, **kwargs)

    def tag_create(
        self,
        label,
        instances=None,
        domains=None,
        nodebalancers=None,
        volumes=None,
        entities=[],
    ):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.tags.create(...) <.TagGroup.create>` for all new projects.
        """
        return self.tags.create(
            label,
            instances=instances,
            domains=domains,
            nodebalancers=nodebalancers,
            volumes=volumes,
            entities=entities,
        )

    def volume_create(self, label, region=None, linode=None, size=20, **kwargs):
        """
        .. note:: This method is an alias to maintain backwards compatibility.
                  Please use :meth:`LinodeClient.volumes.create(...) <.VolumeGroup.create>` for all new projects.
        """
        return self.volumes.create(
            label, region=region, linode=linode, size=size, **kwargs
        )

    # helper functions
    def _get_and_filter(self, obj_type, *filters, endpoint=None):
        parsed_filters = None
        if filters:
            if len(filters) > 1:
                parsed_filters = and_(
                    *filters
                ).dct  # pylint: disable=no-value-for-parameter
            else:
                parsed_filters = filters[0].dct

        # Use sepcified endpoint
        if endpoint:
            return self._get_objects(endpoint, obj_type, filters=parsed_filters)
        else:
            return self._get_objects(
                obj_type.api_list(), obj_type, filters=parsed_filters
            )
