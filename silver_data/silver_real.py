import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Define scope
scope = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate and initialize the client
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# Open the Google Sheet by ID
sheet_id = "1ijoaNSyspC__vPRo7c2bdr5R5lVLNh-27w_BEnarN_Q"
spreadsheet = client.open_by_key(sheet_id)

# Select the worksheet (first sheet or specify by name)
worksheet = spreadsheet.sheet1  # or spreadsheet.worksheet("Sheet Name")

# Read the new data from CSV
today = datetime.today()
sixty_days_ago = today - timedelta(days=60)


ticker_symbol = "SI=F"  # Corrected ticker for Silver Futures
data = yf.Ticker(ticker_symbol)
silver = data.history(start=sixty_days_ago, end=today, interval="15m")

# Fill NaN values to avoid issues
silver.fillna("", inplace=True)

silver_data = silver.values.tolist()

# Add the header (column names) to the data
header = silver.columns.tolist()
silver_data_with_header = [header] + silver_data


# Append new rows to the existing Google Sheet
worksheet.append_rows(silver_data_with_header, value_input_option="RAW")

print("New data successfully appended to Google Sheets.")