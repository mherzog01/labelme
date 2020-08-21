# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 13:55:07 2020

@author: MHerzo
"""

import glob
import json

label_count = {}
for file in glob.glob(r'M:\MSA\Annot\Ground Truth\*.json'):
    with open(file,'r') as f:
        json_data = json.load(f)
    labels = set([shape['label'] for shape in json_data['shapes']])
    has_label = False
    for label in ['No Dermis', 'No dermis']:
        if label in labels:
            has_label = True
        else:
            continue
    if has_label:
        print(label, file)
        if label in label_count:
            label_count[label] +=1
        else:
            label_count[label] = 1
print(label_count)