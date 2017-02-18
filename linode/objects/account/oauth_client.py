from linode.objects import Base, Property

class OAuthClient(Base):
    api_name = 'clients'
    api_endpoint = "/account/clients/{id}"

    properties = {
        "id": Property(identifier=True),
        "name": Property(mutable=True, filterable=True),
        "secret": Property(),
        "redirect_uri": Property(mutable=True),
        "status": Property(),
    }

    def reset_secret(self):
        """
        Resets the client secret for this client.
        """
        result = self._client.post("{}/reset_secret".format(OAuthClient.api_endpoint), model=self)

        if not 'id' in result:
            return result

        self._populate(result)
        return self.secret
