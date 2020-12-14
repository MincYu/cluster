import os
import shutil
import subprocess
import json
from functools import reduce
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--num', type=int, default=128, help="Number of function instances per worker")
args = parser.parse_args()

num = args.num

work_dir = os.path.dirname(os.path.abspath(__file__))
prefix_path = os.path.join(work_dir, "prefix.yml")
suffix_path = os.path.join(work_dir, "suffix.yml")

output_path = os.path.join(work_dir, "store-function-ds.yml")

output_str_list = []
output_str_list.append(open(prefix_path, 'r').readlines())
# output_str_list = output_str_list[:-1]

# function_container_lines = ''
for i in range(num):
    line = '''
      - name: function-'''+ str(i + 1) + '''
        resources:
          limits:
            cpu: 40m
            memory: "200M"
        image: cheneyyu/test_cb
        imagePullPolicy: Always
        env:
        - name: ROUTE_ADDR
          value: ROUTE_ADDR_DUMMY
        - name: MGMT_IP
          value: MGMT_IP_DUMMY
        - name: SCHED_IPS
          value: SCHED_IPS_DUMMY
        - name: THREAD_ID
          value: "''' + str(i) + '''"
        - name: ROLE
          value: executor
        - name: REPO_ORG
          value: hydro-project
        - name: REPO_BRANCH
          value: master
        - name: ANNA_REPO_ORG
          value: hydro-project
        - name: ANNA_REPO_BRANCH
          value: master
        - name: STORAGE_OR_DEFAULT
          value: STORAGE_OR_DEFAULT_DUMMY
        volumeMounts:
        - mountPath: /requests
          name: ipc'''
    # function_container_lines += line
    output_str_list.append(line)
output_str_list.append("\n")
output_str_list.append(open(suffix_path, 'r').readlines())

with open(output_path, 'w') as f:
    for line in output_str_list:
        f.writelines(line)

