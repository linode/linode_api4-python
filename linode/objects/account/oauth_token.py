from linode.objects import Base, Property
from linode.objects.account import OAuthClient

class OAuthToken(Base):
    api_name = 'tokens'
    api_endpoint = "/account/tokens/{id}"

    properties = {
        "id": Property(identifier=True),
        "client": Property(relationship=OAuthClient),
        "type": Property(),
        "scopes": Property(),
        "label": Property(mutable=True),
        "created": Property(is_datetime=True),
        "token": Property(),
        "expiry": Property(is_datetime=True),
    }
