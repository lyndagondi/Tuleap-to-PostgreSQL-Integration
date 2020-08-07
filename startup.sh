#!/usr/bin/bash

cd /root/tuleap-to-postgresql/
python ./Projects_Names_and_Ids.py 2> ./logs/Project_Names_error.log &
