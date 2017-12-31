from __future__ import absolute_import

from linode.objects import Base, Property


class PersonalAccessToken(Base):
    api_endpoint = "/profile/tokens/{id}"

    properties = {
        "id": Property(identifier=True),
        "scopes": Property(),
        "label": Property(mutable=True),
        "created": Property(is_datetime=True),
        "token": Property(),
        "expiry": Property(is_datetime=True),
    }
