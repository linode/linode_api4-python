from __future__ import absolute_import

import requests
from linode.errors import ApiError, UnexpectedResponseError
from linode.objects import Base, Property


class OAuthClient(Base):
    api_endpoint = "/account/oauth-clients/{id}"

    properties = {
        "id": Property(identifier=True),
        "label": Property(mutable=True, filterable=True),
        "secret": Property(),
        "redirect_uri": Property(mutable=True),
        "status": Property(),
        "public": Property(),
    }

    def reset_secret(self):
        """
        Resets the client secret for this client.
        """
        result = self._client.post("{}/reset_secret".format(OAuthClient.api_endpoint), model=self)

        if not 'id' in result:
            raise UnexpectedResponseError('Unexpected response when resetting secret!', json=result)

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
            raise ApiError('No thumbnail found for OAuthClient {}'.format(self.id))

        if dump_to:
            with open(dump_to, 'wb+') as f:
                f.write(result.content)
        return result.content

    def set_thumbnail(self, thumbnail):
        """
        Sets the thumbnail for this OAuth Client.  If thumbnail is bytes,
        uploads it as a png.  Otherwise, assumes thumbnail is a path to the
        thumbnail and reads it in as bytes before uploading.
        """
        headers = {
            "Authorization": "token {}".format(self._client.token),
            "Content-type": "image/png",
        }

        # TODO this check needs to be smarter - python2 doesn't do it right
        if not isinstance(thumbnail, bytes):
            with open(thumbnail, 'rb') as f:
                thumbnail = f.read()

        result = requests.put('{}/{}/thumbnail'.format(self._client.base_url,
                OAuthClient.api_endpoint.format(id=self.id)),
                headers=headers, data=thumbnail)

        if not result.status_code == 200:
            errors = []
            j = result.json()
            if 'errors' in j:
                errors = [ e['reason'] for e in j['errors'] ]
            raise ApiError('{}: {}'.format(result.status_code, errors), json=j)

        return True
