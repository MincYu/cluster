#!/usr/bin/env python3

import logging
import os
import sys

import zmq

def add(ntype, num):
    context = zmq.Context(1)

    add_push_socket = context.socket(zmq.PUSH)
    add_push_socket.connect('ipc:///tmp/node_add')

    msg = ntype + ':' + str(num)
    add_push_socket.send_string(msg)

def remove(ntype, ip):
    context = zmq.Context(1)

    remove_push_socket = context.socket(zmq.PUSH)
    remove_push_socket.connect('ipc:///tmp/node_remove')

    msg = ntype + ':' + ip
    remove_push_socket.send_string(msg)

if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'add':
        add(sys.argv[2], sys.argv[3])
    elif action == 'remove':
        remove(sys.argv[2], sys.argv[3])
    else:
        print('No such action ' + action)
