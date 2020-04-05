from django.apps import AppConfig
import os
import tensorflow as tf
from tensorflow.keras import models
from .ocr import *

os.environ["CUDA_VISIBLE_DEVICES"]="-1"


class ApisConfig(AppConfig):
    name = 'APIs'
    # graph = tf.get_default_graph()
    mdl = None
    url = None
    def __init__(self, url):
        self.url = url

    def _util(self):
        # with self.graph.as_default():
        if self.mdl == None:
            self.mdl = models.load_model('./trainedModels/NumericTestAcc_99514.h5')
        ans = ocr(self.url, self.mdl)
        return ans



