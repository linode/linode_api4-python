from __future__ import annotations

import json
import logging
import time
from typing import BinaryIO, Tuple

import pkg_resources
import requests

from linode_api4.errors import ApiError, UnexpectedResponseError
from linode_api4.groups import *
from linode_api4.objects import *
from linode_api4.objects.filtering import Filter

from .common import SSH_KEY_TYPES, load_and_validate_keys
from .paginated_list import PaginatedList
from .util import drop_null_keys

package_version = pkg_resources.require("linode_api4")[0].version

logger = logging.getLogger(__name__)


class LinodeClient:
    def __init__(
        self,
        token,
        base_url="https://api.linode.com/v4",
        user_agent=None,
        page_size=None,
        retry_rate_limit_interval=None,
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
        :param retry_rate_limit_interval: If given, 429 responses will be automatically
                                         retried up to 5 times with the given interval,
                                         in seconds, between attempts.
        :type retry_rate_limit_interval: int
        """
        self.base_url = base_url
        self._add_user_agent = user_agent
        self.token = token
        self.session = requests.Session()
        self.page_size = page_size
        self.retry_rate_limit_interval = retry_rate_limit_interval

        # make sure we got a sane backoff
        if self.retry_rate_limit_interval is not None:
            if not isinstance(self.retry_rate_limit_interval, int):
                raise ValueError("retry_rate_limit_interval must be an int")
            if self.retry_rate_limit_interval < 1:
                raise ValueError(
                    "retry_rate_limit_interval must not be less than 1"
                )

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
            endpoint = endpoint.format(**vars(model))
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

        # retry on 429 response
        max_retries = 5 if self.retry_rate_limit_interval else 1
        for attempt in range(max_retries):
            response = method(url, headers=headers, data=body)

            warning = response.headers.get("Warning", None)
            if warning:
                logger.warning(
                    "Received warning from server: {}".format(warning)
                )

            # if we were configured to retry 429s, and we got a 429, sleep briefly and then retry
            if self.retry_rate_limit_interval and response.status_code == 429:
                logger.warning(
                    "Received 429 response; waiting {} seconds and retrying request (attempt {}/{})".format(
                        self.retry_rate_limit_interval,
                        attempt,
                        max_retries,
                    )
                )
                time.sleep(self.retry_rate_limit_interval)
            else:
                break

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
