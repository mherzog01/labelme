# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 16:23:19 2020

@author: MHerzo

Export the mask of a given label.  For an image, create a single mask which has all instances of the label of interest.

Process
- Get config
* As of date
* Mode settings (dev/prod, create flags, export folder prefix)
* Annotation of interest

- For each annotation file, determine if contians annotation of interest, and was modified on or after the As Of date.
- If so, export mask
- Create folder structure:
        /ML/exports/<YYYYMMDD-01>/<label name>_mask (folder prefix)

Notes
1.  If multiple labels are present on an image, export mask for just the one of interest.  Model will train to recognize 
    label of interest, even if it is also present with other features.

Assumptions
1.  Images are in a single folder, or the list of images is unique by image basename
2.  .json file for images (if it exists), is in the same folder as the image

TODO:
1.  Copied from rpt01_gen.py.  Create shared objects (e.g. setup of settings)
2.  Use file_suffix in classes.json instead of calculating label_clean in DirNameMgr
"""


from os import path as osp
import glob
import os

from labelme import user_extns
from labelme import LabelFile
from labelme.shape import Shape
from labelme.user_extns.annot_export.dir_name_mgr import DirNameMgr

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from PIL import Image

import sys
import numpy as np
import datetime
import json
import traceback
from matplotlib import pyplot as plt

def get_defect_intensity(group_id):
    return str(group_id) if not group_id == float('nan') else 'None'

def save_subfolder(pixmap, dir_names):
    targ_dir = osp.dirname(dir_names['path'])
    if not osp.exists(targ_dir):
        try:
            os.mkdir(targ_dir)
        except Exception as e:
            print(f'ERROR:  Unable to create directory={targ_dir}')
            traceback.print_exc()
            raise e
    pixmap.save(dir_names['path'])

def disp_imgs(images):
    plt.figure(figsize=(15, 15))
    title = ['Input Image', 'True Mask']
    for idx, img in enumerate(images):
        if images[idx] is None:
          continue
        plt.subplot(1, len(images), idx+1)
        plt.title(title[idx])
        plt.imshow(images[idx])
        plt.axis('off')
    plt.show()

def pixmap2np(pixmap):
    # https://stackoverflow.com/questions/45020672/convert-pyqt5-qpixmap-to-numpy-ndarray
    image = pixmap.toImage()
    w,h = image.width(), image.height()
    num_bytes = image.byteCount()
    num_channels = 4
    assert num_channels == (num_bytes / w / h)
    s = image.bits().asstring(w * h * num_channels)
    arr = np.frombuffer(s, dtype=np.uint8).reshape((h, w, num_channels))
    return arr

#------------------------------------------
# Settings
run_mode = ['DEV','PROD'][1]
as_of_date = datetime.datetime.strptime('8/28/2020', '%m/%d/%Y')  # As of date - process only changes on or after this date
create_img_masks = ['all','new','none'][0]  
label_of_interest = 'Tissue boundary'

if run_mode == 'PROD':
    label_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\Annot\Tech M Herzog'
    classes_file_path = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\cfg\classes.json'
    export_root =  r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\ML\exports'
else:
    # TODO Fix all of these -- Box Sync and export_root may not be correct for Dev
    label_dir = r'C:\Users\mherzo\Box Sync\Herzog_Michael - Personal Folder\2020\Machine Vision Misc\Image Annotation\Annot\Ground Truth'
    classes_file_path = r'C:\Users\mherzo\Box Sync\Herzog_Michael - Personal Folder\2020\Machine Vision Misc\Image Annotation\classes.json'
    export_root = r'c:\Tmp\work1\ML\exports' 
export_folder_name = as_of_date.strftime('%Y-%m-%d') + '-01'
export_folder_path = osp.join(export_root, export_folder_name)  # Masks will be placed in a subfolder of this path

num_to_disp = 0   # Set to 0 or less to disable
#------------------------------------------

# Needed to paint shapes
app = QtWidgets.QApplication(sys.argv)
    
dnm = DirNameMgr(label_dir, export_root=export_root)
if not osp.exists(export_root):
    os.mkdir(export_root)
if not osp.exists(dnm.export_img_mask_dir):
    os.mkdir(dnm.export_img_mask_dir)

if create_img_masks != 'none':
    if not osp.exists(classes_file_path):
        print(f'ERROR:  Need to create masks, but can\'t find classes file {classes_file_path}')
        raise ValueError
    else:
        with open(classes_file_path,'r') as f:
            classes = json.load(f)
            label_to_class = {classes[c]['name']:c for c in classes}


img_num = -1
num_displayed = 0
for file_stat in os.scandir(label_dir):
    
    if osp.splitext(file_stat.name)[1] != '.json':
        continue
    
    mdate = datetime.datetime.fromtimestamp(file_stat.stat().st_mtime)
    if mdate < as_of_date:
        continue
    
    label_file_path = file_stat.path
    label_file = LabelFile(label_file_path, loadImage=False) 
    
    label_list = [s['label'] for s in label_file.shapes]
    
    if not label_of_interest in label_list:
        continue
    
    dnm.set_img_basename(label_file_path)
    img_basename = dnm.img_basename
    
    img_num += 1
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Image={img_num}: {img_basename}')

    if create_img_masks == 'all':
        for file in glob.glob(osp.join(dnm.export_img_mask_dir,'**',dnm.export_img_mask['basestem'] + '*.png'), recursive=True):
            os.remove(file)
        create_image_mask = True
    elif create_img_masks == 'none':
        create_image_mask = False
    elif create_img_masks == 'new':
        create_image_mask = None
    else:
        print(f'Invalid value for create_img_masks={create_img_masks}')

    # TODO Create more friendly way of getting image path from label_file
    img_path = label_file.imagePath
    if not osp.exists(img_path):
        img_path = osp.join(osp.dirname(label_file_path),img_path)
    if not osp.exists(img_path):
        print(f'Error:  unable to get image {img_path} from {label_file_path} and {label_file.imagePath}.')
    img_pixmap = QtGui.QPixmap(img_path)
    #img_pixmap_orig = img_pixmap.copy()
    img_size = img_pixmap.size()
   
    # ----------------------------------------- 
    # Paint and save entire tissue images
    #
    # Process in groups by label for masks
    #
    # Note:  This loop is not strictly needed as we are only processing one label.
    #        However, leave it in case we want to process more than one label in the future
    # ----------------------------------------- 
    #masks = {}
    for label in label_list:
        
        if not label == label_of_interest:
            continue
        
        img_pixmap_mask = QtGui.QPixmap(img_size)   # Empty -- all pixels have value (0,0,0)
        p_img_mask = QtGui.QPainter(img_pixmap_mask)

        dnm.label_name = label
        
        #p_img = QtGui.QPainter(img_pixmap)
        class_color_value = int(label_to_class[label])
        color = QtGui.QColor(*([class_color_value] * 3))

        for s_dict in label_file.shapes:
            
            s_obj = user_extns.shape_dict_to_obj(s_dict)
            
            if not hasattr(s_obj,'label'):
                continue
            
            first_pt_q = None
            for pt in s_obj.points:
                if not first_pt_q:
                    first_pt_q = pt
            s_obj.addPoint(first_pt_q)
            #s_obj.close = True
            s_obj.fill = False
            s_obj.point_size = 0
            # TODO - draw text label and shape # of annotation next to shape
            # TODO Get the scale value more intelligently?  canvas.scale -> widget scale factor via canvas.update?
            s_obj.scale = 1 / 2
            s_obj.line_color = color
            #s_obj.paint(p_img)
            
            s_obj.fill = True
            s_obj.line_color = color
            s_obj.fill_color = color
            #print(f'Painting {row["image_basename"]}, label={row["label"]}, label_instance={row["label_instance"]}, color={color.getRgb()}')
            s_obj.paint(p_img_mask)
        p_img_mask.end()
            
        if label in label_to_class:
            mask_path = dnm.export_img_mask['path']
            if create_img_masks == 'new':
                create_image_mask = not osp.exists(mask_path)
            if create_image_mask:
                save_subfolder(img_pixmap_mask, dnm.export_img_mask)
        #masks[label] = img_pixmap_mask
        
    # TODO Not clear if need to end painters
    #p_img.end()
    
    if num_displayed < num_to_disp:
        num_displayed += 1
        # https://stackoverflow.com/questions/45020672/convert-pyqt5-qpixmap-to-numpy-ndarray
        #img_np = pixmap2np(img_pixmap_orig)
        #mask_np = pixmap2np(img_pixmap_mask)
        img = Image.open(img_path)
        img_np = np.asarray(img)
        mask = Image.open(mask_path)
        mask_np = np.asarray(mask)
        mask_s = set(mask_np.ravel())
        mask_np_norm = (mask_np == max(mask_s)).astype(np.float32)
        print(f'Image {img_num}.  Mask values={mask_s}')
        disp_imgs([img_np, mask_np_norm])


print('Process complete.  Deploy images to Drive.')
# TODO Process does not release memory    
del app
del plt
