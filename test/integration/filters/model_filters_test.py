from test.integration.filters.fixtures import (  # noqa: F401
    domain_instance,
    lke_cluster_instance,
)

from linode_api4.objects import (
    DatabaseEngine,
    DatabaseType,
    Domain,
    Firewall,
    Image,
    LKECluster,
    Type,
)


def test_database_type_model_filter(test_linode_client):
    client = test_linode_client

    db_disk = client.database.types()[0].disk

    filtered_db_type = client.database.types(DatabaseType.disk == db_disk)

    assert db_disk == filtered_db_type[0].disk


def test_database_engine_model_filter(test_linode_client):
    client = test_linode_client

    engine = "mysql"

    filtered_db_engine = client.database.engines(
        DatabaseEngine.engine == engine
    )

    assert len(client.database.engines()) > len(filtered_db_engine)


def test_domain_model_filter(test_linode_client, domain_instance):
    client = test_linode_client

    filtered_domain = client.domains(Domain.domain == domain_instance.domain)

    assert domain_instance.id == filtered_domain[0].id


def test_image_model_filter(test_linode_client):
    client = test_linode_client

    filtered_images = client.images(Image.label.contains("Debian"))

    assert len(client.images()) > len(filtered_images)


def test_linode_type_model_filter(test_linode_client):
    client = test_linode_client

    filtered_types = client.linode.types(Type.label.contains("Linode"))

    assert len(filtered_types) > 0
    assert "Linode" in filtered_types[0].label


def test_lke_cluster_model_filter(test_linode_client, lke_cluster_instance):
    client = test_linode_client

    filtered_cluster = client.lke.clusters(
        LKECluster.label.contains(lke_cluster_instance.label)
    )

    assert filtered_cluster[0].id == lke_cluster_instance.id


def test_networking_firewall_model_filter(
    test_linode_client, e2e_test_firewall
):
    client = test_linode_client

    filtered_firewall = client.networking.firewalls(
        Firewall.label.contains(e2e_test_firewall.label)
    )

    assert len(filtered_firewall) > 0
    assert e2e_test_firewall.label in filtered_firewall[0].label
