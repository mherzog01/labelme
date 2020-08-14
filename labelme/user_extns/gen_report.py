# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 16:23:19 2020

@author: MHerzo


Assumptions
1.  Images are in a single folder, or the list of images is unique by image basename
2.  Dataframe of annotations (df_annot) is generated at the same time that the annotated images (.png files) are generated.  See below for details.

TODO 
TODO *** Scan entire list below for priority tasks
1. Improve performance of report
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
8.  * Create table of contents (by label)
9.  Set title of report .html file
10.  Display lot number.  Requires using database -- centralize annotations with data set?
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
module_folder = osp.dirname(__file__)
export_folder = osp.join(module_folder, 'annotation_exports')
template_path = osp.join(module_folder,'rpt01_template.html')
label_dir = r'\\ussomgensvm00.allergan.com\lifecell\Depts\Tissue Services\Tmp\MSA\Annot\Ground Truth'
#label_dir = r'c:\tmp\work4'
selection_margin = 100  # Number of pixels that surround the selected area of the image
create_img_exports = ['all','new','none'][1]  
#------------------------------------------

# The report depends on current state of image annotations, so prior versions may not have integrity
#rpt_stem = 'rpt01'
#rpt_name = f'{rpt_stem}_{datetime.datetime.now():%Y%M%D_%h%m%s}.html'
rpt_basename = 'rpt01.html'
rpt_path = osp.join(export_folder, rpt_basename)

# TODO Clean up -- move to a function and make pythonic - remove hardcodes and reduce back and forth between lists and numpy arrays
#      Also in apps.py
label_colormap_orig = imgviz.label_colormap(value=200)
LABEL_COLORMAP = []
# Preserve order
for c in label_colormap_orig:
    # Exclude colors too close to the color of tissue [200,200,200]
    # TODO Make soft
    if all(abs(c - np.array([200,200,200])) < np.array([50,50,50])):
        continue
    c_l = list(c)
    if c_l in LABEL_COLORMAP:
        continue
    LABEL_COLORMAP += [c_l]
LABEL_COLORMAP = np.array(LABEL_COLORMAP)

num_labels = len(LABEL_COLORMAP)


image_list = []
df_divs = pd.DataFrame(columns=['Div'])

if osp.exists(rpt_path):
    os.remove(rpt_path)

# TODO Mouse over defect type and severity
# TODO Comments
# TODO Lot number
# TODO Build df_annot when scan image, not as a separate (and duplicate) task
df_annot = user_extns.getAnnotDf(glob.glob(osp.join(label_dir,"*.bmp")))
df_annot['image_basename'] = df_annot['image_path'].map(lambda x:osp.basename(x))

# TODO Check if df_annot is unique on 'image_basename' and 'annot_num'

# **************************************************** 
# 1.  For each image, collect entries in image_div with a key that links them
# 2.  Output them separately using sorted df_annot

# Technical notes
# 1.  The entries in df_annot must be linked to the entries in image_divs 
#     which are created as we draw the images.
#
#     This process first generates df_annot by calling labelFile and iterating over 
#     labelFile.shapes.  It then draws annotations on images using the same logic.
#
#     If labelFile.shapes is the same data in both instances, we can assign each
#     annotation a sequence number, and that sequence will match between 
#     df_annot and the code below.
#
#     => Assume that df_annot was generated from same file as labelFile reads 
#        in the code below.
# **************************************************** 
# TODO Need more pythonic way of initializing df_divs
df_divs['Div'] = [''] * len(df_annot)
multi_idx = pd.MultiIndex.from_frame(df_annot[['image_basename','annot_num']])
df_divs.index = multi_idx


app = QtWidgets.QApplication(sys.argv)
    
