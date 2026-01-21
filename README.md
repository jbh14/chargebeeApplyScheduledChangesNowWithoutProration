# apply scheduled changes now without prorating
Created this simple script for retrieving then applying scheduled changes immediately for a list of Chargebee subscriptions, which can't be done via bulk export/import or from SFDC managed package (no credentials/site provided here, use .env for those).  This could be easily updated/extended to make other updates/address other shortcomings of Chargebee's built-in functionality. 
__Be sure you know what you're doing if using this, since it can delete data in your Chargebee site (production or test)!__

## Available Scripts
1. Running this locally, make the CB site name and API key available to the script by listing inside an `.env` file in your project directory as such:
```
CB_SITE_NAME = "<chargebee_site_name>"
API_KEY = "<api_key_created_from_within_Chargebee>" 
```
2. Create a CSV file with the IDs of the subscriptions you'd like to get and apply scheduled changes for in your project directory.  Name that CSV "subscriptions.csv" and name the column header "subscription_id" (or modify `clearCBcustomerEmails.py` to match the file/column header names you're using).
3. Create and activate a virtual environment:
```
python3 -m venv .venv       # Mac/Linux
python -m venv .venv        # Windows

source .venv/bin/activate   # Mac/Linux
.\venv\Scripts\activate     # Windows
```
4. Install required dependencies:
```
pip install -r requirements.txt
```
5. Run the script:
```
python3 getAndApplyScheduledChanges.py
```