from linode.objects import Base, Property

class User(Base):
    api_name = 'users'
    api_endpoint = "/account/users/{id}"
    id_attribute = 'username'

    properties = {
        'email': Property(mutable=True),
        'username': Property(identifier=True, mutable=True),
        'restricted': Property(mutable=True),
    }

    @property
    def grants(self):
        from linode.objects.account import UserGrants
        resp = self._client.get(UserGrants.api_endpoint.format(username=self.username))

        grants = UserGrants(self._client, self.username)
        grants._populate(resp)
        return grants

    def change_password(self, password):
        """
        Sets this user's password
        """
        result = self._client.post('{}/password'.format(User.api_endpoint),
                model=self, data={ "password": password })

        return True
