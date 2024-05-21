from simple_salesforce import Salesforce, SalesforceResourceNotFound, SalesforceMalformedRequest
from dotenv import load_dotenv
import os
from flask import jsonify

load_dotenv()
username = os.getenv('SF_USERNAME')
password = os.getenv('SF_PASSWORD')
security_token = os.getenv('SF_SECURITY_TOKEN')

sf = Salesforce(username=username, password=password, security_token=security_token, domain='test')

def find_payment_method_of_user(user_id):
    query = f"SELECT Id, Provider_Name__c, Method_Name__c, Customer_Phone_Number__c, Customer_Name__c, Default_Payment_Method__c FROM Payment__c WHERE Account__c = '{user_id}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        user_details_list = []
        for account_details in response['records']:
            user_details = {
                "paymentMethodId": account_details.get('Id'),
                "providerName": account_details.get('Provider_Name__c'),
                "methodName": account_details.get('Method_Name__c'),
                "customerPhone": account_details.get('Customer_Phone_Number__c'),
                "customerName": account_details.get('Customer_Name__c'),
                "defaultPaymentMethod": account_details.get('Default_Payment_Method__c')
            }
            user_details_list.append(user_details)
        return user_details_list
    else:
        return []
    
def find_user(user_id):
    query = f"SELECT Name, Account_ID__c, Phone, CurrencyIsoCode, Alternate_Phone__c, Total_Order_Amount__c, Orders_Placed__c, Country__c, (SELECT Id, AccountId, Name, OtherPhone, Member_ID__c, Age__c, HOH_Relationship__c FROM Contacts), (SELECT Name, Customer__c, Subscription_Start_Date__c, Subscription_End_Date__c, Delivery_Frequency__c FROM Subscriptions__r) FROM Account WHERE ID = '{user_id}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        account_details = response['records'][0]
        
        user_details = {
            "name": account_details.get('Name'),
            "accountIdCH": account_details.get('Account_ID__c'),
            "phoneNumber": account_details.get('Phone'),
            "altPhoneNumber": account_details.get('Alternate_Phone__c'),
            "cumulativeOrders": account_details.get('Orders_Placed__c'),
            "cumulativeAmount": account_details.get('Total_Order_Amount__c'),
            "currency": account_details.get('CurrencyIsoCode'),
            "country": account_details.get('Country__c'),
            "contacts": [],
            "subscriptions":[]
        }
        contacts_data = account_details.get('Contacts', {})
        if contacts_data:
            contacts_data = contacts_data.get('records', [])
            for contact in contacts_data:
                contact_details = {
                    "contactId": contact.get('Id'),
                    "accountId": contact.get('AccountId'),
                    "contactName": contact.get('Name'),
                    "otherPhone": contact.get('OtherPhone'),
                    "memberID": contact.get('Member_ID__c'),
                    "age": contact.get('Age__c'),
                    "relationship":contact.get('HOH_Relationship__c')
                }
                user_details["contacts"].append(contact_details)

        subscriptions_data = account_details.get('Subscriptions__r', {})
        if subscriptions_data:
            subscriptions_data = subscriptions_data.get('records', [])
            for subscription in subscriptions_data:
                subscription_details = {
                    "name": subscription.get('Name'),
                    "customerName": subscription.get('Customer__c'),
                    "startDate": subscription.get('Subscription_Start_Date__c'),
                    "endDate": subscription.get('Subscription_End_Date__c'),
                    "deliveryFrequency":subscription.get('Delivery_Frequency__c')
                }
                user_details["subscriptions"].append(subscription_details)

        return user_details
    else:
        return None

