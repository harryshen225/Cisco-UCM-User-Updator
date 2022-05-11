from logging import error
from os import write
import re
from nbformat import read
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings, Plugin, helpers
from zeep.transports import Transport
from zeep.exceptions import Fault
import pandas as pd
import sys
from yachalk import chalk
import numpy as np
import logging
import logging.config
import json


logging.getLogger('zeep').setLevel(logging.DEBUG)


# global envionrment variables
DEBUG = True
LEVEL = 'ERROR'
WSDL_FILE = 'AXLAPI.wsdl'

# HWL UCM
user = 'CCMAdministrator'
passwd = "HWLAdmin1"
cucm = '10.103.1.254'

# dcloud UCM
# user = 'administrator'
# passwd = 'dCloud123!'
# cucm = '198.18.133.3'

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            'level': LEVEL,
            'propagate': True,
            'handlers': ['console'],
        },
    }
})

# AXl session initialisation
session = Session()
session.verify=False
session.auth = HTTPBasicAuth( user,passwd )
transport = Transport( session = session, timeout = 10 )
settings = Settings( strict = False, xml_huge_tree = True)
client = Client( WSDL_FILE, settings = settings, transport = transport)
service = client.create_service( '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding',f'https://{cucm}:8443/axl/')

def read_input_data(file):
    data = pd.read_csv(file)
    return data

def get_phone(service, phone_name):
    phone  = service.getPhone(name=phone_name)
    phone_od = helpers.serialize_object(phone['return']['phone'])
    return phone_od

def refine_phone_input(phone_info):
    #phone_info['name'] = 'SEP123212321299'
    phone_info['protocol'] = 'SIP'
    phone_info['securityProfileName'] = 'Cisco 8945 - Standard SIP Non-Secure Profile'
    phone_info['sipProfileName'] = 'Standard SIP Profile'
    phone_info['phoneTemplateName'] = 'Standard 8945 SIP'

    phone_info.pop('confidentialAccess')
    phone_info.pop('loadInformation')
    # phone_info.pop('preemption')
    phone_info.pop('mlppIndicationStatus')
    # phone_info.pop('singleButtonBarge')
    phone_info.pop('vendorConfig')
    phone_info.pop('currentConfig')
    # phone_info.pop('ctiid')
    # phone_info.pop('uuid')
    #phone_info.pop('versionStamp')
    phone_info.pop('mraServiceDomain')

    # new_phone_info = {
    #     'name': 'SEP123212321299',
    #     'protocol': 'SIP',
    #     'model': 'Cisco 8945',
    #     'product': 'Cisco 8945',
    #     'class': 'Phone',
    #     'protocolSide': 'User',
    #     'callingSearchSpaceName': phone_info['callingSearchSpaceName'],
    #     'devicePoolName':phone_info['devicePoolName'],
    #     'lines':phone_info['lines'],
    #     'commonPhoneConfigName':phone_info['commonPhoneConfigName'],
    #     'locationName':phone_info['locationName'],
    #     'useTrustedRelayPoint':phone_info['useTrustedRelayPoint'],
    #     'phoneTemplateName':'Standard 8945 SIP',
    #     'primaryPhoneName': None,
    #     'sipProfileName': 'Standard SIP Profile',
    #     'securityProfileName': 'Cisco 8945 - Standard SIP Non-Secure Profile',
    #     'builtInBridgeStatus': phone_info['builtInBridgeStatus'],
    #     'packetCaptureMode':phone_info['packetCaptureMode'],
    #     'certificateOperation': phone_info['certificateOperation'],
    #     'deviceMobilityMode': phone_info['deviceMobilityMode'],
    #     'commonDeviceConfigName': None
    # }
    #print(new_phone_info)
    return phone_info


def prod_process():
    if sys.argv[1]:
        input_data = read_input_data(sys.argv[1])
        phone_list = input_data['Device Name(Line)Sort Descending']

    for phone in phone_list:
        phone_config = get_phone(service, phone)
        #print(phone_config)
        new_phone = refine_phone_input(phone_config)
        service.addPhone(new_phone)


def main():
    try:
        prod_process()
    except Fault as err:
        print('Phone: {}'.format(err))
    
if __name__ == "__main__":
	main()

