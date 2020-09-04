# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 11:02:17 2020

@author: MHerzo
"""

import json
import numpy as np
import os
from PIL import Image

import googleapiclient.discovery



class ImgPredMgr():

    def __init__(self):
        # Globals for automation (machine learning)
        # TODO Make parameters, or get from a config file/module
        self.CLOUD_PROJECT = 'tissue-defect-ui'
        self.MODEL = 'tissue_boundary'
        self.MODEL_VERSION = None
        self.model_img_size = (224,224)
        self.GOOGLE_APPLICATION_CREDENTIALS = r'm:\msa\cfg\cred\Tissue Defect UI-ML Svc Acct.json'
            
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.GOOGLE_APPLICATION_CREDENTIALS

    
    def predict_json(self, instances):
    
        project=self.CLOUD_PROJECT
        model=self.MODEL
        version=self.MODEL_VERSION
        
        service = googleapiclient.discovery.build('ml', 'v1')
        name = 'projects/{}/models/{}'.format(project, model)
    
        if version is not None:
            name += '/versions/{}'.format(version)
    
        response = service.projects().predict(
            name=name,
            body={'instances': instances}
        ).execute()
    
        if 'error' in response:
            raise RuntimeError(response['error'])
    
        return response['predictions']
    
    
    # Assume images in a PIL format
    def predict_imgs(self, img_list):
        instances = []
        for img in img_list:
            
            img_resized = img.resize(self.model_img_size, Image.ANTIALIAS)        
            img_resized_np = np.asarray(img_resized, dtype=np.float) 
            
            img_resized_np = img_resized_np / 255
            #display_img(img_resized_np)
        
            # Without rounding (or the equivalent), the .tolist() method creates a 
            # payload that is too large.  However, the dtype of the array being 
            # rounded must be float, not float32.
            # https://stackoverflow.com/questions/20454332/precision-of-numpy-array-lost-after-tolist
            img_rounded = np.around(img_resized_np, 4)
            instances.append(img_rounded.tolist())
        
        # TODO Add logging and error handling
        self.predictions = self.predict_json(self.CLOUD_PROJECT, self.MODEL, instances)
        return predictions    
    
    
    # Utility functions
    def create_mask(self, pred_mask):
      pred_mask = np.argmax(pred_mask, axis=-1)
      pred_mask = pred_mask[..., np.newaxis]  
      return pred_mask   
  
    @property
    def pred_np(self):
        pred_np_list = []
        for p in self.predictions:
            pred_np = np.array(p['conv2d_transpose_9'])
            pred_np_list.append(pred_np)
        return pred_np_list
