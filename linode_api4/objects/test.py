"""
An example script to test the various uses of the `alert_definitions` method.

This script demonstrates how to:
1. List all alert definitions on an account.
2. List all alert definitions for a specific service type.
3. Retrieve a single, specific alert definition by its ID.
"""

import json
import os
import time
from linode_api4 import LinodeClient

# --- Configuration ---
# Read the API token from the environment to avoid committing secrets in code.
#TOKEN = os.environ.get("LINODE_TOKEN", "")
TOKEN ="9c2457b2144b443fe5ea94af57dfe7625a549f281f38c80409970849023c2f29"
def main():
    """
    Main function to execute the test suite.
    """
    if not TOKEN :
        print(
            "Error: Linode API token is not configured or is a placeholder.\n"
            "Please edit the script to include a valid Linode API token."
        )
        return

    # The monitor endpoints are in beta, so the client must use the v4beta URL.
    client = LinodeClient(TOKEN, base_url="https://api.linode.com/v4beta")
    print("Initialized Linode Client for v4beta API.")

    try:
        # --- 1. List all alert definitions ---
        print("\n========================================")
        print("  1. Testing: List ALL alert definitions")
        print("========================================")
        all_alerts = client.monitor.alert_definitions()
        print(f"Found {len(all_alerts)} total alert definitions.")
        for a in all_alerts:
            print(a)

       # print(json.dumps([alert._json for alert in all_alerts], indent=4))

        # --- 2. List alert definitions for a specific service ---
        service_type = "dbaas"
        print(f"\n========================================")
        print(f"  2. Testing: List alerts for service '{service_type}'")
        print("========================================")
        service_alerts = client.monitor.alert_definitions(service_type=service_type)
        print(f"Found {len(service_alerts)} alerts for service '{service_type}'.")
        print(service_alerts)
        #print(json.dumps([alert._json for alert in service_alerts], indent=4))

        # --- 3. Retrieve a single alert definition ---
        print("\n========================================")
        print("  3. Testing: Retrieve a single alert")
        print("========================================")
        if all_alerts:
            first_alert = all_alerts[0]
            alert_id_to_test = first_alert.id
            service_type_to_test = first_alert.service_type

            print(f"Attempting to fetch alert with ID {alert_id_to_test} from service '{service_type_to_test}'...")
            single_alert = client.monitor.alert_definitions(
                service_type=service_type_to_test, alert_id=alert_id_to_test
            )
            print("Successfully retrieved single alert.")
            print(single_alert)
            #print(json.dumps(single_alert._json, indent=4))
        else:
            print("Skipping single alert test: No alerts found on the account.")

        
        # --- 4. Create, update, and delete an alert definition (safe test) ---
        print("\n========================================")
        print("  4. Testing: Create -> Update -> Delete an alert definition")
        print("========================================")

        created_alert = None
        try:
            # Make the label unique to avoid 'label already exists' errors on repeated runs
            # Ensure label begins/ends with a letter/number and is unique per run
            create_label = f"SDK Test Alert"
            # Use integer severity (API expects a numeric severity value)
            create_severity = 1
            create_type = "cpu"
            # Description must begin and end with a letter or number (no trailing
            # punctuation) per API validation rules.
            create_description = "Temporary alert created by SDK test script"

            # Minimal valid payload pieces required by the monitor API:
            # - channel_ids: list of alert channel IDs (1-5 IDs required)
            # - trigger_conditions: an object describing top-level trigger config
            # - rule_criteria: an object with a 'rules' list
            # Try to pick an existing alert channel from the account.
            available_channels = list(client.monitor.alert_channels())
            if not available_channels:
                print("No alert channels found on account — skipping create test.")
                return
            # Use the first available channel id (API requires 1-5 items)
            create_channel_ids = [available_channels[0].id]

            # API expects a single object for trigger_conditions
            create_trigger_conditions = {
                "criteria_condition": "ALL",
                "evaluation_period_seconds": 300,
                # API requires the polling interval to be 300 for this service
                "polling_interval_seconds": 300,
                "trigger_occurrences": 1,
            }

            # API expects rule_criteria to be an object with a 'rules' array
            create_rule_criteria = {
                "rules": [
                    {
                        # Aggregate function as a string (e.g. 'avg', 'max')
                        "aggregate_function": "avg",
                        # The metric field to evaluate
                        "metric": "cpu_usage",
                        "operator": "gt",
                        "threshold": 90,
                        "unit": "percent",
                        "dimension_filters": [],
                    }
                ]
            }

            print("Creating alert definition...")
            # Send the required fields as top-level parameters.
            created_alert = client.monitor.create_alert_definition(
                service_type=service_type,
                label=create_label,
                severity=create_severity,
                type=create_type,
                description=create_description,
                channel_ids=create_channel_ids,
                trigger_conditions=create_trigger_conditions,
                rule_criteria=create_rule_criteria,
                conditions=[],
                notification_groups=[],
            )

            print(f"Created alert with ID: {created_alert.id}")
            print(created_alert)

            # Wait for any server-side creation/update to finish before attempting
            # to update or delete. The API returns status 'in progress' while
            # the definition is being processed.
            wait_seconds = 60
            poll_interval = 60
            start = time.time()
            while getattr(created_alert, "status", None) == "in progress" and (
                time.time() - start < wait_seconds
            ):
                print("Alert is still in progress; waiting...")
                time.sleep(poll_interval)
                try:
                    created_alert = client.monitor.alert_definitions(
                        service_type=service_type, alert_id=created_alert.id
                    )
                except Exception:
                    # transient error while polling; continue until timeout
                    pass

            if getattr(created_alert, "status", None) == "in progress":
                print(
                    "Warning: alert is still in progress after timeout; proceeding anyway."
                )

            # Attempt to update the alert's label. If the token lacks write
            # permissions, the API will return 403 — handle that gracefully.
            # Updated label must also begin and end with a letter/number — use a hyphenated suffix
            updated_label = f"{create_label}-updated"
            print(f"Updating alert {created_alert.id} label to '{updated_label}'...")
            try:
                updated_alert = client.monitor.update_alert_definition(
                    service_type=service_type,
                    alert_id=created_alert.id,
                    label=updated_label,
                )
                print("Updated alert:")
                print(updated_alert)
            except Exception as update_exc:
                msg = str(update_exc)
                if "403" in msg or "Access Denied" in msg:
                    print(
                        "Update failed with 403 Access Denied — token likely lacks monitor:write permissions. Skipping update."
                    )
                else:
                    print(f"Update failed: {update_exc}")
        finally:
            # Ensure we clean up the created alert definition if it exists
            if created_alert and getattr(created_alert, "id", None):
                try:
                    print(f"Deleting alert definition {created_alert.id} (cleanup)...")
                    time.sleep(60)  # brief pause before delete
                    client.monitor.delete_alert_definition(
                        service_type=service_type, alert_id=created_alert.id
                    )
                    print("Cleanup delete completed.")
                except Exception as cleanup_exc:
                    print(f"Failed to delete created alert definition: {cleanup_exc}")


    except Exception as e:
        print(f"\nAn error occurred during testing: {e}")
        print("This may be due to an invalid API token or insufficient permissions.")

    
if __name__ == "__main__":
    main()