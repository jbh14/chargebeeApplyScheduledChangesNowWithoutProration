import os
import json
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

def apply_changes(scheduled, subscription_id):
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


def main():

    # testing - single subscription ID
    subscription_id = "006R300000BhnaDIAR"
    subscription_ids = [subscription_id]

    # Load customer IDs from CSV
    #subscription_ids = read_subscription_ids(SUBSCRIPTIONS_CSV_FILE, SUBSCRIPTION_ID_COL_HEADER) # 1st parameter is the CSV filename, 2nd parameter is the column header for subscription IDs

    for subscription_id in subscription_ids:
        scheduled_changes_data = get_scheduled_changes(subscription_id)
        apply_changes(scheduled_changes_data, subscription_id)  

if __name__ == "__main__":
    main()