import argparse
import os

from hydro.shared import util
from hydro.cluster.add_nodes import get_current_pod_container_pairs
from kubernetes.stream import stream
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

client, apps_client = util.init_k8s()
pods = client.list_namespaced_pod(namespace=util.NAMESPACE, label_selector='role=function').items
pods = get_current_pod_container_pairs(pods)

pool = ThreadPoolExecutor(max_workers=1000)

futures = []
for pname, cname in pods:
    if cname.startswith('function'):
        cmd = f'kubectl exec -it {pname} --container {cname} -- pkill -9 python'
        futures.append(pool.submit(os.system, cmd))

results = [fu.result() for fu in futures]
print(f'Restart {len(results)} functions')