from logging import error
from os import write
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.exceptions import Fault
import pandas as pd
import sys
from yachalk import chalk
import numpy as np
import logging

logging.getLogger('zeep').setLevel(logging.ERROR)


# global envionrment variables
DEBUG = False
WSDL_FILE = '//Users//harshen//Documents//Dev-Projects//Cisco//Cisco-UCM-User-Updator/AXLAPI.wsdl'

user = 'administrator'
passwd = 'dCloud123!'
cucm = '198.18.133.3'


# AXl session initialisation
session = Session()
session.verify=False
session.auth = HTTPBasicAuth( user,passwd )
transport = Transport( session = session, timeout = 10 )
settings = Settings( strict = False, xml_huge_tree = True )
client = Client( WSDL_FILE, settings = settings, transport = transport)
service = client.create_service( '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding',f'https://{cucm}:8443/axl/')


# testing variables
# userId = "harshen"
# newDevicesList = ['CSFDEVICE1','CSFDEVICE2']
# newDeviceProfiles = ['EMTEST1','EMTEST']
# mailID = "harshen.cisco.com"


def obtainData(file):
	input_data = pd.read_csv(file)
	
	## senity check
	print(chalk.green("Perform input csv senity check.....Please wait...."))
	missing_userid = input_data[input_data['userid'].isna()].index.tolist()
	missing_mailid = input_data[input_data['mailid'].isna()].index.tolist()
	duplicated_userid = input_data[input_data.duplicated(['userid'],keep=False)].index.tolist()
	duplicated_mailid = input_data[input_data.duplicated(['mailid'],keep=False)].index.tolist()
	if(missing_userid or missing_mailid or duplicated_userid or duplicated_mailid):
		print(chalk.red("Please rectify the following errors:"))
		print("\tMissing userid Rows: {}".format([row+1 for row in missing_userid]))
		print("\tMissing mailID Rows: {}".format([row+1 for row in missing_mailid]))
		print("\tDuplicated userid Rows: {}".format([row+1 for row in duplicated_userid]))
		print("\tDuplicated mailid Rows: {}".format([row+1 for row in duplicated_mailid]))
		print(chalk.red("Update Abort"))
		sys.exit(0)
	else:
		print(chalk.green("Sentity Check Completed: All good ^_^!! "))
		return input_data.fillna(0)

def updateUserRecord(service,userId, mailId,newDevicesList, newDeviceProfiles,logs,index):
	try:
		resp_getUser = service.getUser(userid=userId)
		#print(resp_getUser)
		orgin_associatedDevices = resp_getUser['return']['user']['associatedDevices']['device'] if resp_getUser['return']['user']['associatedDevices']!=None else []
		orgin_ctiControledDeviceProfiles = [profile['_value_1'] for profile in resp_getUser['return']['user']['ctiControlledDeviceProfiles']['profileName']]
		associatedDevices = {
			'device': orgin_associatedDevices+newDevicesList
		}
		ctiControlledDeviceProfiles = {
			'profileName': orgin_ctiControledDeviceProfiles + newDeviceProfiles
		}
		resp_updateUser = service.updateUser(userid=userId,associatedDevices=associatedDevices,ctiControlledDeviceProfiles=ctiControlledDeviceProfiles,mailid=mailId)
		logs.loc[index,'Status'] = "Update Successful"
	except Fault as err:
		logs.loc[index,'Status'] = err
		print(chalk.red('Error: Update user {}:{}'.format(userId,err)))
	else:
		print(chalk.green('User {} Update Successful'.format(userId)))

def concatDP(input_data,index):
	concatedDP = [dp for dp in [input_data.loc[index,'emprofile1'],input_data.loc[index,'emprofile2'],input_data.loc[index,'emprofile3']] if dp]
	return concatedDP

def main():
	try:
		if sys.argv[1]:
			input_data=obtainData(sys.argv[1])
			print(input_data)
		else:
			print(chalk.red("Please specify the input csv file path.. e.g. python ucm-user-update.py test.csv"))
			sys.exit(0)
		logs = input_data.copy().replace(0,np.nan)
		logs['Status'] = np.nan
		for index, user_record in input_data.iterrows():
			to_associate_devices = ['TCT'+user_record['userid'],'BOT'+user_record['userid'],'CSF'+user_record['userid']]
			updateUserRecord(service, user_record['userid'],user_record['mailid'],to_associate_devices,concatDP(input_data,index),logs,index)
		logs.to_csv('logs.csv',index=False)
	except OSError as err:
		print(chalk.red(err))

if __name__ == "__main__":
	main()