img_num = -1
for img_path, img_basename in set(zip(df_annot['image_path'], df_annot['image_basename'])):

    #img_basename = r'20200213-154422-Img - Test.bmp'
    img_num += 1
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Image={img_basename}')
    
    img_basestem, img_ext = osp.splitext(img_basename)
    export_basename = img_basestem + '_export.png'
    export_path = osp.join(export_folder,export_basename)
    
    if create_img_exports == 'all':
        create_image = True
    elif create_img_exports == 'none':
        create_image = False
    elif create_img_exports == 'new':
        create_image = not osp.exists(export_path)        

    image_list.append([img_path, export_path])
    
    # Delete files one at a time to allow updates of individual files
    if create_image and osp.exists(export_path):
        os.remove(export_path)
            
    label_file = user_extns.imgFileToLabelFileName(img_basename, label_dir)
    labelFile = labelme.LabelFile(label_file, loadImage=False)    
    
    labels_to_export = set([shape['label'] for shape in labelFile.shapes])
    # TODO **Make consistent - add new label/color combinations as they arise?
    # TODO *Make colors consistent with labelMe
    label_colors = {label : QtGui.QColor(*LABEL_COLORMAP[idx % num_labels]) for idx,label in enumerate(labels_to_export)}
    
    # Load image to initialize the pixmap to the proper size
    # Then, set all pixels to 0
    pixmap = QtGui.QPixmap(img_path)
    img_shape = [pixmap.size().width(),pixmap.size().height()]
    #pixmap.fill(QtGui.QColor(0,0,0))
    # Paint annotations
    # TODO Centralize annotation painting logic -- it exists here and several other places (app.exportMasks, etc.).  Use util/shape_to_mask or examples/.../draw_json.py
    # TODO don't paint if 'create_image' == False
    p = QtGui.QPainter(pixmap)
    shapes_to_export = labelFile.shapes
    for annot_idx, s in enumerate(shapes_to_export):
        annot_num = annot_idx + 1
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
        # TODO - draw text label and shape # of annotation next to shape
        # TODO Get the scale value more intelligently?  canvas.scale -> widget scale factor via canvas.update?
        s_obj.scale = 1 / 2
        s_obj.line_color = label_colors[s_obj.label]
        s_obj.paint(p)
        
        # Get bounding region of image.  ll = Lower Left, ur = Upper Right
        roi_ll = (max(0,min_w - selection_margin), min(img_shape[1],max_h + selection_margin))
        roi_ur = (min(img_shape[0],max_w + selection_margin), max(0,min_h - selection_margin))
        
        # Add to image_divs
        img_div_width = roi_ur[0] - roi_ll[0]
        img_div_height = roi_ll[1] - roi_ur[1]
        
        img_id = f'{img_basename},{annot_num}'
        
        image_divs = ''
        image_divs += f'<div class="crop">\n'
        image_divs += f'  <div class="crop" style="width:{img_div_width};height:{img_div_height}" '
        image_divs += f'       onclick="getimage(\'{img_id}\',{img_num})"'
        image_divs += f'       title="{s_obj.label}, Intensity: {get_defect_intensity(s_obj.group_id), {img_basename}}">\n'
        image_divs += f'    <img id="{img_id}" src="{export_path}" alt="{img_basename} {s_obj.label}" style="margin-top:-{roi_ur[1]};margin-left:-{roi_ll[0]};">\n'
        image_divs += f'  </div>\n'
        image_divs += f'  <div style="width:{img_div_width}">\n'
        image_divs += f'    {img_basename}, {annot_num}\n'
        if any(s_obj.flags.values()):
            image_divs += f'    <br>{", ".join([key for key in s_obj.flags if s_obj.flags[key]])}\n'
        image_divs += f'    <div style="height:5"></div>\n'
        image_divs += f' </div>\n'
        image_divs += f' </div>\n'
        df_divs.loc[(img_basename,annot_num),'Div'] = image_divs
    
    p.end()
    
    if create_image:
        # TODO Improve performance.  Saving to disk is slow
        # https://stackoverflow.com/questions/57404778/how-to-convert-a-qpixmaps-image-into-a-bytes
        # Profiling shows that the "save" method (e.g. pixmap.save) is the bottleneck
        
        # ba = QtCore.QByteArray()
        # buff = QtCore.QBuffer(ba)
        # buff.open(QtCore.QIODevice.WriteOnly) 
        # ok = pixmap.save(buff, "PNG")
        # pixmap_bytes = ba.data()
        # with open(export_path,'wb') as f:
        #    f.write(pixmap_bytes)

        #img_to_export = pixmap.toImage()
        #img_to_export.convertToFormat(QtGui.QImage.Format_Indexed8)
        #img_to_export.save(export_path)

        pixmap.save(export_path)

# 1.  Write HTML header (script) and report header [*Template needed]
# 2.  For each label
#        Write section header
#        Write divs [*Template needed]

image_divs = ''
prev_label = None
prev_grp = None
for idx in df_annot.sort_values(['label','group_id','image_basename','annot_num']).index:
    row = df_annot.loc[idx]
    cur_label = row['label']
    cur_grp = row['group_id']
    if not prev_label or prev_label != cur_label:
        image_divs += f'<h2>{cur_label}</h2>\n'
        prev_label = cur_label
        prev_grp = None
        new_label = True
    else:
        new_label = False
    if new_label or prev_grp != cur_grp:
        image_divs += f'<h3>Defect Intensity: {get_defect_intensity(cur_grp) }</h3>\n'
        prev_grp = cur_grp
    image_divs += df_divs.loc[(row['image_basename'],row['annot_num']),'Div']
        
#TODO Move to PIL without saving to disk in order 
#img_tmp = Image.open(targ_f.ile)
#img_tmp = img_tmp.convert("L")
#img_tmp.save(targ_file)    

xref = {'basedir':export_folder.replace('\\','/'),
        'image_array':image_list,    # In javascript, the Python list is an array
        'image_divs':image_divs}
with open(rpt_path,'w') as f_o:
    with open(template_path) as f_t:
        for in_line in f_t:
            out_line = in_line
            # Escape $
            out_line = out_line.replace('$','$$')
            # Substitute $ for %
            out_line = out_line.replace('%','$')
            template = string.Template(out_line)
            out_line = template.substitute(xref)
            f_o.write(out_line)

# TODO * Handle errors - clean up painter 