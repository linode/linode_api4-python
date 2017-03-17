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
        if not hasattr(self, '_grants'):
            resp = self._client.get(UserGrants.api_endpoint.format(username=self.username))

            grants = UserGrants(self._client, self.username)
            grants._populate(resp)
            self._set('_grants', grants)

        return self._grants

    def invalidate(self):
        if hasattr(self, '_grants'):
            del self._grants
        Base.invalidate(self)

    def change_password(self, password):
        """
        Sets this user's password
        """
        result = self._client.post('{}/password'.format(User.api_endpoint),
                model=self, data={ "password": password })

        return True
