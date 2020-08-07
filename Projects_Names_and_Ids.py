# REST API client for Tuleap open ALM
#The purpose of this project is to create a python module that can be used for accessing a Tuleap
#instance using its REST API.

import os
import os.path
import csv
import logging
import datetime
from datetime import date
from datetime import datetime
from os import path
from Tuleap.RestClient.Connection import Connection, CertificateVerification
from Tuleap.RestClient.Projects import Projects
from Tuleap.RestClient.ArtifactParser import ArtifactParser,ValueParser

def file_len(fname):
	i = 0
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	return i + 1

# ---- Logging Configurations ---- #
str1 = './logs/Projects_Names_and_Ids' + str(date.today()) + '.log'
logging.basicConfig(filename=str1, level=logging.INFO)

file_name = './resources/Projects_Names_and_Ids.csv'
connection = Connection()
auth_token = "tlp-k1-5.c8df505800bc8af2e96b0dcde9d2b68cbc7e85a52d3f69ce34283cefce2abe19"
success = connection.set_access_key("https://tuleap.nctr.sd/api", auth_token)

# ------------- Extract Project IDs and Names --------------- #
if success:
    
    Response_Offset = file_len(file_name) if path.exists(file_name) else 0
    Response_Length = 50
    Response_Limit = 50
    while Response_Length == 50:
      
        projects = Projects(connection)
        success = projects.request_project_list(Response_Limit, Response_Offset)
	projects_dict = dict()

        if success:
          project_list = projects.get_data()	 
	  Response_Length = len(project_list)

	  # ---- Extract IDs and Names from project list in a Dict variable type ---- #
 	  
	  for sub in project_list:
		logging.info('Working on Project: ' + str(sub['id']))
		is_active_logic = sub['status'] == 'active' or sub['status'] == 'suspended'
		if sub['is_template'] == False and is_active_logic:
			logging.info('Project is Active and Not Template')
			projects_dict.update( {sub['id']:sub['label']} )
		else:
			logging.info('Project is either InActive or Template')

	  # ---- Writing IDs and Names to Projects_Names_and_Ids.csv File ----------- #
	  w = csv.writer(open(file_name, "a+"))
	  for key, val in projects_dict.items():
		  w.writerow([key, val.encode('utf-8')])
	  Response_Offset = Response_Offset + Response_Length

	else:
	  logging.error('Can not connect projects api')
    
    connection.logout()
    logging.info('Finished Extracting Project Names and IDs')

else:
    logging.error('Can not Connect Tuleap API!')

logging.info("Now Triggering Projects_Trackers_Ids.py and Projects_Data.py")
str2 = 'python ./Projects_Data.py 2> ./logs/Projects_Data_error' + str(date.today())  +  '.log &'
str3 = 'python ./Projects_Trackers_Ids.py 2> ./logs/Projects_Trackers_Ids_error' + str(date.today())  +  '.log &'

os.system(str2)
os.system(str3)
