#  Copyright 2019 U.C. Berkeley RISE Lab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import random
import zmq
import os

from hydro.management.util import (
    get_executor_pin_address,
    get_executor_unpin_address,
    send_message
)
from hydro.shared.proto.internal_pb2 import CPU, GPU

from hydro.management.scaler.base_scaler import BaseScaler
from hydro.shared.proto.internal_pb2 import PinFunction
from hydro.shared.proto.cloudburst_pb2 import GenericResponse


class DefaultScaler(BaseScaler):
    def __init__(self, ip, ctx, add_socket, remove_socket, pin_accept_socket):
        self.ip = ip
        self.context = ctx
        self.add_socket = add_socket
        self.remove_socket = remove_socket
        self.pin_accept_socket = pin_accept_socket
        self.enable_scaling = os.environ['ENABLE_SCALING'] == '0'
    
    def try_replicate_to_all(self, fname, executor_statuses):
        msg = PinFunction()
        msg.name = fname
        msg.response_address = self.ip 

        existing_replicas = set()
        cpu_executors = set()
        for key in executor_statuses:
            status = executor_statuses[key]
            if status.type == CPU:
                cpu_executors.add(key)
            for func in status.functions:
                if func == fname:
                    existing_replicas.add(key)
        other_nodes = cpu_executors.difference(existing_replicas)

        existing_size = len(existing_replicas)
        if existing_size == 0:
            logging.info('All replicas %s no registered, return.' % (fname))
            return

        new_size = len(other_nodes)
        success_count = 0
        for node in other_nodes:
            ip, tid = node
            send_message(self.context, msg.SerializeToString(),
                         get_executor_pin_address(ip, tid))

            response = GenericResponse()
            try:
                response.ParseFromString(self.pin_accept_socket.recv())
            except zmq.ZMQError:
                logging.error('Pin operation to %s:%d timed out for %s.' %
                              (ip, tid, fname))
                continue

            if response.success:
                logging.info('Pin operation to %s:%d for %s successful.' %
                              (ip, tid, fname))
                success_count += 1
            else:
                # The pin operation was rejected, remove node and try again.
                logging.error('Node %s:%d rejected pin for %s.'
                              % (ip, tid, fname))
        logging.info('All replicas %s. existing: %d, new: %d, success: %d' % (fname, existing_size, new_size, success_count))

    def replicate_function(self, fname, num_replicas, function_locations,
                           cpu_executors, gpu_executors):

        existing_replicas = function_locations[fname]

        msg = PinFunction()
        msg.name = fname
        msg.response_address = self.ip

        # TODO: Add proper support for autoscaling GPU instances and for
        # checking whether batching is enabled.
        if 'gpu' in fname:
            candidate_nodes = gpu_executors.difference(existing_replicas)

            for key in function_locations:
                if 'gpu' in key:
                    for location in function_locations[key]:
                        candidate_nodes.discard(location)
        else:
            candidate_nodes = cpu_executors.difference(existing_replicas)

        for _ in range(num_replicas):
            if len(candidate_nodes) == 0:
                continue

            if not self.enable_scaling:
                continue

            ip, tid = random.sample(candidate_nodes, 1)[0]
            send_message(self.context, msg.SerializeToString(),
                         get_executor_pin_address(ip, tid))

            response = GenericResponse()
            try:
                response.ParseFromString(self.pin_accept_socket.recv())
            except zmq.ZMQError:
                logging.error('Pin operation to %s:%d timed out for %s.' %
                              (ip, tid, fname))
                candidate_nodes.remove((ip, tid))
                continue

            if response.success:
                logging.info('Pin operation to %s:%d for %s successful.' %
                              (ip, tid, fname))
                function_locations[fname].add((ip, tid))
            else:
                # The pin operation was rejected, remove node and try again.
                logging.error('Node %s:%d rejected pin for %s.'
                              % (ip, tid, fname))
            candidate_nodes.remove((ip, tid))

    def dereplicate_function(self, fname, num_replicas, function_locations):
        if num_replicas < 2:
            return
        if not self.enable_scaling:
            return
        while len(function_locations[fname]) > num_replicas:
            ip, tid = random.sample(function_locations[fname], 1)[0]
            send_message(self.context, fname,
                         get_executor_unpin_address(ip, tid))

            function_locations[fname].discard((ip, tid))

    def add_vms(self, kind, count):
        msg = kind + ':' + str(count)
        if self.enable_scaling:
            self.add_socket.send_string(msg)
        else:
            logging.info('Disable scaling (add) %s' % msg)

    def remove_vms(self, kind, ip):
        msg = kind + ':' + ip
        if self.enable_scaling:
            self.remove_socket.send_string(msg)
        else:
            logging.info('Disable scaling (remove) %s' % msg)
