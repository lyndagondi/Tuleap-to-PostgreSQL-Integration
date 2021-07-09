import sys
import csv
import logging
import requests
import datetime
import urllib3
import psycopg2
import json
from datetime import datetime, date, timedelta
from psycopg2 import Error

# --- Disabling SSL Cert Verification --- #
urllib3.disable_warnings()

# --- Logging configurations --- #
str1 = './logs/Projects_Data' + str(date.today()) + '.log'
logging.basicConfig(filename=str1, level=logging.INFO)

try:
    connection = psycopg2.connect(user="postgres",
                                  password="postgres",
                                  host="X.X.X.X",
                                  port="5432",
                                  database="odoo_db")
    cursor = connection.cursor()
except psycopg2.DatabaseError as error:
    logging.error("Error Connecting the Database at X.X.X.X")

projs_dict = {}
f = open('./resources/Projects_Names_and_Ids.csv', 'r')
reader = csv.reader(f)
projs_dict = {row[0]: row[1] for row in reader}
access_token = 'tlp-k1-5.c8df505800bc8af2e96b0dcde9d2b68cbc7e85a52d3f69ce34283cefce2abe19'
user_id = 1

# --- For loop on Projects --- #

for pr in projs_dict:
    write_date = str(date.today() - timedelta(1))
    # ----- This is the Project_Id ----- #
    pr_id = int(pr)
    # ----- This is the Project Name ----- #
    pr_name = projs_dict[pr]

    response = requests.get("https://tuleap.nctr.sd/api/projects/" + pr + "/user_groups",
                            headers={'X-Auth-AccessKey': access_token}, verify=False)
    logging.info('Calling API projects/' + pr_name + '/user_groups')
    data = json.loads(response.text)

    # --- For loop on Projects_User_Groups --- #

    for group in data:
        gr_id = group['id']
        gr_label = group['label']

        is_project_member_group = True if gr_label == 'Project members' else False
        is_project_admins_group = True if gr_label == 'Project administrators' else False

        if is_project_member_group or is_project_admins_group:
            logging.info('This is the Group (' + gr_label + ') we will be working on!')
            #is_manager = 'TRUE' if group['label'] == 'Project administrators' else 'FALSE'

            # --- Requesting the User_Groups/id/Users API --- #

            offset = 0
            length = 50
            x = 1
            while length == 50:
                logging.info('Now requesting the users of: ' + pr_name.decode('utf-8') + '----> ' + gr_label)
                response2 = requests.get("https://tuleap.nctr.sd/api/user_groups/" + str(gr_id) + "/users?limit=50&offset=" + str(offset),
                                         headers={'X-Auth-AccessKey': access_token}, verify=False)

                users_resp = json.loads(response2.text)
                logging.info('Iteration No(' + str(x) + '), Response length: ' + str(len(users_resp)) + ', Offset: ' + str(offset))

                length = len(users_resp)
                offset += length
                users = []

                for user in users_resp:
                    not_user = user['ldap_id'] == 'costing.user' or user['ldap_id'] == 'fadul.a' or user['ldap_id'] == 'hr.team' or not(user['ldap_id'])
                    if not_user:
                        continue
                    else:
                        users += [user['ldap_id']]
                x += 1
            if is_project_admins_group:
                logging.info('Administrators: ')
            else:
                logging.info('Project_Members: ')

            for user in users:
                logging.info(user.decode('utf-8'))
                db_query = '''
                DO
                $do$
                BEGIN
                IF EXISTS (SELECT member_login FROM public."hr_assessment_projects_archive" WHERE member_login = '%s' and project_id = %s) THEN
                UPDATE public."hr_assessment_projects_archive" SET
                            (project_name, is_manager, write_date)
                            =
                            ('%s', %s, '%s')
                            WHERE member_login = '%s' and project_id = %s;
                ELSE
                INSERT INTO public."hr_assessment_projects_archive"
                            (member_login, project_id, project_name, is_manager, create_uid, create_date, write_uid, write_date)
                            VALUES
                            ('%s', %s, '%s', %s, %s, '%s', %s, '%s');
                END IF;
                END
                $do$
                '''
                record_to_upsert = (user, pr_id, pr_name.decode('utf-8'), is_project_admins_group, write_date, user, pr_id, user, pr_id, pr_name.decode('utf-8'), is_project_admins_group, user_id, write_date, user_id, write_date)
                cursor.execute(db_query % record_to_upsert)
                connection.commit()
        else:
            continue
    str2 = 'Finished Migration for Project: ' + pr_name.decode('utf-8') + ' Users!'
    logging.info(str2)
logging.info('Finished Migrating all projects!')
if connection is not None:
    connection.close()