def find_user_order(user_id, stage):
    # Modify the query to conditionally include the StageName filter
    if stage.lower() == "all":
        query = f"SELECT ID, Amount, Delivery_SLA_Date__c, CurrencyIsoCode, Payment_Status__c, Net_Promoter_Score__c, CloseDate, Created_Date__c, Shopify_Order_Number__c, Name, StageName, Payment_Method__r.Customer_Phone_Number__c, Payment_Method__r.CurrencyIsoCode, Payment_Method__r.Customer_Name__c, Payment_Method__r.Method_Name__c, Payment_Method__r.Provider_Name__c, Payment_Method__r.Name, Prescription__r.Name, Prescription__r.Id, Opportunity_Number__c, Patient_Name__r.Name, Subscription__c FROM Opportunity WHERE AccountId = '{user_id}'"
    elif stage.lower() == "pending":
        query = f"SELECT ID, Amount, Delivery_SLA_Date__c, CurrencyIsoCode, Payment_Status__c, Net_Promoter_Score__c, CloseDate, Created_Date__c, Shopify_Order_Number__c, Name, StageName, Payment_Method__r.Customer_Phone_Number__c, Payment_Method__r.CurrencyIsoCode, Payment_Method__r.Customer_Name__c, Payment_Method__r.Method_Name__c, Payment_Method__r.Provider_Name__c, Payment_Method__r.Name, Prescription__r.Name, Prescription__r.Id, Opportunity_Number__c, Patient_Name__r.Name, Subscription__c FROM Opportunity WHERE AccountId = '{user_id}' AND StageName IN ('Qualification', 'Quoted', 'Ordered', 'Picked Up')"
    elif stage.lower() == "past":
        query = f"SELECT ID, Amount, Delivery_SLA_Date__c, CurrencyIsoCode, Payment_Status__c, Net_Promoter_Score__c, CloseDate, Created_Date__c, Shopify_Order_Number__c, Name, StageName, Payment_Method__r.Customer_Phone_Number__c, Payment_Method__r.CurrencyIsoCode, Payment_Method__r.Customer_Name__c, Payment_Method__r.Method_Name__c, Payment_Method__r.Provider_Name__c, Payment_Method__r.Name, Prescription__r.Name, Prescription__r.Id, Opportunity_Number__c, Patient_Name__r.Name, Subscription__c FROM Opportunity WHERE AccountId = '{user_id}' AND StageName IN ('Delivered', 'Delivered-Paid', 'Closed Won')"
    else:
        raise ValueError("Invalid stage provided. Please use 'pending' or 'past'.")

    response = sf.query(query)

    if response['totalSize'] > 0:
        order_summaries = []
        for opportunity_details in response['records']:
            opportunity_id = opportunity_details.get('Id')
            opportunity_number = opportunity_details.get('Opportunity_Number__c')
            opportunity_patient_name = opportunity_details.get('Patient_Name__r')
            payment_method = opportunity_details.get('Payment_Method__r', {})
            prescription = opportunity_details.get('Prescription__r', {})
            opportunity_amount = opportunity_details.get('Amount')
            opportunity_shopify_order_no = opportunity_details.get('Shopify_Order_Number__c')
            opportunity_close_date = opportunity_details.get('CloseDate')
            opportunity_name = opportunity_details.get('Name')
            opportunity_stage = opportunity_details.get('StageName')
            opportunity_created_date = opportunity_details.get('Created_Date__c')
            opportunity_delivery_date = opportunity_details.get('Delivery_SLA_Date__c')
            opportunity_payment_status = opportunity_details.get('Payment_Status__c')
            opportunity_currency = opportunity_details.get('CurrencyIsoCode')
            if stage == 'Pending':
                opportunity_rating = None
            else:
                opportunity_rating = opportunity_details.get('Net_Promoter_Score__c')
            subscription_id = opportunity_details.get('Subscription__c')
            subscription_details = []
            if subscription_id:
                subscription_query = f"SELECT Name, Customer__r.Name, Account__r.Name FROM Subscription__c WHERE Subscription__c.Id = '{subscription_id}'"
                subscriptions_data = sf.query(subscription_query)
                if subscriptions_data['totalSize'] > 0:
                    for subscription in subscriptions_data['records']:
                        customer_name = subscription.get('Customer__r')
                        if customer_name:
                            customer_name = customer_name.get('Name')
                        else:
                            customer_name = None
                        subscription_detail = {
                            "name": subscription.get('Name'),
                            "customerName": customer_name,
                            "accountHolder": subscription.get('Account__r').get('Name')
                        }
                        subscription_details.append(subscription_detail)
            opp_item_query = f"SELECT Product__c, Price__c, Quantity__c, Shopify_Order_Number__c, Date__c FROM Opportunity_Item__c WHERE Opportunity__c = '{opportunity_id}'"
            opp_item_response = sf.query(opp_item_query)
            prescription_details = {}
            payment_method_details = {}

            opportunity_items = []
            if opp_item_response['totalSize'] > 0:
                for item in opp_item_response['records']:
                    opp_item = {
                        "products": item.get('Product__c'),
                        "price": item.get('Price__c'),
                        "quantity": item.get('Quantity__c'),
                        "shopifyOrderNumber": item.get('Shopify_Order_Number__c'),
                        "date": item.get('Date__c')
                    }
                    opportunity_items.append(opp_item)

            if opportunity_patient_name:
                opportunity_patient_name = opportunity_patient_name.get('Name')

            if payment_method:
                payment_method_details = {
                "customerPhoneNumber": payment_method.get('Customer_Phone_Number__c'),
                "currencyIsoCode": payment_method.get('CurrencyIsoCode'),
                "customerName": payment_method.get('Customer_Name__c'),
                "methodName": payment_method.get('Method_Name__c'),
                "providerName": payment_method.get('Provider_Name__c'),
                "name": payment_method.get('Name')
                }
            if prescription:
                prescription_details = {
                "name": prescription.get('Name', 'N/A'),
                "prescriptionId": prescription.get('Id', 'N/A')
                }
            order_summary = {
                "opportunityId":opportunity_id,
                "opportunityName": opportunity_name,
                "opportunityNumber": opportunity_number,
                "patientName": opportunity_patient_name,
                "prescription": prescription_details,
                "paymentMethod": payment_method_details,
                "shopifyOrderNumber": opportunity_shopify_order_no,
                "deliveryDate": opportunity_delivery_date,
                "deliveryRating": opportunity_rating,
                "amount": opportunity_amount,
                "closeDate": opportunity_close_date,
                "createdDate": opportunity_created_date,
                "currentStage": opportunity_stage,
                "paymentStatus": opportunity_payment_status,
                "currency": opportunity_currency,
                "opportunityItems": opportunity_items,  # List of all items
                "subscription":subscription_details
            }
            order_summaries.append(order_summary)

        return order_summaries
    else:
        return {"msg": "No Opportunities found associated with the user"}
    
