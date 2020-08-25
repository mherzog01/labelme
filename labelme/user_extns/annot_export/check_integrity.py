# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 10:26:27 2020

@author: MHerzo
"""

import glob
from os import path as osp
import os

# TODO Make part of DirNameMgr?

def get_file_list(folder):
    file_list = glob.glob(osp.join(root_dir,folder,'**','*'), recursive=True)
    file_list = [file.replace(osp.join(root_dir,folder),'') for file in file_list if osp.isfile(file)]
    file_list = sorted(file_list)
    print(f'{folder}={len(file_list)}')
    #print(file_list[1])
    return file_list

def reduce_name(folder, in_path):
    out_path = in_path
    if folder == 'annotation_exports_single':
        out_path = out_path.replace('','')
    elif folder == 'annotation_exports':
        out_path = out_path.replace('','')
    elif folder == 'annotation_regions_single':
        out_path = out_path.replace('','')
    elif folder == 'annotation_masks':
        out_path = out_path.replace('','')
    elif folder == 'annotation_masks_single':
        out_path = out_path.replace('','')
    return out_path
    
def get_folders():
    in_folders = glob.glob(osp.join(root_dir,'*'))    
    out_folders = []
    for in_folder in in_folders:
        out_folder = in_folder.replace(root_dir,'')
        folders_split = out_folder.split(os.sep)
        out_folders += [folders_split[-1]]
    return out_folders
    
root_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\util\export_images'
subfolders = ['annotation_exports_single',
              'annotation_exports',
              'annotation_regions_single',
              'annotation_masks',
              'annotation_masks_single']

annot_single_l = get_file_list('annotation_exports_single')
masks_single_l = get_file_list('annotation_masks_single')
region_single_l = get_file_list('annotation_regions_single')

#\Bubbles\20200302-144509-Img_export_Bubbles1_annot.png
#\Bubbles\20200302-144509-Img_mask_Bubbles1.png
#\Bubbles\20200302-144509-Img_export_Bubbles1.png
annot_s_reduced_l = [file.replace('export_','').replace('_annot','') for file in annot_single_l]
masks_s_reduced_l = [file.replace('mask_','') for file in masks_single_l]
region_reduced_l = [file.replace('export_','') for file in region_single_l]

diff = set(annot_s_reduced_l).symmetric_difference(masks_s_reduced_l)
print(f'Num diff={len(diff)}')   

# Pipeline design:
# 1.  List all images in 'region'
# 2.  Get mask of region
# 3.  Get label of image
# 4.  Create tf.Dataset

# TODO Ensure 'region' has all of annot and masks 
# TODO Ensure images are unique by just basename -- don't need folder

all_files = annot_single_l + masks_single_l + region_single_l
all_basenames = [osp.basename(f) for f in all_files]
dups = [b for b in all_basenames if all_basenames.count(b) > 1]
if dups:
    print(f'Dupicates found:  {dups}')
else:
    print('No duplicates by basename found')    

xref = {e:{} for e in region_reduced_l}

# TODO ** key is region image (no folder name)
for k,v in zip(annot_s_reduced_l,annot_single_l):
    xref[k]['annot'] = v

for k,v in zip(masks_s_reduced_l,masks_single_l):
    xref[k]['masks'] = v
    
for k,v in zip(region_reduced_l,region_single_l):
    xref[k]['region'] = v
    
print('\nNo Mask:')    
for k in xref:
    if not 'masks' in xref[k].keys(): 
        print(k)    
