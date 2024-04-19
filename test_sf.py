from simple_salesforce import Salesforce
from dotenv import load_dotenv
import os

load_dotenv()
username = os.getenv('SF_USERNAME')
password = os.getenv('SF_PASSWORD')
security_token = os.getenv('SF_SECURITY_TOKEN')

sf = Salesforce(username=username, password=password, security_token=security_token, domain='test')

# account_id_to_find = 'A-41225'
account_id_to_find = '001VE000008xC0dYAE'

# query = f"SELECT Id, Name, Account_ID__c,(SELECT Id, FirstName, LastName, Email, Phone,HOH_Relationship__c FROM Contacts) FROM Account WHERE Account__c = '{account_id_to_find}'"
query = f"SELECT Provider_Name__c, Method_Name__c, Customer_Phone_Number__c, Customer_Name__c FROM Payment__c WHERE Account__c = '{account_id_to_find}'"
response = sf.query(query)

if response['totalSize'] > 0:
    account_details = response['records'][0]
    print("Account Details Found:", account_details)
    # account_name = account_details.get('Name')
    # account_id = account_details.get('Account_ID__c')
    # print("Account Holder:",account_name)
    # print("Account ID:",account_id)
else:
    print("No account found with this Account_ID__c.")