from .base import Base, Property

class Image(Base):
    """
    An Image is something a Linode or Disk can be deployed from.
    """
    api_endpoint = '/images/{id}'

    properties = {
    	"id": Property(identifier=True),
	"label": Property(mutable=True),
	"description": Property(mutable=True),
	"status": Property(),
	"filesystem": Property(),
	"created": Property(is_datetime=True),
	"updated": Property(is_datetime=True),
	"type": Property(),
	"is_public": Property(),
	"last_used": Property(is_datetime=True),
        "vendor": Property(filterable=True),
    }
