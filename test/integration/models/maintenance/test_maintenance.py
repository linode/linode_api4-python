def test_get_maintenance_policies(test_linode_client):
    client = test_linode_client

    policies = client.maintenance.maintenance_policies()

    assert isinstance(policies, list)
    assert all(hasattr(p, "slug") for p in policies)

    slugs = [p.slug for p in policies]
    assert any(
        slug in slugs for slug in ["linode/migrate", "linode/power_off_on"]
    )
