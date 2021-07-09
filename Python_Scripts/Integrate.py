# This is a python script
import sys
import logging
import requests
import calendar
import datetime
import urllib3
import csv
import psycopg2
import json
from datetime import datetime, date, timedelta
from psycopg2 import Error

# --- Disabling SSL Cert Verification --- #
urllib3.disable_warnings()

# --- Trackers Ids Input --- #
tid_file = open('./resources/Trackers_Names_and_Ids.csv', 'r')
reader = csv.reader(tid_file)
tids = [i[0] for i in reader]

# --- Grabbing the Last Execution Date of the script --- #
la_ex_file = open('./resources/la_ex_date.txt', 'r')
la_ex_date = la_ex_file.readlines()
la_ex_date = str(la_ex_date)
la_ex_date = datetime.strptime(la_ex_date[2:12], "%Y-%m-%d").date()
la_ex_file.close()

# --- Logging Config --- #
str1 = './logs/Integrate' + str(date.today()) + '.log'
logging.basicConfig(filename=str1, level=logging.INFO)

# --- DB Connection --- #

try:
    connection = psycopg2.connect(user="postgres",
                                  password="postgres",
                                  host="X.X.X.X",
                                  port="5432",
                                  database="odoo_db")
    cursor = connection.cursor()
    logging.info('Connected to Endpoint X.X.X.X')

except psycopg2.DatabaseError as error:
    logging.error("Error Connecting the Database at X.X.X.X")

# --- Admin User ID in Odoo DB --- #
user_id = 1

