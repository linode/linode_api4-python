import requests

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

    def get_thumbnail(self, dump_to=None):
        """
        This returns binary data that represents a 128x128 image.
        If dump_to is given, attempts to write the image to a file
        at the given location.
        """
        headers = {
            "Authorization": "token {}".format(self._client.token)
        }

        result = requests.get('{}/{}/thumbnail'.format(self._client.base_url,
                OAuthClient.api_endpoint.format(id=self.id)),
                headers=headers)

        if not result.status_code == 200:
            return False # TODO - handle this better?

        if dump_to:
            with open(dump_to, 'wb+') as f: # TODO -python2?
                f.write(result.content)
        else:
            return result.content

    def set_thumbnail(self, thumb):
        # TODO
        pass
