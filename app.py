from flask import Flask, request, redirect, jsonify
from flask_jwt_extended import JWTManager, create_access_token,jwt_required, get_jwt_identity
from dotenv import load_dotenv
from pay_api import encrypt_rsa, PrpCrypt
from helpers.salesforce_access import find_payment_method_of_user, find_user_order, find_user, create_new_user, update_user_fcm, find_user_by_phone, validate_pin, find_user_prescription, update_user, update_opportunity_sf, get_contact_related_data, update_rating_sf, create_payment_method, update_payment_method, check_user_status, handle_existing_customer_new_app_user
import os
import json
from datetime import timedelta
import requests
from flask_cors import CORS


app = Flask(__name__)
load_dotenv()
CORS(app)
app.config['JWT_SECRET_KEY'] = os.getenv('BEARER_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)

jwt = JWTManager(app)
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
        provider_name = received_data["providerName"]
        json_string = custom_format(received_data)

        payload_encrypt = encrypt_rsa(json_string).encrypt()

        result = send_post_request(BASE_URL+"api/pay",token,payload_encrypt)
        if provider_name != "AYA Pay":
            webview_link = os.getenv('DINGER_STAGING_SITE')
            transaction_no = result["response"]["transactionNum"]
            form_token = result["response"]["formToken"]
            merchant_order_id = result["response"]["merchOrderId"]
            result = {
                "link": webview_link + f"formCheckout?transactionNo={transaction_no}&formToken={form_token}&merchantOrderId={merchant_order_id}"
            }
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
@jwt_required()
def get_payment_method(user_id):
    try:
        user_payment_method = find_payment_method_of_user(user_id)
        return user_payment_method
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/create_payment_method/<account_id>', methods=['POST'])
@jwt_required()
def new_payment_method(account_id):
    try:
        data = request.json
        response = create_payment_method(account_id, data)
        return jsonify(response), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/update_payment_method/<payment_id>', methods=['POST'])
@jwt_required()
def update_existing_payment_method(payment_id):
    try:
        data = request.json
        response = update_payment_method(payment_id, data)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/api/get_order/<user_id>/<stage>', methods=['POST'])
@jwt_required()
def get_order(user_id,stage):
    try:
        order_summary = find_user_order(user_id,stage)
        return order_summary
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/get_prescription/<patient_id>/', defaults={'prescription_id': None}, methods=['POST'])
@app.route('/api/get_prescription/<patient_id>/<prescription_id>', methods=['POST'])
@jwt_required()
def get_prescription(patient_id, prescription_id):
    try:
        prescription_summary = find_user_prescription(patient_id, prescription_id)
        return prescription_summary
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/get_contact_data/<contact_id>', methods=['POST'])
@jwt_required()
def contact_data(contact_id):
    result = get_contact_related_data(contact_id)
    return jsonify(result)
    
@app.route('/api/get_user/<user_id>', methods=['POST'])
@jwt_required()
def get_user(user_id):
    try:
        user_profile = find_user(user_id)
        return user_profile
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/check_user', methods=['POST'])
@jwt_required()
def find_user_login():
    try:
        received_data = request.json
        phone = received_data['phone']
        response = check_user_status(phone)

        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_pin/<user_id>', methods=['POST'])
@jwt_required()
def create_pin_for_old_customers(user_id):
    try:
        received_data = request.json
        fcm_token = received_data['fcmToken']
        user_pin = received_data['PIN']
        firebase_uid = received_data['firebaseUid']
        shopify_status = received_data['shopifyStatus']

        response = handle_existing_customer_new_app_user(user_id, fcm_token, user_pin, firebase_uid, shopify_status)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_account',methods=['POST'])
@jwt_required()
def create_account():
    try:
        current_user = get_jwt_identity()
        if current_user != "CommonHealth":
            return jsonify({"msg": "Unauthorized user"}), 403
        else:
            received_data = request.json
            user_name = received_data['username']
            user_phone = received_data['phone']
            fcm_token = received_data['fcmToken']
            user_country = received_data['country']
            user_pin = received_data['PIN']
            firebase_uid = received_data['firebaseUid']
            shopify_status = received_data['shopifyStatus']
            new_user_response = create_new_user(user_name, user_phone, fcm_token,user_country,user_pin, firebase_uid, shopify_status)
            return new_user_response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/update_account/<user_id>/fcmToken',methods=['POST'])
@jwt_required()
def update_account_fcm(user_id):
    try:
        received_data = request.json
        fcm_token = received_data['fcmToken']
        update_fcm_response = update_user_fcm(fcm_token, user_id)
        return update_fcm_response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/update_rating/<opportunity_id>',methods=['POST'])
@jwt_required()
def update_rating(opportunity_id):
    try:
        received_data = request.json
        rating = received_data["deliveryRating"]
        update_rating_response = update_rating_sf(opportunity_id, rating)
        return update_rating_response
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/update_account/<user_id>',methods=['POST'])
@jwt_required()
def update_account(user_id):
    try:
        data = request.json

        update_data = {}
        update_data['Name'] = data.get('name')
        update_data['CH_Email__c'] = data.get('email')
        update_data['ShippingStreet'] = data.get('shippingStreet')
        if 'geolocation' in data and data['geolocation']:
            try:
                lat, lng = data['geolocation'].split(',')
                update_data['Geolocation__Latitude__s'] = float(lat)
                update_data['Geolocation__Longitude__s'] = float(lng)
            except ValueError:
                return {'error': 'Invalid geolocation format. Please use "lat,lng".'}
        update_data['Display_Photo_URL__c'] = data.get('photo_url')

        update_user_response = update_user(update_data,user_id)
        return update_user_response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/update_opportunity/<opportunity_id>", methods=["POST"])
def update_opportunity(opportunity_id):
    try:
        received_data = request.json
        new_stage = received_data.get('newStage')
        
        # Validate inputs
        if not new_stage:
            return jsonify({'error': 'Missing required parameters: opp_id or new_stage'}), 400
        else:
            update_opportunity_response = update_opportunity_sf(new_stage,opportunity_id)
            return update_opportunity_response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/login/<login_type>", methods=["POST"])
def login(login_type):
    try:
        if login_type == "basic":
            username = request.json.get("username", None)
            password = request.json.get("password", None)
            if username != os.getenv('ADMIN_USERNAME') or password != os.getenv('ADMIN_PASSWORD'):
                return jsonify({"msg": "Bad username or password"}), 401

            access_token = create_access_token(identity=username)
            return jsonify({"access_token":access_token})
        elif login_type == "phoneAuth":
            phone = request.json.get("phone", None)
            response = find_user_by_phone(phone)
            access_token = create_access_token(identity=response["name"])
            return jsonify({"access_token":access_token,"accountId":response['accountId']})
        elif login_type == "PIN":
            phone = request.json.get("phone", None)
            pin = request.json.get("PIN", None)
            response = validate_pin(phone, pin)
            access_token = create_access_token(identity=response["name"])
            return jsonify({"access_token":access_token,"accountId":response['accountId']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)