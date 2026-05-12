import json
import os

import pandas as pd
import torch
from tqdm import tqdm

print('loading raw data')
with open('processed_data/uid_index.json', 'r') as f:
    uid_index = json.load(f)

edge = pd.read_csv('Twibot22_Dataset/edge.csv')

print('extracting edge_index&edge_type')
edge_index = []
edge_type = []
list_membership = {}

for _, row in tqdm(edge.iterrows(), total=len(edge)):
    sid = row['source_id']
    tid = row['target_id']
    relation = row['relation']

    sid_idx = uid_index.get(sid)
    tid_idx = uid_index.get(tid)

    if relation == 'followers':
        if sid_idx is None or tid_idx is None:
            continue
        edge_index.append([sid_idx, tid_idx])
        edge_type.append(0)
    elif relation=='following':
        if sid_idx is None or tid_idx is None:
            continue
        edge_index.append([sid_idx, tid_idx])
        edge_type.append(1)
    elif relation == 'own':
        if sid_idx is None:
            continue
        if tid not in list_membership:
            list_membership[tid] = {'creator': [], 'members': []}
        list_membership[tid]['creator'].append(sid_idx)
    elif relation in ['followed', 'membership']:
        if tid_idx is None:
            continue
        if sid not in list_membership:
            list_membership[sid] = {'creator': [], 'members': []}
        list_membership[sid]['members'].append(tid_idx)

# Create relation 2: Ownership
for list_id, roles in list_membership.items():
    for creator in roles['creator']:
        for member in roles['members']:
            edge_index.append([creator, member])
            edge_type.append(2)

os.makedirs('processed_data', exist_ok=True)
torch.save(torch.LongTensor(edge_index).t(), './processed_data/edge_index.pt')
torch.save(torch.LongTensor(edge_type), './processed_data/edge_type.pt')