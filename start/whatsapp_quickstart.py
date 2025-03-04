import json
import os
import requests
from dotenv import load_dotenv
\
# Load environment variables
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENTS_WAID = [os.getenv("RECIPIENT_WAID1"), os.getenv("RECIPIENT_WAID")]
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
FLASK_API_URL = "http://127.0.0.1:8000/get-data"  # Update if hosted

# Store user trade status (Replace with DB in production)
user_purchases = {}  # Example: {"919876543210": {"bought": True, "price": 75000}
# Should print the number

# --------------------------------------------------------------
# Fetch processed data from Flask API
# --------------------------------------------------------------
def fetch_processed_data():
    try:
        response = requests.get(FLASK_API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error fetching data: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

# --------------------------------------------------------------
# Prepare WhatsApp message data
# --------------------------------------------------------------
def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

# --------------------------------------------------------------
# Send WhatsApp message
# --------------------------------------------------------------
def send_message(data):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }
    response = requests.post(url, data=data, headers=headers)

    if response.status_code == 200:
        print("✅ Message sent!")
    else:
        print(f"❌ Error: {response.status_code}, {response.text}")

# --------------------------------------------------------------
# Format WhatsApp messages (Introduction + Market Signals)
# --------------------------------------------------------------
def format_intro_message():
    return """
📢 *Stock Trading Signals* 📢

✅ When a *buy signal* appears, you can choose to buy the stock.  
To confirm your purchase, send:  
🚩 *Bought at <price>* (Example: "🚩 Bought at 2500")  

✅ When a *sell signal* appears, you should sell if you've already bought.  
To confirm your sale, send:  
💰 *Sold at <price>* (Example: "Sold at 2550")  
"""

def format_signal_message(data, wa_id):
    price_change = data.get("price_change_pct", "N/A")
    price_change = f"{price_change:.2f}%" if isinstance(price_change, (int, float)) else str(price_change)

    market_message = f"""
📊 *Market Update* 📊

📉 *Trend:* {data.get("trend", "N/A")}
💹 *Current Price:* {data.get("current_price", "N/A")}
📈 *Price Change (%):* {price_change}

🔻 *Nearest Support:* {data.get("nearest_support", "N/A")}
🔺 *Nearest Resistance:* {data.get("nearest_resistance", "N/A")}

📊 *Indicators:*  
📌 *MACD Line:* {data.get("macd_line", "N/A")}  
📌 *MACD Signal:* {data.get("macd_signal", "N/A")}  
📌 *5 EMA:* {data.get("5_EMA", "N/A")}  

📢 *Signals:*  
✅ *Buy:* {data.get("buy_signal", "N/A")}  
❌ *Sell:* {data.get("sell_signal", "N/A")}  
📉 *Short:* {data.get("short_signal", "N/A")}  
🚪 *Exit:* {data.get("exit_signal", "N/A")}
"""

    has_bought = wa_id in user_purchases
    trade_signal = "\n🟢 *Buy Signal Available!* You may want to buy now!" if not has_bought else "\n🔴 *Sell Signal Available!* Consider selling if you haven't already."

    return market_message + trade_signal

# --------------------------------------------------------------
# Main Execution: Fetch Data, Format & Send Messages
# --------------------------------------------------------------
def main_function():
    processed_data = fetch_processed_data()
    
    if processed_data:
        for recipient in RECIPIENTS_WAID:
            print(f"📲 Sending message to: {recipient}")
    
            # Send introduction message
            intro_message = format_intro_message()
            intro_data = get_text_message_input(recipient, intro_message)
            send_message(intro_data)
            print("✅ Intro message sent to", recipient)

            # Send actual signal message
            signal_message = format_signal_message(processed_data, recipient)
            signal_data = get_text_message_input(recipient, signal_message)
            send_message(signal_data)
            print("✅ Signal message sent to", recipient)


# Ensure the script runs only when executed directly
if __name__ == "__main__":
    main_function()
