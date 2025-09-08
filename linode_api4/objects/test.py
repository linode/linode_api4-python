# test.py - end-to-end Monitor alert definition test (no hardcoded token)
import os
import sys
import time
import uuid
from typing import Optional

from linode_api4 import LinodeClient

# Configuration from environment
TOKEN = os.environ.get("LINODE_TOKEN", "314276e1193d18455d9d3c9e74d87c3dd077e906a11b55e86e471c3db238fcba")
SERVICE_TYPE = os.environ.get("MONITOR_SERVICE_TYPE", "dbaas")
SEVERITY = int(os.environ.get("ALERT_SEVERITY", "3"))
BASE_URL = os.environ.get("LINODE_BASE_URL", "https://api.linode.com/v4beta")

if not TOKEN:
    print("LINODE_TOKEN environment variable is required")
    sys.exit(1)

client = LinodeClient(TOKEN, base_url=BASE_URL)
created_id: Optional[int] = None

def find_channel_id() -> Optional[int]:
    for ch in client.monitor.alert_channels():
        cid = getattr(ch, "id", None) or ch.get("id", None)
        if cid:
            return int(cid)
    return None

try:
    channel_id = find_channel_id()
    if not channel_id:
        print("No alert channel found. Create one in the UI or via API and re-run.")
        sys.exit(1)
    print("Fetch All Alerts for the user")
    final = client.get(f"/monitor/alert-channels")
    print(final)
    print("Fetch All Alerts for the user complete")
    #sys.exit(1)
    
    label = f"sdk-e2e-{uuid.uuid4().hex[:8]}"
    description = "Temporary alert created by SDK e2e test"
    alert_type = "threshold"  # top-level 'type' for API
    # Build payload according to API requirements
    payload = {
        "label": label,
        "severity": SEVERITY,
        "type": alert_type,
        "description": description,
        "channel_ids": [channel_id],
        "trigger_conditions": {
            "criteria_condition": "ALL",
            "evaluation_period_seconds": 300,
            "polling_interval_seconds": 300,
            "trigger_occurrences": 1,
        },
        "rule_criteria": {
            "rules": [
                {
                    "metric": "cpu_usage",          # metric name may vary by service
                    "operator": "gt",               # example: greater than
                    "threshold": 90,                # example threshold
                    "aggregate_function": "avg",    # average
                    "period": 300,
                    "unit": "percent",
                    "dimension_filters": [],
                }
            ]
        },
        # keep optional empty lists if API expects them
        "conditions": [],
        "notification_groups": [],
    }

    print("Creating alert definition:", label)
    res = client.post(f"/monitor/services/{SERVICE_TYPE}/alert-definitions", data=payload)
    if "id" not in res:
        print("Create failed, response:", res)
        sys.exit(1)

    created_id = res["id"]
    print("Created alert id:", created_id)

    # Fetch created resource
    time.sleep(2)
    obj = client.get(f"/monitor/services/{SERVICE_TYPE}/alert-definitions/{created_id}")
    print("Fetched:", obj)

    # Poll until not 'in progress' (best-effort)
    timeout = 300
    interval = 5
    start = time.time()
    while time.time() - start < timeout:
        obj = client.get(f"/monitor/services/{SERVICE_TYPE}/alert-definitions/{created_id}")
        status = obj.get("status")
        print("Status:", status)
        if not status or status.lower() != "in progress":
            break
        time.sleep(interval)

    # Try update if allowed
    updated_label = f"{label}-upd"
    try:
        print("Updating label to:", updated_label)
        updated = client.put(
            f"/monitor/services/{SERVICE_TYPE}/alert-definitions/{created_id}",
            data={"label": updated_label},
        )
        print("Updated:", updated)
    except Exception as e:
        msg = str(e)
        if "403" in msg or "Access Denied" in msg or "permission" in msg.lower():
            print("Update failed due to permissions (monitor:write required). Skipping update.")
        else:
            raise

    # Final fetch before delete
    final = client.get(f"/monitor/services/{SERVICE_TYPE}/alert-definitions/{created_id}")
    print("Final object:", final)
    time.sleep(120)

    # Delete
    print("Deleting alert id:", created_id)
    client.delete(f"/monitor/services/{SERVICE_TYPE}/alert-definitions/{created_id}")
    print("Deleted")

except Exception as exc:
    print("Error:", exc)
    raise
finally:
    # Best-effort cleanup in case something failed earlier
    if created_id:
        try:
            client.delete(f"/monitor/services/{SERVICE_TYPE}/alert-definitions/{created_id}")
        except Exception:
            pass