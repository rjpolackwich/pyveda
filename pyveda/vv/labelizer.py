try:
    import ipywidgets as widgets
    from ipywidgets import Button, HBox, VBox, RadioButtons
    has_ipywidgets = True
except:
    has_ipywidgets = False

try:
    from IPython.display import display, clear_output
    has_ipy = True
except:
    has_ipy = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    has_plt = True
except:
    has_plt = False

from shapely.geometry.geo import shape
from shapely.geometry import *
import numpy as np
import requests

from pyveda.auth import Auth
from pyveda.veda import api
gbdx = Auth()
conn = gbdx.gbdx_connection

class Labelizer():
    def __init__(self, vedaset, count):
        """
          Labelizer will page through image/labels and allow users to remove/change data or labels from a VedaBase or VedaStream
          Params:
            ids (generator): A Url generator for datapoints to be viewed
            count (int): the number of datapoints to process
            imshape (tuple): shape of each incoming image
            dtype (str): the datatype of the images
            mltype (str): the mltype of the veda collection
        """
        assert has_ipywidgets, 'Labelizer requires ipywidgets to be installed'
        assert has_ipy, 'Labelizer requires ipython to be installed'
        assert has_plt, 'Labelizer requires matplotlib to be installed'

        # self.ids = ids #not sure if we need or not yet.
        self.vedaset = vedaset
        self.count = count
        # self.imshape = imshape
        # self.dtype = dtype
        # self.mltype = mltype
        self.index = 0
        self.dp = self.vedaset.get_next()
        self.flagged_tiles = []

        def get_next(self):
            """
            Fetches the next DataPoint object from VedaCollection ids.
            """
            self.dp = self.vedaset.__next__()
            print('this worked!')
            return self

        def clean(self):
            a = self.get_next()
            print('good')
            return(a)