def find_user_prescription(user_id, prescription_id):
    # Modify the query to conditionally include the StageName filter
    if prescription_id == None:
        query = f"SELECT ID, Account__c, Instructions__c, Patient__c, Age__c, Prescribing_Practitioner__c, Prescribing_Clinic__c, Prescription_Created_Date__c, Name FROM Prescription__c WHERE Account__c = '{user_id}'"
    else:
        query = f"SELECT ID, Account__c, Instructions__c, Patient__c, Age__c, Prescribing_Practitioner__c, Prescribing_Clinic__c, Prescription_Created_Date__c, Name FROM Prescription__c WHERE Account__c = '{user_id}' AND Prescription__c = '{prescription_id}'"

    response = sf.query(query)

    if response['totalSize'] > 0:
        prescription_summaries = []
        for prescription_details in response['records']:
            prescription_id = prescription_details.get('Id')
            prescription_account_holder = prescription_details.get('Account__c')
            prescription_patient_name = prescription_details.get('Patient__c')
            prescription_age = prescription_details.get('Age__c')
            prescription_prescribing_practitioner = prescription_details.get('Prescribing_Practitioner__c')
            prescription_prescribing_clinic = prescription_details.get('Prescribing_Clinic__c')
            prescription_creation_date = prescription_details.get('Prescription_Created_Date__c')
            prescription_name = prescription_details.get('Name')
            prescription_instructions = prescription_details.get('Instructions__c')

            line_items_query = f"SELECT ID, Brand_Name__c, Generic_Name__c, Tablet__c, Prescription__c, Frequency__c, Units_per_Day__c FROM Prescription_Line_Item__c WHERE Prescription__c = '{prescription_id}'"
            line_items_response = sf.query(line_items_query)

            line_items = []
            if line_items_response['totalSize'] > 0:
                for item in line_items_response['records']:
                    opp_item = {
                        "brandName": item.get('Brand_Name__c'),
                        "genericName": item.get('Generic_Name__c'),
                        "tablet": item.get('Tablet__c'),
                        "frequency": item.get('Frequency__c'),
                        "unitsPerDayInsulin": item.get('Units_per_Day__c')
                    }
                    line_items.append(opp_item)

            prescription_summary = {
                "prescriptionId": prescription_id,
                "accountHolder": prescription_account_holder,
                "patientName": prescription_patient_name,
                "age": prescription_age,
                "prescribingPractitioner": prescription_prescribing_practitioner,
                "prescribingClinic": prescription_prescribing_clinic,
                "creationDate": prescription_creation_date,
                "prescriptionNumber": prescription_name,
                "instructions":prescription_instructions,
                "prescriptionLineItems": line_items  # List of all items
            }
            prescription_summaries.append(prescription_summary)

        return prescription_summaries
    else:
        return {"msg": "No Prescriptions found associated with the user"}
    
