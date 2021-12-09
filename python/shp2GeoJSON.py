#!/usr/bin/env python
# coding: utf-8

import os
path = "/Users/evan/Utah_County_Boundaries/"
os.chdir(path)
print("Current Working Directory ", os.getcwd())

from osgeo import ogr, gdal
import rasterio as rio
from rasterio.mask import mask

import pandas as pd
import geopandas as gpd
import numpy as np

import georasters as gr

from fiona.crs import from_epsg
from shapely.geometry import box

# for plotting
from rasterio import plot
from rasterio.plot import show
from rasterio.plot import show_hist
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx

# for reading a geodatabase
import fiona

# flood_file = input("Flood map file name:\t")
flood_file = 'utah_state.shp'

flood_map = gpd.read_file(flood_file)
'''
fig, ax = plt.subplots(figsize = (12,12))

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Flood Extent Map');

flood_map.plot(ax=ax)
#ctx.add_basemap(ax, crs = flood_map.crs, source = ctx.providers.OpenStreetMap.Mapnik)
plt.show()
'''
import json
import geojson
from shapely.geometry import shape

import shapefile
import pygeoif

import shapely.wkt
import shapely.geometry


# This will import all of the utility functions and more
from fldimpact_def import *

# Will want to change the names of the geojson files
json_file = 'Utah.geojson'
flood_map.to_file(json_file, driver='GeoJSON')
f = open(json_file,)

fld_json = json.load(f)


'''print(fld_json)



fld_map = gpd.read_file('Utah.geojson')

fig, ax = plt.subplots(figsize = (12,12))


ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Flood Extent Map');

fld_map.plot(ax=ax)
ctx.add_basemap(ax, crs = fld_map.crs, source = ctx.providers.OpenStreetMap.Mapnik)
plt.show()'''