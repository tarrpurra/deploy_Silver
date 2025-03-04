import logging
from flask import current_app, jsonify
import json
import requests

# from app.services.openai_service import generate_response
import re


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


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


def generate_response(response):
    # Return text in uppercase
    return response.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


user_purchases = {}  # Example: {"919876543210": {"bought": True, "buy_price": 25.50}}

def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"].strip().lower()

    has_bought = wa_id in user_purchases  # Check if user has an active trade

    if "🚩" in message_body:  # User confirms they have bought
        try:
            buy_price = float(message_body.split()[-1])  # Extract price
            user_purchases[wa_id] = {"bought": True, "buy_price": buy_price}

            response = f"✅ Trade recorded at {buy_price}. Waiting for sell signal."
        except ValueError:
            response = "❌ Invalid format. Use: 🚩 Bought at <price>"

    elif message_body == "sell":
        if has_bought:
            buy_price = user_purchases[wa_id]["buy_price"]
            response = f"✅ Sell signal received. Please confirm sale by sending 'sold at <price>'."
        else:
            response = "🚫 You haven't bought silver yet. No sell signal available."

    elif "sold at" in message_body:
        if has_bought:
            try:
                sell_price = float(message_body.split()[-1])  # Extract price
                buy_price = user_purchases[wa_id]["buy_price"]

                # Calculate profit or loss
                profit_loss = round(sell_price - buy_price, 2)
                status = "Profit" if profit_loss > 0 else "Loss" if profit_loss < 0 else "Break-even"

                response = f"💰 Trade closed. Bought at {buy_price}, sold at {sell_price}. {status}: {profit_loss}"
                
                # Remove user record from memory
                del user_purchases[wa_id]

            except ValueError:
                response = "❌ Invalid format. Use: sold at <price>"
        else:
            response = "🚫 You haven't bought silver yet. No record found."

    else:
        response = "Send '🚩 Bought at <price>' to confirm purchase, 'sell' to initiate, or 'sold at <price>' to close the trade."

    data = get_text_message_input(wa_id, response)
    send_message(data)



# def process_whatsapp_message(body):
#     wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
#     name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

#     message = body["entry"][0]["changes"][0]["value"]["messages"][0]
#     message_body = message["text"]["body"]

#     # TODO: implement custom function here
#     response = generate_response(message_body)

#     # OpenAI Integration
#     # response = generate_response(message_body, wa_id, name)
#     # response = process_text_for_whatsapp(response)

#     data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
#     send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
