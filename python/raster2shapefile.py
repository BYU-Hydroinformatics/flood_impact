#!/usr/bin/env python
# coding: utf-8

# # Set Working Directory

import os
# What is the path of your working directory
# path = input("Path of working directory:\t")
path = "/Users/evan/flood_map_py/"
os.chdir(path)
print("Current Working Directory ", os.getcwd())


# # Load Library
# We do not need all of these, but it's something to start with.

from osgeo import gdal, ogr
import rasterio as rio

import numpy as np
import geopandas as gpd
from fiona.crs import from_epsg

# This will import all of the utility functions and more
from fldimpact_def import *

# ## Flood Map Raster Upload

# Flood raster file
# fld_file = input("What is the location of the flood map raster file?:\t")
fld_file = 'Thailand_Oct2021/Flood_Nakhon_Sawan_100m.tif'

# These are pre-named and it assumed there is a folder called temp in the os path previously stated.
# You can grab code from flood_impact.py for creating and deleting a temp folder
reclass_file ='temp/fld_reclass.tif'

reclass_raster(fld_file, reclass_file, 1, 1, 1, 0)

null_file = "temp/fld_nodata.tif"

ras_Null(reclass_file, null_file, 0)


# # Convert Raster to Polygon
# flood_map = input("Location to put the flood map:\t")
flood_map = 'temp/fld_poly_thai_100m.shp'

ras2poly(null_file, flood_map, 0)


# # Fix the Geometry if needed

# Check to see if the geometries are valid
fld_map = gpd.read_file(flood_map)
fld_map.is_valid

# Ocassionally the geometries are not valid so fix geometries
fix_geometries(flood_map)

# Since the data we have is in ESPG: 4236, force the shapefile to be same projection
fld_map = gpd.read_file(flood_map)
data = fld_map.to_crs(epsg=4326)
# write shp file
data.to_file(flood_map)


# ### Setting consistent plotting style throughout notebook
'''
import seaborn as sns

sns.set_style("dark")
sns.set(font_scale=1.5)

import matplotlib.pyplot as plt
import contextily as ctx



flood_map = gpd.read_file(flood_map)

fig, ax = plt.subplots(figsize = (12,12))


ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Flood Extent Map');

flood_map.plot(ax=ax)
ctx.add_basemap(ax, crs = flood_map.crs, source = ctx.providers.OpenStreetMap.Mapnik)
plt.show()'''