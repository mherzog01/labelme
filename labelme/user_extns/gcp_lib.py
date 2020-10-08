# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 11:02:17 2020

@author: MHerzo
"""

import numpy as np
import os
from PIL import Image

import googleapiclient.discovery

from matplotlib import pyplot as plt

from labelme.user_extns import img_ml_util



class ImgPredMgr():

    def __init__(self):
        # Globals for automation (machine learning)
        # TODO Make parameters, or get from a config file/module
        self.CLOUD_PROJECT = 'tissue-defect-ui'
        self.MODEL = 'tissue_boundary'
        self.MODEL_VERSION = None
        self.model_img_size = (224,224)
        self.GOOGLE_APPLICATION_CREDENTIALS = r'm:\msa\cfg\cred\Tissue Defect UI-ML Svc Acct.json'
        self.cred_set = False
        
        self.set_cred()
        
    def set_cred(self, cred_path=None):
        if cred_path is None:
            cred_path = self.GOOGLE_APPLICATION_CREDENTIALS
        if os.path.exists(cred_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path
            self.cred_set = True

    
    # TODO Add logging and error handling - status messages
    def predict_json(self, instances):
    
        project=self.CLOUD_PROJECT
        model=self.MODEL
        version=self.MODEL_VERSION
        
        self.service = googleapiclient.discovery.build('ml', 'v1', cache_discovery=False, )
        self.model_version_string = 'projects/{}/models/{}'.format(project, model)
    
        if version is not None:
            self.model_version_string += '/versions/{}'.format(version)
    
        response = self.service.projects().predict(
            name=self.model_version_string,
            body={'instances': instances}
        ).execute()
    
        if 'error' in response:
            raise RuntimeError(response['error'])
    
        return response['predictions']
    
    
    # Assume images in a PIL format
    def predict_imgs(self, img_list):
        instances = []
        self.resized_images = []
        self.predictions = []
        for img in img_list:
            
            img_resized = img.resize(self.model_img_size, Image.ANTIALIAS)        
            img_resized_np = np.asarray(img_resized, dtype=np.float) 
            
            img_resized_np = img_resized_np / 255
            self.resized_images.append(img_resized_np)
            #display_img(img_resized_np)
        
            # Without rounding (or the equivalent), the .tolist() method creates a 
            # payload that is too large.  However, the dtype of the array being 
            # rounded must be float, not float32.
            # https://stackoverflow.com/questions/20454332/precision-of-numpy-array-lost-after-tolist
            img_rounded = np.around(img_resized_np, 4)
            instances.append(img_rounded.tolist())
        
        # TODO Add logging and error handling
        self.predictions = self.predict_json(instances)
        return self.predictions    
    
    
    # Utility functions
    def create_mask_np(self, pred_mask):
        pred_np = np.argmax(pred_mask, axis=-1)
        #pred_np = pred_np[..., np.newaxis]  
        return pred_np 
  
    @property
    def pred_masks(self):
        pred_mask_list = []
        for p in self.predictions:
            pred_mask = np.array(p['conv2d_transpose_output'])
            pred_mask_list.append(pred_mask)
        return pred_mask_list

    @property
    def pred_masks_np(self):
        pred_mask_np_list = []
        for p in self.pred_masks:
            pred_mask_np_list.append(self.create_mask_np(p))
        return pred_mask_np_list


if __name__ == '__main__':

    # TODO Move to Tests. Segregate user_extns tests from other tests.
    img_path = r'c:\tmp\work1\20200211-151331-Img.bmp'
    
    ipm = ImgPredMgr()
    cred_path = ipm.GOOGLE_APPLICATION_CREDENTIALS
    if not os.path.exists(cred_path):
        cred_path = r'c:\tmp\work1\Tissue Defect UI-ML Svc Acct.json'
    ipm.set_cred(cred_path)
    
    img = Image.open(img_path)
    ipm.predict_imgs([img])
    for idx, m_np in enumerate(ipm.pred_masks_np):
        print(idx, m_np.shape)
        
    for img_resized, mask in zip(ipm.resized_images, ipm.pred_masks_np):
        overlay = img_ml_util.add_overlay(img_resized, mask)
        img_ml_util.display([img_resized, mask, overlay])        