from simple_salesforce import Salesforce
from dotenv import load_dotenv
import os

load_dotenv()
username = os.getenv('SF_USERNAME')
password = os.getenv('SF_PASSWORD')
security_token = os.getenv('SF_SECURITY_TOKEN')

sf = Salesforce(username=username, password=password, security_token=security_token, domain='test')

def find_payment_method_of_user(user_id):
    query = f"SELECT Provider_Name__c, Method_Name__c, Customer_Phone_Number__c, Customer_Name__c,Default_Payment_Method__c FROM Payment__c WHERE Account__c = '{user_id}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        account_details = response['records'][0]
        user_details={
            "providerName":account_details.get('Provider_Name__c'),
            "methodName":account_details.get('Method_Name__c'),
            "customerPhone":account_details.get('Customer_Phone_Number__c'),
            "customerName":account_details.get('Customer_Name__c'),
            "defaultPaymentMethod":account_details.get('Default_Payment_Method__c')
        }
        return user_details
    else:
        return None
    
def find_user(user_id):
    query = f"SELECT Name, Account_ID__c, Phone, Alternate_Phone__c, Total_Order_Amount__c,Orders_Placed__c, Country__c FROM Account WHERE ID = '{user_id}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        account_details = response['records'][0]
        user_details={
            "name":account_details.get('Name'),
            "accountIdCH":account_details.get('Account_ID__c'),
            "phoneNumber":account_details.get('Phone'),
            "altPhoneNumber":account_details.get('Alternate_Phone__c'),
            "cumulativeOrders":account_details.get('Orders_Placed__c'),
            "cumulativeAmount":account_details.get('Total_Order_Amount__c'),
            "country":account_details.get('Country__c')
        }
        return user_details
    else:
        return None

def find_user_order(user_id, stage):
    query = f"SELECT ID, Amount,Created_Date__c,Shopify_Order_Number__c,Name, StageName FROM Opportunity WHERE AccountId = '{user_id}' AND StageName = '{stage}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        opportunity_details = response['records'][0]
        opportunity_id = opportunity_details.get('Id')
        opportunity_amount = opportunity_details.get('Amount')
        opportunity_shopify_order_no = opportunity_details.get('Shopify_Order_Number__c')
        opportunity_created_date = opportunity_details.get('Created_Date__c')
        opportunity_name = opportunity_details.get('Name')
        opportunity_stage = opportunity_details.get('StageName')
        opp_item_query = f"SELECT Product__c, Price__c, Quantity__c, Shopify_Order_Number__c, 	Date__c FROM Opportunity_Item__c WHERE Opportunity__c = '{opportunity_id}' "
        opp_item = sf.query(opp_item_query)
        if opp_item['totalSize'] > 0:
            opp_item_details=opp_item['records'][0]
            opp_item_products= opp_item_details.get('Product__c')
            opp_item_price= opp_item_details.get('Price__c')
            opp_item_quantity= opp_item_details.get('Quantity__c')
            opp_item_shopify_order_no= opp_item_details.get('Shopify_Order_Number__c')
            opp_item_date= opp_item_details.get('Date__c')
            order_summary={
                "opportunityName":opportunity_name,
                "shopifyOrderNumber":opportunity_shopify_order_no,
                "amount":opportunity_amount,
                "createdDate":opportunity_created_date,
                "currentStage":opportunity_stage,
                "opportunityItem":{
                    "products":opp_item_products,
                    "price":opp_item_price,
                    "quantity":opp_item_quantity,
                    "shopifyOrderNumber":opp_item_shopify_order_no,
                    "date":opp_item_date
                }
            }
            return order_summary
        else:
            raise ValueError("No Opportunity Item associated with this Opportunity")
    else:
        return None
    
def create_new_user(user_name, user_phone, fcm_token, user_country):
    new_account = {
        'Name': user_name,
        'Phone': user_phone,
        'RecordTypeId': '0124x000000ZGecAAG',
        'CurrencyIsoCode': 'MMK',
        'Country__c':user_country,
        'FCM_Token__c': fcm_token
    }

    response = sf.Account.create(new_account)
    new_user_response = {
        'name':user_name,
        'fcmToken':fcm_token,
        'userId':response.get('id')
    }
    return new_user_response

def update_user(fcm_token, user_id):
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

def find_user_by_phone(phone):
    query = f"SELECT Name FROM Account WHERE Phone = '{phone}'"
    response = sf.query(query)

    if response['totalSize'] > 0:
        account_details = response['records'][0]
        user_details= account_details.get('Name')
        return user_details
    else:
        raise ValueError ("No user found!")

def validate_pin(phone, pin):
    query = f"SELECT Name FROM Account WHERE Phone = '{phone}' AND PIN_Code__c = {pin}"
    response = sf.query(query)

    if response['totalSize'] > 0:
        account_details = response['records'][0]
        user_details= account_details.get('Name')
        return user_details
    else:
        raise ValueError ("No user found!")

# # account_id_to_find = 'A-41225'
# account_id_to_find = '001VE000008xC0dYAE'

# query = f"SELECT Id, Name, Account_ID__c, RecordTypeId, CurrencyIsoCode,(SELECT Id, FirstName, LastName, Email, Phone,HOH_Relationship__c FROM Contacts) FROM Account WHERE ID = '{account_id_to_find}'"
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