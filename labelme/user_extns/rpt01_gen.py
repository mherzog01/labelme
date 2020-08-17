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

def get_defect_intensity(group_id):
    return str(group_id) if not group_id == float('nan') else 'None'

#------------------------------------------
# Settings
run_mode = ['DEV','PROD'][0]
create_img_exports = ['all','new','none'][1]  
create_annot_exports = [ 'all','new','none'][1]
selection_margin = 100  # Number of pixels that surround the selected area of the image
if run_mode == 'PROD':
    label_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\Annot\Ground Truth'
else:
    label_dir = r'c:\tmp\work4\Annot\Ground Truth'
#------------------------------------------
    
module_folder = osp.dirname(__file__)
template_path = osp.join(module_folder,'rpt01_template.html')
export_root = osp.join(label_dir, '..','..','util','export_images')
export_img_dir = osp.join(export_root,'annotation_exports')
export_annot_dir = osp.join(export_root,'annotation_exports_single')
#label_dir = r'c:\tmp\work4'

# The report depends on current state of image annotations, so prior versions may not have integrity
#rpt_stem = 'rpt01'
#rpt_name = f'{rpt_stem}_{datetime.datetime.now():%Y%M%D_%h%m%s}.html'
rpt_basename = 'rpt01.html'
rpt_path = osp.join(export_root, rpt_basename)

LABEL_COLORMAP = user_extns.get_colormap()
num_colors = len(LABEL_COLORMAP)


image_dict = {} # Xref images of entire tissue with and without annotations
annot_dict = {} # Xref images of individual annotations with and without annotation boundaries displayed

