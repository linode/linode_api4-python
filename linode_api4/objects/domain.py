from linode_api4.errors import UnexpectedResponseError
from linode_api4.objects import Base, DerivedBase, Property


class DomainRecord(DerivedBase):
    """
    A single record on a Domain.

    API Documentation: https://www.linode.com/docs/api/domains/#domain-record-view
    """

    api_endpoint = "/domains/{domain_id}/records/{id}"
    derived_url_path = "records"
    parent_id_name = "domain_id"

    properties = {
        "id": Property(identifier=True),
        "domain_id": Property(identifier=True),
        "type": Property(),
        "name": Property(mutable=True),
        "target": Property(mutable=True),
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
    """
    A single Domain that you have registered in Linode’s DNS Manager.
    Linode is not a registrar, and in order for this Domain record to work
    you must own the domain and point your registrar at Linode’s nameservers.

    API Documentation: https://www.linode.com/docs/api/domains/#domain-view
    """

    api_endpoint = "/domains/{id}"
    properties = {
        "id": Property(identifier=True),
        "domain": Property(mutable=True),
        "group": Property(mutable=True),
        "description": Property(mutable=True),
        "status": Property(mutable=True),
        "soa_email": Property(mutable=True),
        "retry_sec": Property(mutable=True),
        "master_ips": Property(mutable=True),
        "axfr_ips": Property(mutable=True),
        "expire_sec": Property(mutable=True),
        "refresh_sec": Property(mutable=True),
        "ttl_sec": Property(mutable=True),
        "records": Property(derived_class=DomainRecord),
        "type": Property(mutable=True),
        "tags": Property(mutable=True),
    }

    def record_create(self, record_type, **kwargs):
        """
        Adds a new Domain Record to the zonefile this Domain represents.
        Each domain can have up to 12,000 active records.

        API Documentation: https://www.linode.com/docs/api/domains/#domain-record-create

        :param record_type: The type of Record this is in the DNS system. Can be one of:
                            A, AAAA, NS, MX, CNAME, TXT, SRV, PTR, CAA.
        :type: record_type: str

        :param kwargs: Additional optional parameters for creating a domain record. Valid parameters
                       are: name, target, priority, weight, port, service, protocol, ttl_sec. Descriptions
                       of these parameters can be found in the API Documentation above.
        :type: record_type: dict

        :returns: The newly created Domain Record
        :rtype: DomainRecord
        """

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
        """
        Returns the zone file for the last rendered zone for the specified domain.

        API Documentation: https://www.linode.com/docs/api/domains/#domain-zone-file-view

        :returns: The zone file for the last rendered zone for the specified domain in the form
                  of a list of the lines of the zone file.
        :rtype: List[str]
        """

        result = self._client.get(
            "{}/zone-file".format(self.api_endpoint), model=self
        )

        return result["zone_file"]

    def clone(self, domain: str):
        """
        Clones a Domain and all associated DNS records from a Domain that is registered in Linode’s DNS manager.

        API Documentation: https://www.linode.com/docs/api/domains/#domain-clone

        :param domain: The new domain for the clone. Domain labels cannot be longer
                       than 63 characters and must conform to RFC1035. Domains must be
                       unique on Linode’s platform, including across different Linode
                       accounts; there cannot be two Domains representing the same domain.
        :type: domain: str
        """
        params = {"domain": domain}

        result = self._client.post(
            "{}/clone".format(self.api_endpoint), model=self, data=params
        )

        return Domain(self, result["id"], result)

    def domain_import(self, domain, remote_nameserver):
        """
        Imports a domain zone from a remote nameserver. Your nameserver must
        allow zone transfers (AXFR) from the following IPs:
            - 96.126.114.97
            - 96.126.114.98
            - 2600:3c00::5e
            = 2600:3c00::5f

        API Documentation: https://www.linode.com/docs/api/domains/#domain-import

        :param domain: The domain to import.
        :type: domain: str

        :param remote_nameserver: The remote nameserver that allows zone transfers (AXFR).
        :type: remote_nameserver: str
        """

        params = {
            "domain": domain.domain if isinstance(domain, Domain) else domain,
            "remote_nameserver": remote_nameserver,
        }

        self._client.post("/domains/import", model=self, data=params)
