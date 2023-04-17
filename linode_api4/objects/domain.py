from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property


class DomainRecord(DerivedBase):
    api_endpoint = "/domains/{domain_id}/records/{id}"
    derived_url_path = "records"
    parent_id_name = "domain_id"

    properties = {
        "id": Property(identifier=True),
        "domain_id": Property(identifier=True),
        "type": Property(),
        "name": Property(mutable=True, filterable=True),
        "target": Property(mutable=True, filterable=True),
        "priority": Property(mutable=True),
        "weight": Property(mutable=True),
        "port": Property(mutable=True),
        "service": Property(mutable=True),
        "protocol": Property(mutable=True),
        "ttl_sec": Property(mutable=True),
        "tag": Property(mutable=True),
        "created": Property(),
        "updated": Property(),
    }


class Domain(Base):
    api_endpoint = "/domains/{id}"
    properties = {
        "id": Property(identifier=True),
        "domain": Property(mutable=True, filterable=True),
        "group": Property(mutable=True, filterable=True),
        "description": Property(mutable=True),
        "status": Property(mutable=True),
        "soa_email": Property(mutable=True),
        "retry_sec": Property(mutable=True),
        "master_ips": Property(mutable=True, filterable=True),
        "axfr_ips": Property(mutable=True),
        "expire_sec": Property(mutable=True),
        "refresh_sec": Property(mutable=True),
        "ttl_sec": Property(mutable=True),
        "records": Property(derived_class=DomainRecord),
        "type": Property(mutable=True),
        "tags": Property(mutable=True),
    }

    def record_create(self, record_type, **kwargs):
        params = {
            "type": record_type,
        }
        params.update(kwargs)

        result = self._client.post(
            "{}/records".format(Domain.api_endpoint), model=self, data=params
        )
        self.invalidate()

        if not "id" in result:
            raise UnexpectedResponseError(
                "Unexpected response creating domain record!", json=result
            )

        zr = DomainRecord(self._client, result["id"], self.id, result)
        return zr

    def zone_file_view(self):
        result = self._client.get(
            "{}/zone-file".format(self.api_endpoint), model=self
        )

        return result["zone_file"]

    def domain_clone(self, domain: str):
        params = {"domain": domain}

        self._client.post(
            "{}/clone".format(self.api_endpoint), model=self, data=params
        )

    def domain_import(self, domain, remote_nameserver):
        params = {
            "domain": domain.domain if isinstance(domain, Domain) else domain,
            "remote_nameserver": remote_nameserver,
        }

        self._client.post("/domains/import", model=self, data=params)
