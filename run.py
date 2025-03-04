import logging
import numpy as np  # Import numpy for conversion
from threading import Thread
from flask import Flask, jsonify
from app import create_app
from silver_data import fetch_silver_data, append_new_data, authenticate_google_sheets
from silver_data import calculate_indicators
from silver_data import identify_trend_signals
from start import main_function  # WhatsApp bot function
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Google Sheets credentials and sheet ID
CREDENTIALS_FILE = "credentials.json"
SHEET_ID = "1ijoaNSyspC__vPRo7c2bdr5R5lVLNh-27w_BEnarN_Q"

# Create Flask app
app = create_app()

# Store the latest processed data globally
latest_data = {"trend": "Processing not started yet."}

# Flag to control the loop
processing_active = True  # Allows stopping if needed in the future

def processing_data():
    """Fetches and processes silver market data before starting WhatsApp messages."""
    global latest_data
    with app.app_context():
        try:
            logging.info("Authenticating Google Sheets...")
            worksheet = authenticate_google_sheets(CREDENTIALS_FILE, SHEET_ID)
            
            logging.info("Fetching new silver data from yfinance...")
            new_data = fetch_silver_data()
            if new_data is None or new_data.empty:
                logging.error("Failed to fetch new data from yfinance.")
                latest_data = {"error": "Failed to fetch new data from yfinance"}
                return  # Stop if fetching fails
            
            logging.info("Calculating indicators...")
            new_data = calculate_indicators(new_data)
            if new_data is None:
                logging.error("Failed to calculate indicators.")
                latest_data = {"error": "Failed to calculate indicators"}
                return  # Stop if calculation fails

            logging.info("Checking Trend...")
            market_trend = identify_trend_signals(new_data)
            # Convert numpy types to Python types for JSON compatibility
            latest_data = {
                key: (int(value) if isinstance(value, np.integer) else
                      float(value) if isinstance(value, np.floating) else
                      value)
                for key, value in market_trend.items()
            }

            logging.info("Appending new data to Google Sheets...")
            success = append_new_data(worksheet, new_data)
            if not success:
                logging.error("Failed to append new data to Google Sheets.")
                latest_data["error"] = "Failed to append new data to Google Sheets"
            else:
                logging.info("Successfully appended data to Google Sheets.")

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            latest_data = {"error": str(e)}


def whatsapp_bot():
    """Starts WhatsApp bot after processing data."""
    logging.info("Starting WhatsApp bot after processing data...")
    while processing_active:
        try:
            logging.info("Sending WhatsApp message...")
            main_function()  # Call WhatsApp bot function
        except Exception as e:
            logging.error(f"Error in WhatsApp bot: {e}")

        time.sleep(600)  # Wait 10 minutes before sending the next message

# Flask routes
@app.route("/")
def home():
    return "Flask app is running!"

@app.route("/get-data", methods=["GET"])
def get_processed_data():
    return jsonify(latest_data)

@app.route("/process-data", methods=["GET"])
def trigger_processing():
    return jsonify({"message": "Data processing is running."})

if __name__ == "__main__":
    logging.info("Starting Flask app...")

    # Run processing first, then WhatsApp bot
    processing_thread = Thread(target=processing_data)
    processing_thread.start()
    processing_thread.join()  # Wait until processing is done

    # Start WhatsApp bot after data is processed
    whatsapp_thread = Thread(target=whatsapp_bot, daemon=True)
    whatsapp_thread.start()

    app.run(host="0.0.0.0", port=8000, debug=True)
