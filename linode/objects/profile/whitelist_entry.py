from __future__ import absolute_import

from linode.objects import Base, Property


class WhitelistEntry(Base):
    api_endpoint = "/profile/whitelist/{id}"

    properties = {
        'id': Property(identifier=True),
        'address': Property(),
        'netmask': Property(),
        'note': Property(),
    }