def get_contact_related_data(contact_id):
    try:
        # Querying only the Name, Id, and Phone of the contact
        contact_data = sf.query(f"SELECT Id, Name, Phone, Age__c FROM Contact WHERE Id = '{contact_id}'")['records'][0]
        contact_info = {
            'id': contact_data['Id'],
            'name': contact_data['Name'],
            'phone': contact_data['Phone'],
            'age':contact_data['Age__c']
        }

        # Querying prescriptions and their line items
        prescription_query = sf.query_all(f"""
            SELECT Id, Name, (SELECT Id, Name, Brand_Name__c, Generic_Name__c, Status__c, Frequency__c FROM Prescription_Line_Items__r)
            FROM Prescription__c
            WHERE Patient__c = '{contact_id}'
        """)['records']

        # Formatting prescriptions to include only specific fields
        prescriptions = [
            {
                'prescriptionId': pres['Id'],
                'prescriptionName': pres['Name'],
                'prescriptionLineItems': [
                    {
                        'id': item['Id'],
                        'name': item['Name'],
                        'brandName': item['Brand_Name__c'],
                        'genericName': item['Generic_Name__c'],
                        'status': item['Status__c'],
                        'frequency': item['Frequency__c']
                    } for item in pres['Prescription_Line_Items__r']['records']
                ] if 'Prescription_Line_Items__r' in pres else []
            } for pres in prescription_query
        ]

        # Querying subscriptions
        subscription_query = sf.query_all(f"""
            SELECT Id, Name, Delivery_Frequency__c
            FROM Subscription__c
            WHERE Customer__c = '{contact_id}'
        """)['records']

        # Formatting subscriptions to include only specified fields
        subscriptions = [
            {
                'subscriptionId': sub['Id'],
                'subscriptionName': sub['Name'],
                'deliveryFrequency': sub['Delivery_Frequency__c']
            } for sub in subscription_query
        ]

        return {
            "contact": contact_info,
            "prescriptions": prescriptions,
            "subscriptions": subscriptions
        }
    except Exception as e:
        return {"error": str(e)}