# --- Loop on the Tracker IDs --- #
auth_key = 'tlp-k1-5.c8df505800bc8af2e96b0dcde9d2b68cbc7e85a52d3f69ce34283cefce2abe19'
for tid in tids:
    write_date = str(date.today() - timedelta(1))
    offset = 0
    length = 100
    i = 1

    # --- API Requesting --- #
    while length == 100:
        response = requests.get(
            "https://tuleap.nctr.sd/api/trackers/" + tid.rstrip() + "/artifacts?values=all&limit=100&offset=" + str(
                offset), headers={
                'X-Auth-AccessKey': auth_key}, verify=False)

        if response.status_code != 200:
            logging.error("Problem connecting the API while calling for ID: " + tid)

        data = json.loads(response.text)
        length = len(data)
        offset = offset + length

        # --- For emtpy trackers --- #
        if length == 0:
            logging.info('Empty Tracker!, This will be broke! Tracker_ID: ' + tid)
            break

        # --- Loop on the Artifacts --- #
        for el in data:
            logging.info('Working on Artifact ID: ' + str(el['id']))
            artifact_title = 'None'
            artifact_type = 'None'
            artifact_tracker_name = 'None'
            end_date = 'None'
            is_end_nulled = False
            artifact_assignee = 'None'
            artifact_compt = 'None'
            artifact_eval_score = 'None'
            artifact_eval_comment = 'None'
            artifact_status = 'None'
            artifact_id = 0
            artifact_pr_id = 0
            artifact_act_eff = 0.0
            artifact_pl_eff = 0.0
            is_parent_task = False

            for item1 in el['values']:
                # --- End_date --- #
                if item1['label'] == 'End Date':
                    if item1['value'] is not None:
                        artifact_en_date = item1['value'][:10]
                        end_date = datetime.strptime(artifact_en_date, '%Y-%m-%d').date()
                    else:
                        artifact_en_date = 'None'
                        end_date = 'None'
                        is_end_nulled = True

                # --- Parent_Tasks excluding --- #
                elif item1['label'] == 'References':
                    if len(item1['value']) < 1:
                        is_parent_task = False
                        continue
                    else:
                        for reference in item1['value']:
                            if 'Task' in el['tracker']['label'] and el['tracker']['label'] != 'Administrative  Tasks' and 'CTask' not in el['xref'] and 'CTask' in reference['ref']:
                                is_parent_task = True
                                break
                            else:
                                is_parent_task = False
                                continue

            if is_parent_task:
                logging.info('This is a Parent Task, ID is:  (' + str(el['id']) + ')')
                continue

            ###############################################
            if is_end_nulled or end_date < la_ex_date:
                is_not_wanted_artifact = True
                to_execute = False
            else:
                to_execute = True
                is_not_wanted_artifact = False
            ##############################################

            # --- to_execute artifact --- #
            if to_execute:

                logging.info('\n\nTask is to_execute ID: ' + str(el['id']) + ', End_Date: ' + artifact_en_date)

                # ---------------- artifact_id ----------------- #
                logging.info("\tArtifact Id is: " + str(el['id']))
                artifact_id = el['id']

                # ---------------- title ---------------- #
                if el['title'] is not None:
                    artifact_title = el['title']
                else:
                    artifact_title = 'None'

                # ---------------- submitted_on --------------- #
                logging.info('\tSubmitted on: ' + el['submitted_on'])
                submitted_on_date = el['submitted_on']

                # ---------------- Project Id ---------------- #
                logging.info("\tProject ID is: " + str(el['project']['id']))
                artifact_pr_id = el['project']['id']

                # ---------------- tracker_name --------------- #
                logging.info('\tTracker Name is: ' + el['tracker']['label'].encode('utf-8'))
                artifact_tracker_name = el['tracker']['label']

                # ---------------- login ---------------- #
                if len(el['assignees']) == 0:
                    artifact_assignee = 'None'
                elif el['assignees'][0]['ldap_id'] is None:
                    logging.info('\t' + el['assignees'][0]['ldap_id'])
                    logging.info('\tAdmin Artifact, Continue!')
                    continue
                else:
                    artifact_assignee = el['assignees'][0]['ldap_id']
                logging.info('\tAssignee is: ' + artifact_assignee)

                # ---------------- status ---------------- #
                if el['status'] is not None:
                    artifact_status = el['status']
                else:
                    artifact_status = 'None'
                logging.info('\tStatus is: ' + artifact_status)

                # --- The rest can be got via a for loop --- #
                for item in el['values']:
                    # ---------------- planned_hours + actual_hours ---------------- #
                    if item['label'] == 'Planned Hours':
                        if item['value'] is not None:
                            artifact_pl_eff = float(item['value'])
                        else:
                            artifact_pl_eff = 0.0
                        logging.info("\tPlanned Hours is: " + str(artifact_pl_eff))

                    elif item['label'] == 'Actual Hours':
                        if item['value'] is not None:
                            artifact_act_eff = float(item['value'])
                        else:
                            artifact_act_eff = 0.0
                        logging.info("\tActual Hours is: " + str(artifact_act_eff))

                    # ---------------- Start_date ---------------- #
                    elif item['label'] == 'Start Date':
                        if item['value'] is not None:
                            artifact_st_date = item['value'][:10]
                        else:
                            artifact_st_date = 'None'
                        logging.info("\tStart Date is: " + artifact_st_date)

                    # ---------------- type ---------------- #
                    elif item['label'] == 'Type':
                        if len(item['values']) >= 1:
                            artifact_type = item['values'][0]['label']
                        else:
                            artifact_type = 'None'
                        logging.info('\tType is: ' + artifact_type)

                    # ---------------- competency ---------------- #
                    elif item['label'] == 'Competency':
                        if len(item['values']) > 0:
                            artifact_compt = item['values'][0]['label']
                        else:
                            artifact_compt = 'None'
                        logging.info("\tCompetency earned is: " + artifact_compt.encode('utf-8'))

                    # ---------------- Handling admin_affairs_tasks_title structure ---------------- #
                    elif item['label'] == 'Task title' and 'bind_value_ids' in item:
                        artifact_title = ''
                        if item['bind_value_ids'] is not None:
                            for task_title in item['bind_value_ids']:
                                artifact_title = artifact_title + task_title + ', '
                            artifact_title = artifact_title[:-2]
                            logging.info('\tAdmin Affairs Task is: ' + artifact_title.encode('utf-8'))
                        else:
                            artifact_title = 'None'

                    # ---------------- eval_score + eval_comment ---------------- #
                    elif item['label'] == 'Evaluation':
                        if len(item['values']) > 0:
                            artifact_eval_score = item['values'][0]['label']
                        else:
                            artifact_eval_score = str(0)
                        logging.info('\tEvaluation Score is: ' + artifact_eval_score)

                    elif item['label'] == 'Evaluation Comment':
                        if item['value'] is not None:
                            artifact_eval_comment = item['value']
                        else:
                            artifact_eval_comment = 'None'
                        logging.info('\tEvaluation Comment is: ' + artifact_eval_comment.encode('utf-8'))

                artifact_id = int(artifact_id)
                artifact_title = artifact_title[:200].encode('utf-8') if len(artifact_title) > 200 else artifact_title.encode('utf-8')
                artifact_compt = artifact_compt[:200].encode('utf-8') if len(artifact_compt) > 200 else artifact_compt.encode('utf-8')
                artifact_eval_comment = artifact_eval_comment[:200].encode('utf-8') if len(artifact_eval_comment) > 200 else artifact_eval_comment.encode('utf-8')
                artifact_act_eff = round(artifact_act_eff, 2)
                artifact_pl_eff = round(artifact_pl_eff, 2)

                db_query = ''' 
                                    DO
                                    $do$
                                    BEGIN
                                        IF EXISTS (SELECT artifact_id FROM public."hr_assessment_artifacts_archive" WHERE artifact_id = %s) THEN
                                            UPDATE public."hr_assessment_artifacts_archive" SET 
                                            (title, type, login, competency, status, start_date, end_date, actual_hours, planned_hours, tracker_name, eval_score, eval_comment, write_date) 
                                            =
                                            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                            WHERE artifact_id = %s;
                                        ELSE 
                                            INSERT INTO public."hr_assessment_artifacts_archive"
                                        	(artifact_id, title, type, login, competency, status, project_id, 
                                        	    start_date, end_date, actual_hours, planned_hours, tracker_name,
                                        	    eval_score, eval_comment, create_uid, create_date, write_date, write_uid, submitted_on)
                                            VALUES
                                        	(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                                        END IF;
                                    END 
                                    $do$
                                '''

                # ---------------- "upsert" is a term used for Update-or-Insert type Queries ---------------- #
                record_to_upsert = (
                artifact_id, artifact_title, artifact_type, artifact_assignee, artifact_compt, artifact_status,
                artifact_st_date, artifact_en_date, artifact_act_eff, artifact_pl_eff, artifact_tracker_name,
                artifact_eval_score, artifact_eval_comment, write_date, artifact_id, artifact_id, artifact_title,
                artifact_type, artifact_assignee, artifact_compt, artifact_status, artifact_pr_id, artifact_st_date,
                artifact_en_date, artifact_act_eff, artifact_pl_eff, artifact_tracker_name, artifact_eval_score,
                artifact_eval_comment, user_id, write_date, write_date, user_id, submitted_on_date)

                cursor.execute(db_query, record_to_upsert)
                connection.commit()

            # --- is_not_wanted_artifact --- #
            else:
                logging.info('This Artifact is not_wanted: ' + str(el['id']) + ', End_date: ' + artifact_en_date)
                continue

# ---------------- PostgreSQL Connection ends --------------------- #

if connection is not None:
    connection.close()

# ---------------- PostgreSQL Connection ends --------------------- #

# ---------------- Save new la_ex_date value  --------------------- #

year = la_ex_date.year
month = la_ex_date.month

if month == 12:
        month = 1
        year += 1
else:
        month += 1

if month < 10:
	month = '0' + str(month)
else:
	month = str(month)

year = str(year)

new_date_str = year + '-' + month + '-01\n'
file2 = open("./resources/la_ex_date.txt", "w")
file2.write(new_date_str)
file2.close()

# ---------------- Save new la_ex_date value  --------------------- #
