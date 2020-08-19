# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 16:23:19 2020

@author: MHerzo

Create a report for browsing annotation details.

- For each image, generate an image with the annotations on it.

- For each annotation on an image, generates a .png image 
  and a .json file for that annotation

- Generate HTML file which displays an image of each annotation, with the ability to view
  an image of the entire piece of tissue, with or without annotations


Assumptions
1.  Images are in a single folder, or the list of images is unique by image basename
2.  .json file for images (if it exists), is in the same folder as the image

TODO *** Scan entire list below for priority tasks
1. Improve performance of report generation - save to a different format than .png
1.1 Improve performance/cleanthliness of HTML
- Use styles, not object-level HTML (e.g. onclick)
- Break into separate files
1.2 * Don't output full paths for each entry in tissue and annot arrays.  Instead, place the folder names in arrays/vars and use JavaScript to construct a path to the image.
2. If click on image text, select whole image name
3. **Display of defects, ensure some value is shown.  E.g. 20200306-154951-Img.bmp, Annot #7 - center and point on circle are the same:
        {
      "label": "Residual Epi",
      "points": [
        [
          2688.0,
          1640.625
        ],
        [
          2688.0,
          1640.625
        ]
      ],
      "group_id": 5,
      "shape_type": "circle",
      "flags": {
        "Rework": true,
        "Not in picture": false,
        "Not in tissue": false,
        "Review recommended": false
      }
    },
4.  Compute and display area of each annotation
5.  Create map for each image - hover over each annotation and see different values
6.  Double click on defect and launch LabelMe for that image
7.  * In last section, images with no defects are not displayed.  nan is shown instead.
8.  Change name from /util to /reports
10.  Display lot number.  Requires using database -- centralize annotations with data set?
11. Comments
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
import json
import traceback

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

def test_dir_name_mgr():
    dnm = DirNameMgr()
    dnm.subdir_name = 'xx_subdir_name_yy'
    dnm.img_basename = 'aa_img_basename_bb'
    print(dnm.export_img)
    
    dnm2 = DirNameMgr()
    print(dnm2.subdir_name, dnm2.img_basename)    
    
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
class DirNameMgr():
    
    export_root = None
    img_basename = None
    label_name = None
    label_instance = 0
   
    def __init__(self, label_dir):

        self.module_folder = osp.dirname(__file__)

        self.label_dir = label_dir
        self.export_root = osp.join(label_dir, '..','..','util','export_images')

        self.export_img_dir = osp.join(self.export_root,'annotation_exports')
        self.export_annot_dir = osp.join(self.export_root,'annotation_exports_single')
        self.export_annot_region_dir = osp.join(self.export_root,'annotation_regions_single')
        self.export_img_mask_dir = osp.join(self.export_root,'annotation_masks')
        self.export_annot_mask_dir = osp.join(self.export_root,'annotation_masks_single')

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


#------------------------------------------
# Settings
run_mode = ['DEV','PROD'][0]
create_img_exports = ['all','new','none'][1]  
create_annot_exports = [ 'all','new','none'][1]
create_img_masks = ['all','new','none'][0]  
create_annot_masks = [ 'all','new','none'][0]
selection_margin = 100  # Number of pixels that surround the selected area of the image
if run_mode == 'PROD':
    label_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\Annot\Ground Truth'
    classes_file_path = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\cfg\classes.txt'
else:
    label_dir = r'C:\Users\mherzo\Box Sync\Herzog_Michael - Personal Folder\2020\Machine Vision Misc\Image Annotation\Annot\Ground Truth'
    classes_file_path = r'C:\Users\mherzo\Box Sync\Herzog_Michael - Personal Folder\2020\Machine Vision Misc\Image Annotation\classes.txt'

rpt_basename = 'rpt01.html'
run_rpt = [True,False][0]
#------------------------------------------
    
dnm = DirNameMgr(label_dir)
template_path = osp.join(dnm.module_folder,'rpt01_template.html')

if create_img_masks != 'none' or create_annot_masks != 'none':
    if not osp.exists(classes_file_path):
        print(f'ERROR:  Need to create masks, but can\'t find classes file {classes_file_path}')
        raise ValueError
    else:
        with open(classes_file_path,'r') as f:
            classes = json.load(f)
            label_to_class = {classes[c]['name']:c for c in classes}

# The report depends on current state of image annotations, so prior versions may not have integrity
#rpt_stem = 'rpt01'
#rpt_name = f'{rpt_stem}_{datetime.datetime.now():%Y%M%D_%h%m%s}.html'
rpt_path = osp.join(dnm.export_root, rpt_basename)