def create_new_user(user_name, user_phone, fcm_token, user_country, user_pin, firebase_uid):
    
    if user_country == "Philippines":
        currency = 'USD'
    elif user_country == "Myanmar":
        currency = 'MMK'

    new_account = {
        'Name': user_name,
        'Phone': user_phone,
        'RecordTypeId': '0124x000000ZGecAAG',
        'CurrencyIsoCode': currency,
        'Country__c':user_country,
        'FCM_Token__c': fcm_token,
        'PIN_Code__c': user_pin,
        'Firebase_UID__c':firebase_uid
    }
    response = sf.Account.create(new_account)
    new_contact = {
        'LastName': user_name,
        'AccountId': response.get('id'),
        'RecordTypeId': '0124x000000ZGiKAAW',
        'Phone': user_phone,
        'CurrencyIsoCode': currency
    }
    response_contact = sf.Contact.create(new_contact)
    new_user_response = {
        'name':user_name,
        'fcmToken':fcm_token,
        'userId':response.get('id'),
        'firebaseUid':firebase_uid
    }
    return new_user_response

def update_user_fcm(fcm_token, user_id):
    new_account_details = {
        'FCM_Token__c': fcm_token
    }

    response = sf.Account.update(user_id, new_account_details)
    new_user_response = {
        'response': 'Account updated successfully!',
        'fcmToken':fcm_token,
        'userId':user_id
    }
    return new_user_response

def update_user(update_data, user_id):
    try:
        sf.Account.update(user_id, update_data)
        new_user_response = {
            'response': 'Account updated successfully!',
            'userId': user_id
        }
        return new_user_response
    except SalesforceResourceNotFound:
        return jsonify({'error': 'User not found in Salesforce with ID: {}'.format(user_id)}), 404
    except SalesforceMalformedRequest as e:
        return jsonify({'error': 'Invalid data provided; Salesforce could not process the request. Details: {}'.format(e)}),400
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: {}'.format(e)}),500

def update_rating_sf(opportunity_id, rating):
    try:
        sf.Opportunity.update(opportunity_id, {
            'Net_Promoter_Score__c': rating
        })
        new_user_response = {
            'response': 'Rating updated successfully!',
            'opportunityId': opportunity_id
        }
        return new_user_response
    except SalesforceResourceNotFound:
        return jsonify({'error': 'User not found in Salesforce with ID: {}'.format(opportunity_id)}), 404
    except SalesforceMalformedRequest as e:
        return jsonify({'error': 'Invalid data provided; Salesforce could not process the request. Details: {}'.format(e)}),400
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: {}'.format(e)}),500

def update_opportunity_sf(new_stage, opp_id):
    try:
        # Check if the Opportunity exists
        sf.Opportunity.get(opp_id)

        # Update the Opportunity stage
        sf.Opportunity.update(opp_id, {
            'StageName': new_stage
        })
        return {'response': 'Opportunity updated successfully!', 'opportunityId':opp_id}
    except SalesforceResourceNotFound:
        # Opportunity ID is not found
        return jsonify({'error': 'Opportunity not found'}), 404
    except SalesforceMalformedRequest as e:
        # Handling cases such as invalid field values or fields that do not exist
        return jsonify({'error': 'Malformed request: ' + str(e)}), 400
    except Exception as e:
        # Generic error handling for any other unexpected errors
        return jsonify({'error': 'An error occurred: ' + str(e)}), 500

def find_user_by_phone(phone):
    query = f"SELECT Name, Id FROM Account WHERE Phone = '{phone}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        account_details = response['records'][0]
        user_details= {
            "name": account_details.get('Name'),
            "accountId":account_details.get('Id')
        }
        return user_details
    else:
        raise ValueError ("No user found!")

def validate_pin(phone, pin):
    # Query to check if a user exists with the given phone number
    user_query = f"SELECT Name, Id FROM Account WHERE Phone = '{phone}'"
    user_response = sf.query(user_query)

    if user_response['totalSize'] == 0:
        raise ValueError("No user found!")

    # Query to check if the user with the given phone number has the correct PIN
    pin_query = f"SELECT Name, Id FROM Account WHERE Phone = '{phone}' AND PIN_Code__c = {pin}"
    pin_response = sf.query(pin_query)

    if pin_response['totalSize'] > 0:
        account_details = pin_response['records'][0]
        user_details = {
            "name": account_details.get('Name'),
            "accountId": account_details.get('Id')
        }
        return user_details
    else:
        raise ValueError("Wrong PIN!")
    

