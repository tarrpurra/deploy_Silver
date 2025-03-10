import yfinance as yf
import pandas as pd
import json
import os
import logging
from datetime import datetime, timedelta
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

import yfinance as yf
import pandas as pd
import json
import os
import logging
from datetime import datetime, timedelta
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Load environment variables from .env file
load_dotenv()

# Load Google credentials from environment variable
google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def authenticate_google_sheets(sheet_id):
    """
    Authenticate with Google Sheets using credentials from environment variables.
    """
    try:
        # Write the credentials to a temporary file
        with open("temp_credentials.json", "w") as f:
            json.dump(google_creds, f)

        # Authenticate with Google Sheets
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("temp_credentials.json", scopes=scope)
        client = gspread.authorize(creds)

        # Access Sheet2 instead of Sheet1
        sheet = client.open_by_key(sheet_id).worksheet("Sheet2")
        return sheet
    except Exception as e:
        logging.error(f"Failed to authenticate with Google Sheets: {e}")
        raise



def fetch_silver_data():
    today = datetime.now()
    sixty_days_ago = today - timedelta(days=60)

    logging.info(f"Fetching data from {sixty_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}...")

    ticker_symbol = "SI=F"  # Silver futures on Yahoo Finance
    data = yf.Ticker(ticker_symbol)

    # Try fetching 15m data first
    silver = data.history(start=sixty_days_ago, end=today, interval="15m")

    if silver.empty:
        logging.warning("15-minute data is empty. Switching to 1-day interval.")
        silver = data.history(start=sixty_days_ago, end=today, interval="1d")

    if silver.empty:
        logging.error(f"No data found for {ticker_symbol}. It may be delisted or unavailable.")
        return None  # Stop execution if no data is available

    # Drop unnecessary columns safely
    silver.drop(columns=["Dividends", "Stock Splits"], inplace=True, errors="ignore")

    # Reset index for proper formatting
    silver.reset_index(inplace=True)

    logging.info(f"Fetched {len(silver)} rows of data using interval: {'15m' if 'Datetime' in silver else '1d'}")

    return silver  # Return as a DataFrame for further processing

# Example usage

def load_existing_data(worksheet):
    """
    Loads existing data from Google Sheets into a Pandas DataFrame.
    """
    data = pd.DataFrame(worksheet.get_all_records())

    if data.empty:
        logging.info("Google Sheet is empty.")
        return data

    data["Datetime"] = pd.to_datetime(data["Datetime"], errors="coerce")

    # Convert existing Datetime to New York timezone
    if data["Datetime"].dt.tz is None:
        data["Datetime"] = data["Datetime"].dt.tz_localize("America/New_York")
    else:
        data["Datetime"] = data["Datetime"].dt.tz_convert("America/New_York")

    return data

def append_new_data(worksheet, new_data):
    """
    Appends new data to the Google Sheet and deletes the first 60 rows after appending.
    """
    existing = load_existing_data(worksheet)

    if "Datetime" not in new_data.columns:
        logging.error("New data is missing 'Datetime' column!")
        return

    new_data["Datetime"] = pd.to_datetime(new_data["Datetime"], errors="coerce")

    if existing.empty:
        logging.info("Sheet is empty. Writing full dataset with headers...")
        worksheet.update([new_data.columns.tolist()] + new_data.astype(str).values.tolist())
        logging.info(f"Stored {len(new_data)} rows in the empty sheet.")
        return

    if "Datetime" not in existing.columns:
        logging.error("Existing data is missing 'Datetime' column!")
        return

    existing["Datetime"] = pd.to_datetime(existing["Datetime"], errors="coerce")
    last_date = existing["Datetime"].max()

    if pd.isna(last_date):
        logging.error("Last date in existing data is NaN. Cannot compare new data.")
        return

    # Ensure timezone consistency
    last_date = last_date.tz_localize(None)
    new_data["Datetime"] = new_data["Datetime"].dt.tz_localize(None)

    # Filter out duplicate entries
    new_data = new_data[new_data["Datetime"] > last_date]

    if new_data.empty:
        logging.info("No new data to append.")
        return

    # **STEP 1: Append new data**
    worksheet.append_rows(new_data.astype(str).values.tolist())
    logging.info(f"Appended {len(new_data)} new rows to the sheet.")

    # **STEP 2: Delete the first 60 rows if total rows exceed threshold**
    total_rows = len(existing) + len(new_data)  # New total rows
    rows_to_delete = 60

    if total_rows > rows_to_delete + 1:  # +1 to keep the header
        logging.info(f"Deleting the first {rows_to_delete} rows to maintain size.")
        worksheet.delete_rows(2, rows_to_delete + 1)  # Keep header intact
        logging.info("Old rows deleted successfully.")
