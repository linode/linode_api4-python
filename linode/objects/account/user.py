from linode.objects import Base, Property

class User(Base):
    api_name = 'users'
    api_endpoint = "/account/users/{id}"
    id_attribute = 'email'

    properties = {
        'email': Property(identifier=True),
        'username': Property(),
        'restricted': Property(),
    }
