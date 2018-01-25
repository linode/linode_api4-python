from __future__ import absolute_import

from linode.objects import Base, Property
from linode.objects.longview import LongviewSubscription


class AccountSettings(Base):
    api_endpoint = "/account/settings"
    id_attribute = 'managed' # this isn't actually used

    properties = {
        "network_helper": Property(mutable=True),
        "managed": Property(),
        "longview_subscription": Property(slug_relationship=LongviewSubscription)
    }
