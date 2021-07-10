#!/usr/bin/env python3

import logging
import os
import sys

import zmq

from hydro.cluster.add_nodes import add_nodes
from hydro.cluster.remove_node import remove_node
from hydro.shared import util

os.environ['STORAGE_OR_DEFAULT'] = '1'
client, apps_client = util.init_k8s()
# cfile = '/hydro/anna/conf/anna-config.yml'
cfile = '/home/ubuntu/hydro-project/anna/conf/anna-base.yml'
prefix = '/home/ubuntu/hydro-project/cluster/hydro/cluster'
def add(ntype, num):
    add_nodes(client, apps_client, cfile, [ntype], [num],
                prefix=prefix)
    logging.info('Successfully added %d %s node(s).' % (num, ntype))

def remove(ntype, ip):
    remove_node(ip, ntype)
    logging.info('Successfully removed node %s.' % (ip))
    
if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'add':
        add(sys.argv[2], int(sys.argv[3]))
    elif action == 'remove':
        remove(sys.argv[2], sys.argv[3])
    else:
        print('No such action ' + action)
