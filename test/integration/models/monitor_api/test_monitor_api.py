def test_monitor_api_fetch_dbaas_metrics(test_monitor_client):
    client, entity_ids = test_monitor_client

    metrics = client.metrics.fetch_metrics(
        "dbaas",
        entity_ids=entity_ids,
        metrics=[{"name": "read_iops", "aggregate_function": "avg"}],
        relative_time_duration={"unit": "hr", "value": 1},
    )

    assert metrics.status == "success"
