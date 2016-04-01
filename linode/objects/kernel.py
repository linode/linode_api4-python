from .base import Base, Property

class Kernel(Base):
    api_endpoint="/kernels/{id}"
    properties = {
        "created": Property(is_datetime=True),
        "deprecated": Property(filterable=True),
        "description": Property(),
        "id": Property(identifier=True),
        "kvm": Property(filterable=True),
        "label": Property(filterable=True),
        "updates": Property(),
        "version": Property(filterable=True),
        "x64": Property(filterable=True),
        "xen": Property(filterable=True),
    }
