from os import write
import requests
import sys
import pandas as pd
import numpy as np
import xmltodict,json

## dcloud system settings
# ucm_ip = "198.18.133.3"
# app_username = "administrator"
# app_user_password = "dCloud123!"

# HWL system settings
app_username = 'CCMAdministrator'
app_user_password = "HWLAdmin1"
ucm_ip = '10.103.1.254'

# user specific information
device_name = "SEPB4AE2BC9C05A"
login_user = "aperez"
login_dp = "DP-aperez"


url = "https://{}:8443/emservice/EMServiceServlet".format(ucm_ip)
headers = {
  'Content-Type': 'application/x-www-form-urlencoded'
}

def login_user(conn):
    res = conn.getresponse()
    return res.read()

def read_input_data(file):
    data = pd.read_csv(file)
    return data

def construct_payload(device_name,login_user,login_dp):
    payload = '''xml=
    <request>
        <appInfo>
            <appID>{app_username}</appID>
            <appCertificate>{app_user_password}</appCertificate>
        </appInfo>
        <login>
            <deviceName>{device_name}</deviceName>
            <userID>{login_user}</userID>
            <deviceProfile>{login_dp}</deviceProfile>
        </login>
    </request>
    '''.format(
        app_username=app_username,
        app_user_password=app_user_password,
        device_name=device_name,
        login_user=login_user,
        login_dp=login_dp
        )

    return payload

def login_user(headers, payload,index,logs):
    response = requests.request(
        "POST", 
        url, 
        headers=headers, 
        data=payload,
        verify=False
        )

    data = xmltodict.parse(response.text)
    if('success' in data['response'].keys()):
        logs.loc[index,'Status'] = "Login Successful"
        print("Row {} Login Successful".format(index+1))
    else:
        logs.loc[index,'Status'] = str(data['response']['failure']['error'])
        print("Row {} Login Failed: {}".format(index+1,data['response']['failure']['error'] ))
    return response

def prod_process():
    try:
        if sys.argv[1]:
            input_data = read_input_data(sys.argv[1]).dropna()
        else:
            print("Please specify the input csv file path.. e.g. python ucm-phone-migration.py test.csv")
            sys.exit(0)

        logs = input_data.copy()
        logs['Status'] = np.nan
        for index, record in input_data.iterrows():
            payload = construct_payload(record['Device Name'],record['User ID'],"{}".format(record['User ID']))
            login_user(headers, payload,index,logs)

        logs.to_csv('em_login_logs.csv',index=False)

    except OSError as err:
            logs.loc[index, 'Status'] = err
            print("Error: {}".format(err))


def main():
    prod_process()

if __name__ == "__main__":
	main()