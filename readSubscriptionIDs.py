import csv

# Function to read subscription IDs from CSV 
def read_subscription_ids(csv_filename, subscription_id_col_header="subscription_id") -> list:
    subscription_ids = []
    with open(csv_filename, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)  # Reads CSV into a dictionary format
        for row in reader:
            subscription_ids.append(row[subscription_id_col_header])  # Assumes first column is "subscription_id"
    return subscription_ids