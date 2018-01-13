from __future__ import absolute_import

from linode.objects import Base, Property


class User(Base):
    api_endpoint = "/account/users/{id}"
    id_attribute = 'username'

    properties = {
        'email': Property(mutable=True),
        'username': Property(identifier=True, mutable=True),
        'restricted': Property(mutable=True),
    }

    @property
    def grants(self):
        """
        Retrieves the grants for this user.  If the user is unrestricted, this
        will result in an ApiError.  This is smart, and will only fetch from the
        api once unless the object is invalidated.

        :returns: The grants for this user.
        :rtype: linode.objects.account.UserGrants
        """
        from linode.objects.account import UserGrants
        if not hasattr(self, '_grants'):
            resp = self._client.get(UserGrants.api_endpoint.format(username=self.username))

            grants = UserGrants(self._client, self.username, resp)
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
        self._client.post('{}/password'.format(User.api_endpoint),
                model=self, data={ "password": password })

        return True
