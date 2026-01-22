import os
import json
import csv
import requests
import base64
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from readSubscriptionIDs import read_subscription_ids

SUBSCRIPTIONS_CSV_FILE = "subscriptions.csv"
SUBSCRIPTION_ID_COL_HEADER = "subscription_id"

# Load environment variables from .env file
load_dotenv()

# get API credentials from env variables
if not os.getenv("CB_SITE_NAME"):
    raise ValueError("CB_SITE_NAME is not set in the environment variables")
if not os.getenv("API_KEY"):
    raise ValueError("API_KEY is not set in the environment variables")
BASE_URL = "https://" + os.getenv("CB_SITE_NAME") + ".chargebee.com/api/v2/"
API_KEY = os.getenv("API_KEY")

# Encode API Key in Base64
AUTH_HEADER = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {AUTH_HEADER}"
}


def get_scheduled_changes(subscription_id):
    url = BASE_URL + "subscriptions/" + subscription_id + "/retrieve_with_scheduled_changes"
    get_scheduled_changes_response = requests.get(url, auth=HTTPBasicAuth(API_KEY, ""))
    get_scheduled_changes_response.raise_for_status()
    scheduled_changes_data = get_scheduled_changes_response.json()
    print(f"scheduled changes for subscription ID {subscription_id}:")
    print(json.dumps(scheduled_changes_data, indent=2))
    return scheduled_changes_data

def has_scheduled_changes(scheduled):
    """Check if scheduled changes contain subscription_items"""
    subscription = scheduled.get("subscription", {})
    subscription_items = subscription.get("subscription_items", [])
    return len(subscription_items) > 0

def apply_changes(scheduled, subscription_id):
    try:
        # extract subscription_items from scheduled changes (only care about subscription_items)
        subscription = scheduled.get("subscription", {})
        subscription_items = subscription.get("subscription_items", [])

        if not subscription_items:
            print(f"No subscription_items found in scheduled changes for subscription {subscription_id}")
            return None

        # transform to update_for_items payload in Chargebee's form-encoded format
        payload = {
            "prorate": False,
            "invoice_immediately": False
        }

        # Build subscription_items in format: subscription_items[field][index] = value
        for index, item in enumerate(subscription_items):
            payload[f"subscription_items[item_price_id][{index}]"] = item["item_price_id"]
            
            # Only include quantity and unit_price if present
            if "quantity" in item:
                payload[f"subscription_items[quantity][{index}]"] = item["quantity"]
            if "unit_price" in item:
                payload[f"subscription_items[unit_price][{index}]"] = item["unit_price"]

        print("")
        print(f"payload for subscription ID {subscription_id}:")
        print(json.dumps(payload, indent=2))
        print("")

        url = BASE_URL + "subscriptions/" + subscription_id + "/update_for_items"
        apply_changes_response = requests.post(url, data=payload, auth=HTTPBasicAuth(API_KEY, ""))
        apply_changes_response.raise_for_status()
        apply_changes_data = apply_changes_response.json()
        print("")
        print(f"apply changes response for subscription ID {subscription_id}:")
        print(json.dumps(apply_changes_data, indent=2))
        return apply_changes_data
    except Exception as e:
        print(f"Error applying changes for subscription {subscription_id}: {str(e)}")
        raise


def main():
    # Read CSV file and process each row
    rows = []
    fieldnames = None
    
    # First, read all rows from CSV
    with open(SUBSCRIPTIONS_CSV_FILE, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames.copy() if reader.fieldnames else []
        
        # Strip BOM and whitespace from fieldnames
        fieldnames = [name.strip('\ufeff').strip() if name else name for name in fieldnames]
        
        # Add columns if they don't exist
        if "has_scheduled_changes_data" not in fieldnames:
            fieldnames.append("has_scheduled_changes_data")
        if "success" not in fieldnames:
            fieldnames.append("success")
        
        for row in reader:
            # Create a normalized row with cleaned column names
            normalized_row = {}
            for key, value in row.items():
                normalized_key = key.strip('\ufeff').strip()
                normalized_row[normalized_key] = value
            
            # Skip empty rows
            if not normalized_row or not normalized_row.get(SUBSCRIPTION_ID_COL_HEADER):
                continue
            rows.append(normalized_row)
    
    # Process each row and track success
    for row in rows:
        subscription_id = row.get(SUBSCRIPTION_ID_COL_HEADER)
        if not subscription_id:
            print(f"Skipping row with missing subscription_id: {row}")
            continue
        print(f"Processing subscription ID: {subscription_id}")
        
        scheduled_changes_data = None
        try:
            scheduled_changes_data = get_scheduled_changes(subscription_id)
            has_changes = has_scheduled_changes(scheduled_changes_data)
            
            # Set has_scheduled_changes_data column
            row["has_scheduled_changes_data"] = "1" if has_changes else "0"
            
            if has_changes:
                # Attempt to apply changes
                result = apply_changes(scheduled_changes_data, subscription_id)
                
                # Mark as successful if apply_changes returned a result
                if result is not None:
                    row["success"] = "1"
                    print(f"✓ Successfully applied changes for subscription {subscription_id}")
                else:
                    row["success"] = "0"
                    print(f"✗ Failed to apply changes for subscription {subscription_id}")
            else:
                # No scheduled changes found, skip applying and set success to 0
                row["success"] = "0"
                print(f"✗ No scheduled changes found for subscription {subscription_id}")
                
        except Exception as e:
            # Set has_scheduled_changes_data based on whether we successfully retrieved data
            if scheduled_changes_data is not None:
                try:
                    has_changes = has_scheduled_changes(scheduled_changes_data)
                    row["has_scheduled_changes_data"] = "1" if has_changes else "0"
                except:
                    row["has_scheduled_changes_data"] = "0"
            else:
                # Failed to retrieve scheduled changes data
                row["has_scheduled_changes_data"] = "0"
            row["success"] = "0"
            print(f"✗ Failed to process subscription {subscription_id}: {str(e)}")
        
        print("")
    
    # Write results back to CSV
    with open(SUBSCRIPTIONS_CSV_FILE, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Results written to {SUBSCRIPTIONS_CSV_FILE}")

if __name__ == "__main__":
    main()