# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 08:52:46 2020

@author: MHerzo
"""

from os import path as osp

def test_dir_name_mgr():
    dnm = DirNameMgr(r'c:\tmp')
    dnm.export_annot_dir = 'xx_annot_dir_name_yy'
    dnm.img_basename = 'aa_img_basename_bb'
    print(dnm.export_img)
    
    dnm2 = DirNameMgr(r'c:\tmp2')
    print(dnm2.export_annot_dir, dnm2.img_basename)    

#    
# class DirNameMgr
#
# Manage directories and names of the 5 possible sets of images
# 
# Structure:
# 
# export_root
# - annotation_exports
#       <images of entire tissue pieces with all annotations (across all label types)>
# - annotation_regions_single
#       - label1
#           <area of tissue where each instance of label1 resides - no annotation>
#       - label2
#           <area of tissue where each instance of label2 resides - no annotation>
#       ...
# - annotation_exports_single
#       - label1
#           <area of tissue where each instance of label1 resides with annotation>
#       - label2
#           <area of tissue where each instance of label2 resides with annotation>
#       ...
# - annotation_masks
#       - label1
#           <image of entire tissue piece with masks for all instances of label1>
#       - label2
#           <image of entire tissue piece with masks for all instances of label2>
#       ...
# - annotation_masks_single
#       - label1
#           <image of area of tissue where each instance of label1 resides, with mask>
#       - label2
#           <image of area of tissue where each instance of label2 resides, with mask>
#       ...
#
# Usage
#   1.  Create object
#   2.  For each image, set `img_basename`
#
# E.g. 
#  
#   dnm = DirNameMgr(r'c:\tmp')
#   for img_path in img_path_list:
#       dnm.set_img_basename(img_path)

class DirNameMgr():
    
    export_root = None
    img_basename = None
    label_name = None
    label_instance = 0
   
    def __init__(self, label_dir, export_root=None):

        self.module_folder = osp.dirname(__file__)

        self.label_dir = label_dir
        if export_root:
            self.export_root = export_root
        else:
            self.export_root = osp.join(label_dir, '..','..','util','export_images')

        self.export_img_dir = osp.join(self.export_root,'annotation_exports')
        self.export_annot_dir = osp.join(self.export_root,'annotation_exports_single')
        self.export_annot_region_dir = osp.join(self.export_root,'annotation_regions_single')
        self.export_img_mask_dir = osp.join(self.export_root,'annotation_masks')
        self.export_annot_mask_dir = osp.join(self.export_root,'annotation_masks_single')
        
    def set_img_basename(self, img_path):
        self.img_basename = osp.basename(img_path)

    @property
    def img_basestem(self):
        return osp.splitext(self.img_basename)[0]

    @property
    def img_extn(self):
        return osp.splitext(self.img_basename)[1]
    

    @property
    def label_clean(self):
        label_clean = self.label_name
        if label_clean:
            label_clean = label_clean.replace('/','')
            label_clean = label_clean.replace('\\','')
        else:
            label_clean = ''
        return label_clean

    # All annotations on the image
    @property
    def export_img(self):
        dir_info = {}
        dir_info['basestem'] = self.img_basestem
        dir_info['basename'] = self.img_basestem + '_export.png'
        dir_info['path'] = osp.join(self.export_img_dir,dir_info['basename'])
        return dir_info

    # Masks for all annotations on the image
    @property
    def export_img_mask(self):
        dir_info = {}
        dir_info['basestem'] = self.img_basestem + '_mask'
        dir_info['basename'] = dir_info['basestem'] + '_' + self.label_clean + '.png'
        dir_info['path'] = osp.join(self.export_img_mask_dir,
                                    self.label_clean, 
                                    dir_info['basename'])
        return dir_info

    # Tissue region of single annotation, no annotation
    @property
    def export_annot_region(self):
        dir_info = {}
        dir_info['basestem'] = self.img_basestem + '_export'
        dir_info['basename'] = dir_info['basestem'] + '_' + self.label_clean + str(self.label_instance) + '.png'
        dir_info['path'] = osp.join(self.export_annot_region_dir,self.label_clean,dir_info['basename'])
        return dir_info


    # Single annotation on the image
    @property
    def export_annot(self):
        dir_info = {}
        dir_info['basestem'] = self.img_basestem + '_export'
        dir_info['basename'] = dir_info['basestem'] + '_' + self.label_clean + str(self.label_instance) + '_annot.png'
        dir_info['path'] = osp.join(self.export_annot_dir,self.label_clean, dir_info['basename'])
        return dir_info

    # Mask of single annotation on the image
    @property
    def export_annot_mask(self):
        dir_info = {}
        dir_info['basestem'] = self.img_basestem + '_mask'
        dir_info['basename'] = dir_info['basestem'] + '_' + self.label_clean + str(self.label_instance) + '.png'
        dir_info['path'] = osp.join(self.export_annot_mask_dir,self.label_clean,dir_info['basename'])
        return dir_info



if __name__ == '__main__':
    test_dir_name_mgr()