LABEL_COLORMAP = user_extns.get_colormap()
num_colors = len(LABEL_COLORMAP)


image_dict = {} # Xref images of entire tissue with and without annotations
annot_dict = {} # Xref images of individual annotations with and without annotation boundaries displayed

obj_annots = user_extns.AnnotDf()
df_annot = obj_annots.df_annot
df_annot['divs'] = ''
df_annot['label_instance'] = None
df_annot['label_instance'].astype(int)

# Needed to paint shapes
app = QtWidgets.QApplication(sys.argv)
    
label_colors = {}
img_num = -1
for img_path in glob.glob(osp.join(label_dir,"*.bmp")):
    
    img_num += 1

    obj_annots.load_files(img_path)
    img_basename = obj_annots.cur_image_basename
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Image={img_num}: {img_basename}')
    
    dnm.img_basename = img_basename
    
    if not obj_annots.cur_image_shapes:
        continue
    
    if create_img_exports == 'all':
        create_image = True
    elif create_img_exports == 'none':
        create_image = False
    elif create_img_exports == 'new':
        create_image = not osp.exists(dnm.export_img['path'])        
    else:
        print(f'Invalid value for create_img_exports={create_img_exports}')

    if create_img_masks == 'all':
        for file in glob.glob(osp.join(dnm.export_img_mask_dir,'**',dnm.export_img_mask['basestem'],'*.png'), recursive=True):
            os.remove(file)
        create_image_mask = True
    elif create_img_masks == 'none':
        create_image_mask = False
    elif create_img_masks == 'new':
        create_image_mask = None
    else:
        print(f'Invalid value for create_img_masks={create_img_masks}')

    image_dict[img_num] = [img_path, dnm.export_img['path']]
    
    # Delete files one at a time to allow updates of individual files
    if create_image and osp.exists(dnm.export_img['path']):
        os.remove(dnm.export_img['path'])
    
    img_pixmap = QtGui.QPixmap(img_path)
    img_pixmap_orig = img_pixmap.copy()
    img_size = img_pixmap.size()
    img_pixmap_mask = QtGui.QPixmap(img_size)   # Empty -- all pixels have value (0,0,0)

    # Organize images by label/annotation instance
    # To avoid dealing with different representations of path separators, use the base name
    df_shapes = df_annot.query(f'`image_basename` == "{img_basename}"')
    # https://stackoverflow.com/questions/37997668/pandas-number-rows-within-group-in-increasing-order
    df_grp = df_shapes.groupby('label').cumcount()+1
    for idx in df_grp.index:
        df_annot.loc[idx,'label_instance'] = df_grp.loc[idx]
    # Requery -- df_shapes may not be a view
    df_shapes = df_annot.query(f'`image_basename` == "{img_basename}"').sort_values(['label','image_basename','label_instance'])
    
    # Paint annotations
    # TODO Centralize annotation painting logic -- it exists here and several other places (app.exportMasks, etc.).  Use util/shape_to_mask or examples/.../draw_json.py
    # TODO don't paint if 'create_image' == False and 'create_annot' == False.  However, if create_annot_exports == 'new', 'create_annot' is set below 
    p_img = QtGui.QPainter(img_pixmap)
   
    # ----------------------------------------- 
    # Paint and save entire tissue images
    # ----------------------------------------- 
    prev_label = None
    for idx in df_shapes.index:
        row = df_shapes.loc[idx]
        s_obj = row['shape_obj']  
        if not hasattr(s_obj,'label'):
            continue
        label = s_obj.label
        dnm.label_name = label
        dnm.label_instance = row['label_instance']

        # TODO *Make colors consistent with labelMe
        if label and not label in label_colors:
            label_colors[s_obj.label] = QtGui.QColor(*LABEL_COLORMAP[len(label_colors) % num_colors])
        
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
        s_obj.line_color = label_colors[s_obj.label]
        s_obj.paint(p_img)
        
        s_obj.fill = True
        if s_obj.label in label_to_class:
            if create_img_masks == 'new':
                create_image_mask = not osp.exists(dnm.export_img_mask['path'])
            if not prev_label or prev_label != s_obj.label:
                p_img_mask = QtGui.QPainter(img_pixmap_mask)
                if prev_label:
                    if create_image_mask:
                        save_subfolder(img_pixmap_mask, prev_dnm_info)
                    p_img_mask.end()
                prev_label = s_obj.label
                prev_dnm_info = dnm.export_img_mask.copy()
            class_color_value = label_to_class[s_obj.label]
            color = QtGui.QColor(*[int(class_color_value)]*3)
            s_obj.line_color = color
            s_obj.fill_color = color
            s_obj.paint(p_img_mask)
        else:
            create_image_mask = False
    if prev_label and create_image_mask:
        save_subfolder(img_pixmap_mask, dnm.export_img_mask)
        p_img_mask.end()
    if create_image:
        img_pixmap.save(dnm.export_img['path'])

    # TODO Not clear if need to end painters
    p_img.end()

    # ----------------------------------------- 
    # Create annotation-level images
    #
    # Do so after creating tissue-level images, so annotation exports get all annotations in the regions being exported
    # ----------------------------------------- 
    # Delete all annotations of the image along with the tissue region export, if desired
    if create_annot_exports == 'all':
        for file in glob.glob(osp.join(dnm.export_annot_dir,'**',dnm.export_annot['basestem'],'*.png'), recursive=True):
            os.remove(file)
        for file in glob.glob(osp.join(dnm.export_annot_region_dir,'**',dnm.export_annot_region['basestem'],'*.png'), recursive=True):
            os.remove(file)
        create_annot_images = True
    elif create_annot_exports == 'none':
        create_annot_images = False
    elif create_annot_exports == 'new':
        # create_annot_images will be set in logic below for each annotation
        create_annot_images = None
    else:
        print(f'Invalid value for create_annot_exports={create_annot_exports}')

    if create_annot_masks == 'all':
        for file in glob.glob(osp.join(dnm.export_annot_mask_dir,'**',dnm.export_annot_mask['basestem'],'*.png'), recursive=True):
            os.remove(file)
        create_annot_mask = True
    elif create_annot_masks == 'none':
        create_annot_mask = False
    elif create_annot_masks == 'new':
        # create_annot_mask will be set in logic below for each annotation
        create_annot_mask = None
    else:
        print(f'Invalid value for create_annot_masks={create_annot_masks}')

    # For each tissue region, export needed annotations/regions
    for idx in df_shapes.index:
        row = df_shapes.loc[idx]
        annot_num = row['annot_num']  # Unique within an image
        annot_id = row.name # Unique identifier across all annotations in report
        s_obj = row['shape_obj']  
        if not hasattr(s_obj,'label'):
            continue
        label = s_obj.label
        dnm.label_name = label
        dnm.label_instance = row['label_instance']

        # TODO More pythonic way of handing min/max x/y
        min_w, max_w, min_h, max_h = (img_size.width(),0,img_size.height(),0)
        for pt in s_obj.points:
            #pt_q = QtCore.QPointF(pt[0],pt[1])
            #pt_q_list += [pt_q]
            min_w = min(min_w, pt.x())
            max_w = max(max_w, pt.x())
            min_h = min(min_h, pt.y())
            max_h = max(max_h, pt.y())
        
        # Get bounding region of image.  ll = Lower Left, ur = Upper Right
        roi_ll = (max(0,min_w - selection_margin), min(img_size.height(),max_h + selection_margin))
        roi_ur = (min(img_size.width(),max_w + selection_margin), max(0,min_h - selection_margin))
        
        # Add to image_divs
        img_div_width = roi_ur[0] - roi_ll[0]
        img_div_height = roi_ll[1] - roi_ur[1]
        
        margin_top = roi_ur[1]
        margin_left = roi_ll[0]
        
        # ------------------
        # Create images for the annotation
        # ------------------
        if create_annot_exports == 'new':
            if osp.exists(dnm.export_annot['path']) and osp.exists(dnm.export_annot_region['path']):
                create_annot_images = False
            else:
                create_annot_images = True            
                
        if create_annot_masks == 'new':
            if osp.exists(dnm.export_annot_mask['path']):
                create_annot_mask = False
            else:
                create_annot_mask = True            
                
        roi_ll_q = QtCore.QPoint(margin_left,margin_top)
        roi_q = QtCore.QRect(roi_ll_q,QtCore.QSize(img_div_width,img_div_height))

        if create_annot_images:
            # https://stackoverflow.com/questions/25795380/how-to-crop-a-image-and-save

            # Unannotated image
            annot_pixmap = img_pixmap_orig.copy(roi_q)
            save_subfolder(annot_pixmap, dnm.export_annot_region)

            # Annotated image
            annot_pixmap_a = img_pixmap.copy(roi_q)
            
            # No need to annotate again.  Already done on tissue image.
            # disp_annot_on_img = True
            # if disp_annot_on_img:
            #     points_tmp = []
            #     for pt_q in s_obj.points:
            #         points_tmp += [pt_q - roi_ll_q]
            #     s_obj.points = points_tmp
            #     p_annot = QtGui.QPainter(annot_pixmap)
            #     s_obj.paint(p_annot)
            #     p_annot.end()
            save_subfolder(annot_pixmap_a, dnm.export_annot)
            
        if create_annot_mask:
            annot_pixmap_mask = img_pixmap_mask.copy(roi_q)
            save_subfolder(annot_pixmap_mask, dnm.export_annot_mask)
            

        annot_dict[annot_id] = [dnm.export_annot_region['path'], dnm.export_annot['path']]
        
        # ------------------
        # Construct and store the HTML for the divs
        # ------------------

        img_id = f'annot_{annot_id}'
        
        image_divs = ''
        image_divs += f'<div class="disp_img">\n'
        image_divs += f'  <div '
        image_divs += f'       onclick="getimage(\'{img_id}\',{annot_id})"'
        image_divs += f'       title="{s_obj.label}, Intensity: {get_defect_intensity(s_obj.group_id)}, {img_basename}">\n'
        image_divs +=  '    <img id="{2}" src="{0}" alt="{0} {1}">\n'.format(dnm.export_annot['path'],s_obj.label,img_id)
        image_divs += f'  </div>\n'
        image_divs += f'  <div style="height:5"></div>\n'
        image_divs += f'  <div style="width:{img_div_width}">\n'
        image_divs += f'    {img_basename}, {annot_num} <a onclick="show_tissue_img(\'{img_id}\',{annot_id},{img_num})" href="javascript:void">Show</a>\n'
        if any(s_obj.flags.values()):
            image_divs += f'    <br>{", ".join([key for key in s_obj.flags if s_obj.flags[key]])}\n'
        image_divs += f'    <div style="height:10"></div>\n'
        image_divs += f' </div>\n'
        image_divs += f' </div>\n'

        df_annot.loc[idx,'divs'] = image_divs
    