if osp.exists(rpt_path):
    os.remove(rpt_path)

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
    
    if not obj_annots.cur_image_shapes:
        continue
    
    img_basestem, img_ext = osp.splitext(img_basename)
    export_img_basename = img_basestem + '_export.png'
    export_img_path = osp.join(export_img_dir,export_img_basename)
    
    if create_img_exports == 'all':
        create_image = True
    elif create_img_exports == 'none':
        create_image = False
    elif create_img_exports == 'new':
        create_image = not osp.exists(export_img_path)        
    else:
        print(f'Invalid value for create_image={create_image}')

    image_dict[img_num] = [img_path, export_img_path]
    
    # Delete files one at a time to allow updates of individual files
    if create_image and osp.exists(export_img_path):
        os.remove(export_img_path)
    
    img_pixmap = QtGui.QPixmap(img_path)
    img_pixmap_orig = img_pixmap.copy()
    img_size = img_pixmap.size()

    # Organize images by label/annotation instance
    # Assume that df_shapes is a view of df_annot
    # To avoid dealing with different representations of path separators, use the base name
    df_shapes = df_annot.query(f'`image_basename` == "{img_basename}"')
    # https://stackoverflow.com/questions/37997668/pandas-number-rows-within-group-in-increasing-order
    df_grp = df_shapes.groupby('label').cumcount()+1
    for idx in df_grp.index:
        df_annot.loc[idx,'label_instance'] = df_grp.loc[idx]
    
    # Paint annotations
    # TODO Centralize annotation painting logic -- it exists here and several other places (app.exportMasks, etc.).  Use util/shape_to_mask or examples/.../draw_json.py
    # TODO don't paint if 'create_image' == False
    p_img = QtGui.QPainter(img_pixmap)
    
    #TODO Centralize logic in creating all names.  Deletion, and possibly other logic makes naming assumptions.
    export_annot_basestem = f'{img_basestem}_export_'

    # Delete all annotations of the image, if desired
    if create_annot_exports == 'all':
        for file in glob.glob(osp.join(export_annot_dir,export_annot_basestem + '*.png')):
            os.remove(file)
        create_annot_images = True
    elif create_annot_exports == 'none':
        create_annot_images = False
    elif create_annot_exports == 'new':
        # create_annot_images will be set in logic below for each annotation
        pass
    else:
        print(f'Invalid value for create_annot_exports={create_annot_exports}')

    for idx in df_shapes.index:
        row = df_shapes.loc[idx]
        annot_num = row['annot_num']  # Unique within an image
        annot_id = row.name # Unique identifier across all annotations in report
        s_obj = row['shape_obj']  
        if not hasattr(s_obj,'label'):
            continue
        label = s_obj.label

        # TODO *Make colors consistent with labelMe
        if label and not label in label_colors:
            label_colors[s_obj.label] = QtGui.QColor(*LABEL_COLORMAP[len(label_colors) % num_colors])
        
        # TODO More pythonic way of handing min/max x/y
        min_w, max_w, min_h, max_h = (img_size.width(),0,img_size.height(),0)
        first_pt_q = None
        for pt in s_obj.points:
            #pt_q = QtCore.QPointF(pt[0],pt[1])
            #pt_q_list += [pt_q]
            if not first_pt_q:
                first_pt_q = pt
            min_w = min(min_w, pt.x())
            max_w = max(max_w, pt.x())
            min_h = min(min_h, pt.y())
            max_h = max(max_h, pt.y())
        s_obj.addPoint(first_pt_q)
        #s_obj.close = True
        s_obj.fill = False
        s_obj.point_size = 0
        # TODO - draw text label and shape # of annotation next to shape
        # TODO Get the scale value more intelligently?  canvas.scale -> widget scale factor via canvas.update?
        s_obj.scale = 1 / 2
        s_obj.line_color = label_colors[s_obj.label]
        s_obj.paint(p_img)
        
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
        label_clean = s_obj.label.replace('/','')
        export_annot_basename = export_annot_basestem + f'{label_clean}_{annot_num}.png'
        export_annot_path = osp.join(export_annot_dir,export_annot_basename)        

        export_annot_basename_a = export_annot_basestem + f'{label_clean}_{annot_num}_annot.png'
        export_annot_path_a = osp.join(export_annot_dir,export_annot_basename_a)        

        if create_annot_exports == 'new':
            if osp.exists(export_annot_path) and osp.exists(export_annot_path_a):
                create_annot_images = False
            else:
                create_annot_images = True            
                
        if create_annot_images:
            # https://stackoverflow.com/questions/25795380/how-to-crop-a-image-and-save
            roi_ll_q = QtCore.QPoint(margin_left,margin_top)
            roi_q = QtCore.QRect(roi_ll_q,QtCore.QSize(img_div_width,img_div_height))

            # Unannotated image
            annot_pixmap = img_pixmap_orig.copy(roi_q)
            annot_pixmap.save(export_annot_path)

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
            annot_pixmap_a.save(export_annot_path_a)
            
        annot_dict[annot_id] = [export_annot_path, export_annot_path_a]
        
        # ------------------
        # Construct and store the HTML for the divs
        # ------------------

        img_id = f'annot_{annot_id}'
        
        image_divs = ''
        image_divs += f'<div class="disp_img">\n'
        image_divs += f'  <div '
        image_divs += f'       onclick="getimage(\'{img_id}\',{annot_id})"'
        image_divs += f'       title="{s_obj.label}, Intensity: {get_defect_intensity(s_obj.group_id)}, {img_basename}">\n'
        image_divs += f'    <img id="{img_id}" src="{export_annot_path_a}" alt="{export_annot_basename_a} {s_obj.label}">\n'
        image_divs += f'  </div>\n'
        image_divs += f'  <div style="height:5"></div>\n'
        image_divs += f'  <div style="width:{img_div_width}">\n'
        image_divs += f'    {img_basename}, {annot_num} <a onclick="show_tissue_img(\'{img_id}\',{annot_id},{img_num})" href="javascript:void">Show</a>\n'
        if any(s_obj.flags.values()):
            image_divs += f'    <br>{", ".join([key for key in s_obj.flags if s_obj.flags[key]])}\n'
        image_divs += f'    <div style="height:10"></div>\n'
        image_divs += f' </div>\n'
        image_divs += f' </div>\n'

        # The following is for entire images.  We are using a different approach
        # image_divs = ''
        # image_divs += f'<div class="crop">\n'
        # image_divs += f'  <div class="crop" style="width:{img_div_width};height:{img_div_height}" '
        # image_divs += f'       onclick="getimage(\'{img_id}\',{img_num})"'
        # image_divs += f'       title="{s_obj.label}, Intensity: {get_defect_intensity(s_obj.group_id), {img_basename}}">\n'
        # image_divs += f'    <img id="{img_id}" src="{export_img_path}" alt="{img_basename} {s_obj.label}" style="margin-top:-{margin_top};margin-left:-{margin_left};">\n'
        # image_divs += f'  </div>\n'
        # image_divs += f'  <div style="width:{img_div_width}">\n'
        # image_divs += f'    {img_basename}, {annot_num}\n'
        # if any(s_obj.flags.values()):
        #     image_divs += f'    <br>{", ".join([key for key in s_obj.flags if s_obj.flags[key]])}\n'
        # image_divs += f'    <div style="height:5"></div>\n'
        # image_divs += f' </div>\n'
        # image_divs += f' </div>\n'
        df_annot.loc[idx,'divs'] = image_divs
    
    p_img.end()
    
    if create_image:
        img_pixmap.save(export_img_path)

# ------------------------------------------------
# Set up variables for Template substitution
# ------------------------------------------------

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