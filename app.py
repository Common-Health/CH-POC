from flask import Flask, request, redirect, jsonify
from dotenv import load_dotenv
from pay_api import encrypt_rsa, PrpCrypt
from helpers.salesforce_access import find_payment_method_of_user, find_user_order, find_user, create_new_user
import os
import json
import requests


app = Flask(__name__)
load_dotenv()
PROJECT_NAME = os.getenv('PROJECT_NAME')
API_KEY = os.getenv('API_KEY')
MERCHANT_NAME = os.getenv('MERCHANT_NAME')
BASE_URL = os.getenv('BASE_URL')

def get_payment_token():
    # Build the full URL
    url = f"{BASE_URL}api/token?projectName={PROJECT_NAME}&apiKey={API_KEY}&merchantName={MERCHANT_NAME}"
    
    # Send GET request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse JSON response
        data = response.json()
        
        # Extract paymentToken
        payment_token = data["response"]["paymentToken"]
        
        if payment_token:
            return payment_token
        else:
            raise ValueError("Payment Token not found in the response.")
    else:
        error_code = response.status_code
        raise ValueError(f"Failed to retrieve data:{error_code}")

def custom_format(data):
    formatted_items = []
    for key, value in data.items():
        if isinstance(value, str):
            formatted_value = f"'{value}'"
        elif isinstance(value, list) or isinstance(value, dict):
            # Convert list or dict to a JSON string and format it
            formatted_value = json.dumps(value)
            if isinstance(value, list):  # Special handling for lists
                formatted_value = f"'{formatted_value}'"
        else:
            formatted_value = value
        formatted_items.append(f"{key}: {formatted_value}")
    return "{" + ",".join(formatted_items) + "}"

def send_post_request(url, auth_token, payload_value):
    # Headers dictionary
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Data dictionary: this will be url-encoded by requests
    data = {
        'payload': payload_value
    }

    # Sending the POST request
    response = requests.post(url, headers=headers, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError('Failed to send POST request:', response.status_code, response.text)

@app.route('/api/initiate_payment', methods=['POST'])
def initiate_payment():
    try:
        token = get_payment_token()
        received_data = request.json
        json_string = custom_format(received_data)

        payload_encrypt = encrypt_rsa(json_string).encrypt()

        result = send_post_request(BASE_URL+"api/pay",token,payload_encrypt)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/check_payment', methods=['POST'])
def check_payment_status():
    try:
        received_data = request.json
        payment_result = received_data["paymentResult"]
        result = PrpCrypt().decrypt(payment_result)
        return result
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/get_payment_method/<user_id>', methods=['POST'])
def get_payment_method(user_id):
    try:
        user_payment_method = find_payment_method_of_user(user_id)
        return user_payment_method
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/get_order/<user_id>/<stage>', methods=['POST'])
def get_order(user_id,stage):
    try:
        order_summary = find_user_order(user_id,stage)
        return order_summary
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/get_user/<user_id>', methods=['POST'])
def get_user(user_id):
    try:
        user_profile = find_user(user_id)
        return user_profile
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_account',methods=['POST'])
def create_account():
    try:
        received_data = request.json
        user_name = received_data['username']
        user_phone = received_data['phone']
        fcm_token = received_data['fcmToken']
        user_country = received_data['country']
        new_user_response = create_new_user(user_name, user_phone, fcm_token,user_country)
        return new_user_response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)