# ------------------------------------------------
# Set up variables for Template substitution
# ------------------------------------------------
if run_rpt:
    df_annot_sort = df_annot.sort_values(['label','group_id','image_basename','annot_num'])
    
    # Table of contents (by label)
    toc = ''
    for cur_label in df_annot_sort['label'].unique():
        toc += f'<div style="margin-left:20px"><a href="#{cur_label}">{cur_label}</a></div>\n'
    
    # Divs
    image_divs = ''
    prev_label = None
    prev_grp = None
    first_label = True
    for idx in df_annot_sort.index:
        row = df_annot_sort.loc[idx]
        cur_label = row['label']
        cur_grp = row['group_id']
        if not prev_label or prev_label != cur_label:
            image_divs += f'<h2 id="{cur_label}">{cur_label}</h2>\n'
            if first_label:
                first_label = False
            else:
                image_divs += f'<a href="#top">Top</a>\n'
            prev_label = cur_label
            prev_grp = None
            new_label = True
        else:
            new_label = False
        if new_label or prev_grp != cur_grp:
            image_divs += f'<h3>Defect Intensity: {get_defect_intensity(cur_grp) }</h3>\n'
            prev_grp = cur_grp
        image_div = df_annot.loc[idx,'divs']
        # If image_div is empty, it will be float('nan').  Unfortunately, image_div == float('nan') does not seem to work.
        if isinstance(image_div,str):
            image_divs += image_div
            
    #TODO Move to PIL without saving to disk in order 
    #img_tmp = Image.open(targ_f.ile)
    #img_tmp = img_tmp.convert("L")
    #img_tmp.save(targ_file)    
    
    if osp.exists(rpt_path):
        os.remove(rpt_path)
    
    # TODO Set variables for various directories, so don't have to store full path names in arrays and src of images
    # TODO Put carriage returns between entries in dicts
    xref = {'image_dict':image_dict,    # In javascript, the Python list is an array
            'image_divs':image_divs,
            'annot_dict':annot_dict,
            'toc':toc}
    with open(rpt_path,'w') as f_o:
        with open(template_path) as f_t:
            for in_line in f_t:
                out_line = in_line
                # Escape $
                out_line = out_line.replace('$','$$')
                # Substitute % for $
                out_line = out_line.replace('%','$')
                template = string.Template(out_line)
                out_line = template.substitute(xref)
                f_o.write(out_line)

# TODO * Handle errors - clean up painter 