def create_payment_method(account_id, data):
    try:
        new_payment = {
            'Provider_Name__c': data['providerName'],
            'Method_Name__c': data['methodName'],
            'Customer_Phone_Number__c': data['customerPhone'],
            'Customer_Name__c': data['customerName'],
            'Default_Payment_Method__c': data['defaultPaymentMethod'],
            'CurrencyIsoCode': data['currency'],
            'Account__c': account_id
        }
        response = sf.Payment__c.create(new_payment)
        return response
    except SalesforceMalformedRequest as e:
        raise e

def update_payment_method(payment_id, data):
    try:
        update_payment = {}
        if 'providerName' in data:
            update_payment['Provider_Name__c'] = data['providerName']
        if 'methodName' in data:
            update_payment['Method_Name__c'] = data['methodName']
        if 'customerPhone' in data:
            update_payment['Customer_Phone_Number__c'] = data['customerPhone']
        if 'customerName' in data:
            update_payment['Customer_Name__c'] = data['customerName']
        if 'defaultPaymentMethod' in data:
            update_payment['Default_Payment_Method__c'] = data['defaultPaymentMethod']
        if 'currency' in data:
            update_payment['CurrencyIsoCode'] = data['currency']

        response = sf.Payment__c.update(payment_id, update_payment)
        
        return {
            "id": payment_id,
            "message": "Payment method updated successfully"
        }
    except SalesforceMalformedRequest as e:
        raise e

# # account_id_to_find = 'A-41225'
# account_id_to_find = '001VE000008xC0dYAE'

# query = f"SELECT Id, Name, Account_ID__c, RecordTypeId, CurrencyIsoCode,(SELECT Id, AccountId, Name, OtherPhone, Member_ID__c, Age__c FROM Contacts) FROM Account WHERE ID = '{account_id_to_find}'"
# # query = f"SELECT Provider_Name__c, Method_Name__c, Customer_Phone_Number__c, Customer_Name__c FROM Opportunity WHERE AccountId = '{account_id_to_find}'"
# # query = f"SELECT ID, Amount, Shopify_Order_Number__c,Name FROM Opportunity WHERE AccountId = '{account_id_to_find}' AND StageName = 'Ordered'"
# response = sf.query(query)
# # if response['totalSize'] > 0:
# #     opportunity_details = response['records'][0]
# #     opportunity_id = opportunity_details.get('Id')
# #     opportunity_amount = opportunity_details.get('Amount')
# #     opportunity_shopify_order_no = opportunity_details.get('Shopify_Order_Number__c')
# #     opportunity_name = opportunity_details.get('Name')
# #     opp_item_query = f"SELECT Product__c, Price__c, Quantity__c, Shopify_Order_Number__c, 	Date__c FROM Opportunity_Item__c WHERE Opportunity__c = '{opportunity_id}' "
# #     opp_item = sf.query(opp_item_query)
# #     if opp_item['totalSize'] > 0:
# #         opp_item_details=opp_item['records'][0]
# #         opp_item_products= opp_item_details.get('Product__c')
# #         opp_item_price= opp_item_details.get('Price__c')
# #         opp_item_quantity= opp_item_details.get('Quantity__c')
# #         opp_item_shopify_order_no= opp_item_details.get('Shopify_Order_Number__c')
# #         opp_item_date= opp_item_details.get('Date__c')

# if response['totalSize'] > 0:
#     account_details = response['records'][0]
#     print("Account Details Found:", account_details)
#     # account_name = account_details.get('Name')
#     # account_id = account_details.get('Account_ID__c')
#     # print("Account Holder:",account_name)
#     # print("Account ID:",account_id)
# else:
#     print("No account found with this Account_ID__c.")