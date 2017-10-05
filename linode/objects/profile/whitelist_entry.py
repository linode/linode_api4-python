from ...errors import UnexpectedResponseError
from .. import Base, Property

class WhitelistEntry(Base):
    api_endpoint = "/profile/whitelist/{id}"

    properties = {
        'id': Property(identifier=True),
        'address': Property(),
        'netmask': Property(),
        'note': Property(),
    }

