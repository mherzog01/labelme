# -*- coding: utf-8 -*-
"""

For each annotation on an image, generates a .png image 
and a .json file for that annotation

@author: MHerzo


Assumptions
1.  Images are in a single folder, or the list of images is unique by image basename
2.  Dataframe of annotations (df_annot) is generated at the same time that the annotated images (.png files) are generated.  See below for details.
"""


from os import path as osp
import glob
import labelme
import os
from labelme import user_extns
from labelme.shape import Shape
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from PIL import Image
import sys
import imgviz
import numpy as np
import string
import shutil
import datetime
import pandas as pd

#------------------------------------------
# Settings
module_folder = osp.dirname(__file__)
export_folder = osp.join(module_folder, 'annotation_exports_single')
#label_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\Annot\Ground Truth'
label_dir = r'c:\tmp\work4'
selection_margin = 100  # Number of pixels that surround the selected area of the image
create_img_exports = ['all','new','none'][1]  
#------------------------------------------

annotation_color = QtGui.QColor(0,0,0)



app = QtWidgets.QApplication(sys.argv)
    
img_num = -1
for img_path in glob.glob(osp.join(label_dir,"*.bmp")):
    
    img_basename = osp.basename(img_path)

    #img_basename = r'20200213-154422-Img - Test.bmp'
    img_num += 1
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Image={img_basename}')
    
    img_basestem, img_ext = osp.splitext(img_basename)

    label_file = user_extns.imgFileToLabelFileName(img_basename, label_dir)
    labelFile = labelme.LabelFile(label_file, loadImage=False)    
    
    img_pixmap = QtGui.QPixmap(img_path)
    img_shape = [img_pixmap.size().width(),img_pixmap.size().height()]

    # Paint annotations
    # TODO Centralize annotation painting logic -- it exists here and several other places (app.exportMasks, etc.).  Use util/shape_to_mask or examples/.../draw_json.py
    # TODO don't paint if 'create_image' == False
    shapes_to_export = labelFile.shapes
    df_shapes = pd.DataFrame([(shape['label'],shape) for shape in shapes_to_export], columns=['label','shape'])
    df_shapes = df_shapes.sort_values(['label'])
    # https://stackoverflow.com/questions/37997668/pandas-number-rows-within-group-in-increasing-order
    df_shapes['idx'] = df_shapes.groupby('label').cumcount()+1
    df_shapes.set_index(['label','idx'],inplace=True)
    for label, annot_idx in df_shapes.index:
        s = df_shapes.loc[(label,annot_idx)]['shape']
        s_obj = Shape(label=s['label'], shape_type=s['shape_type'],
          flags=s['flags'], group_id=s['group_id'])
        first_pt_q = None
        # TODO More pythonic way of handing min/max x/y
        min_w, max_w, min_h, max_h = (img_shape[0],0,img_shape[1],0)
        for pt in s['points']:
            pt_q = QtCore.QPointF(pt[0],pt[1])
            if not first_pt_q:
                first_pt_q = pt_q
            s_obj.addPoint(pt_q)
            min_w = min(min_w, pt[0])
            max_w = max(max_w, pt[0])
            min_h = min(min_h, pt[1])
            max_h = max(max_h, pt[1])
        s_obj.addPoint(first_pt_q)
        #s_obj.close = True
        s_obj.fill = False
        s_obj.point_size = 0
        # TODO Get the scale value more intelligently?  canvas.scale -> widget scale factor via canvas.update?
        s_obj.scale = 1 / 2
        s_obj.line_color = annotation_color

        # Get bounding region of image.  ll = Lower Left, ur = Upper Right
        roi_ll = (max(0,min_w - selection_margin), min(img_shape[1],max_h + selection_margin))
        roi_ur = (min(img_shape[0],max_w + selection_margin), max(0,min_h - selection_margin))
        
        img_div_width = roi_ur[0] - roi_ll[0]
        img_div_height = roi_ll[1] - roi_ur[1]
        
        margin_top = roi_ur[1]
        margin_left = roi_ll[0]
    
        export_basename = f'{img_basestem}_export_{s_obj.label}_{annot_idx}.png'
        export_path = osp.join(export_folder,export_basename)
        
        if create_img_exports == 'all':
            create_image = True
        elif create_img_exports == 'none':
            create_image = False
        elif create_img_exports == 'new':
            create_image = not osp.exists(export_path)        
    
        # Delete files one at a time to allow updates of individual files
        if create_image and osp.exists(export_path):
            os.remove(export_path)
                
        if create_image:
            # https://stackoverflow.com/questions/25795380/how-to-crop-a-image-and-save
            roi_ll_q = QtCore.QPoint(margin_left,margin_top)
            roi_q = QtCore.QRect(roi_ll_q,QtCore.QSize(img_div_width,img_div_height))
            pixmap = img_pixmap.copy(roi_q)
            disp_annot_on_img=False
            if disp_annot_on_img:
                points_tmp = []
                for pt_q in s_obj.points:
                    points_tmp += [pt_q - roi_ll_q]
                s_obj.points = points_tmp
                p = QtGui.QPainter(pixmap)
                s_obj.paint(p)
                p.end()
            pixmap.save(export_path)
        
        # Delete/add .json

# TODO * Handle errors - clean up painter 