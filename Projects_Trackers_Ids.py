# -*- coding: utf-8 -*-
# REST API client for Tuleap open ALM

#The purpose of this project is to create a python module that can be used for accessing a Tuleap
#instance using its REST API.

## Usage example:
#```python
import os
import os.path
import csv
import logging
import datetime
from datetime import datetime
from datetime import date
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

file_name = './resources/Trackers_Names_and_Ids.csv'
auth_token = "tlp-k1-5.c8df505800bc8af2e96b0dcde9d2b68cbc7e85a52d3f69ce34283cefce2abe19"

str1 = './logs/Projects_Trackers_Ids' + str(date.today()) + '.log'
logging.basicConfig(filename=str1, level=logging.INFO)


connection = Connection()
success = connection.set_access_key("https://tuleap.nctr.sd/api", auth_token)

if success:
	# Read projects id from file projects/data
	f = open('./resources/Projects_Names_and_Ids.csv', 'r')
	reader = csv.reader(f)
	projects_ids = [int(i[0]) for i in reader]
	# Projects trackers
	projects = Projects(connection)
	loop = 0
	for x in projects_ids:
		logging.info('Project ID: ' + str(x))
		success = projects.request_trackers(x, 50, None)
		if success:
			tracker_list = projects.get_data()
			tracker_list = list(filter(lambda i: (i['item_name'] != "story" and i['item_name'] != "sprint" and i['item_name'] != "rel" and i['item_name'] != "epic"), tracker_list))
			tracker_id = { sub['id']:sub['label'] for sub in tracker_list }
			if loop == 0:
				w = csv.writer(open(file_name, "w"))
			else:
				w = csv.writer(open(file_name, "a+"))
			for key, val in tracker_id.items():
				logging.info("Working on Tracker: " + val.encode('utf-8') + " ID: " + str(key))
				w.writerow([key, val.encode('utf-8')])
		loop = 1
connection.logout()

logging.info("Now Triggering Integrate.py...")
str2 = 'python ./Integrate.py 2> ./logs/error' + str(date.today()) + '.log &'
os.system(str2)
