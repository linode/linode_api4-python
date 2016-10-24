from linode.objects import Base, Property

class User(Base):
    api_name = 'user'
    api_endpoint = "/account/users/{id}"
    properties = {
        'id': Property(identifier=True),
        'email': Property(),
        'username': Property(),
    }
