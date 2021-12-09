#!/usr/bin/env python
# coding: utf-8

# ### Load Library
import os
import shutil

import pandas as pd
import georasters as gr
import glob

# This will import all of the utility functions and more
from fldimpact_def import *


# Set working directory

path = "/Users/evan/flood_map_py/Peru/"

os.chdir(path)
print("Current Working Directory ", os.getcwd())


newpath = path + 'temp'
if not os.path.exists(newpath):
    os.makedirs(newpath)

for filename in os.listdir(newpath):
    file_path = os.path.join(newpath, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

#####################################################################################################
# Load up croplands raster dataset path
croplands_path = "croplands_S10W80.tif"

# Load up population raster dataset path
pop_path = "worldpop_peru.tif"

# Load up the OpenSteetMap point shapefile dataset path
osm_file = "Chazuta_points.shp"

# Name of country
country = 'Peru'

# Name of Province
province = 'San Martin'

# Name of Region or Municipality
region = 'Chazuta'

# ### Add any other thing that you want here that will not change looping through each file

# Set column names in the order you want them in
column_names = ['Country', 'Province', 'Region', 'Return Period', 'Flood Depth', 'Flowrate (cms)',
                'Flood Date', 'Event', 'Impact Method', 'Map Method', 'Flood Map Name',
                'Agriculture (ha)', 'Population', 'Education', 'Entertainment',
                'Facilities', 'Financial', 'Food', 'Healthcare', 'Others',
                'Public Service', 'Transportation', 'Waste Management']


return_period = np.nan
flowrate = np.nan
flood_date = np.nan
event =np.nan
impact_method = "Python"
map_method = "HAND"

# Specific to removing layers for the Chazuta geodatabase
floodmap_gdb = "Chazuta_test.gdb"
fld_layer = fiona.listlayers(floodmap_gdb)
fld_layer.remove('Chazuta_Catchment_HAND')
fld_layer.remove('Chazuta_DrainageLine_HAND')
fld_layer.remove('ChazRatingCurve20m')

#####################################################################################################
# Sets an empty list that will be loaded up with values as the following iterates through a directory
impact=[]

# This is the looping mechanism
# Note: things in the loop are separated for ease of understanding the code
# Note: flood_dir is the full file path for the working directory of all flood polygons
# Note: change '.geojson' to '.shp' when applicable or other file extension that has the flood polygons.
#       Rasters will need to be changed first

# Search through the flood polygon directory and apply the following for all files
for layers in fld_layer:
    #######################
    #   Flood Map Upload  #
    #######################

    # Can help to determine problems with errors if they occur
    # print(filepath)

    # Load flood polygons into a GeoPandas DataFrame
    flood_map = gpd.read_file(floodmap_gdb, layer = layers)

    # Make sure the crs is set to EPSG:4326
    if flood_map.crs == "EPSG:4326":
        new_crs = flood_map.crs
    else:
        # Change the Coordinate Reference System to epsg=4326
        data = flood_map.to_crs(epsg=4326)

        # write shp file in the temp folder
        data.to_file('temp/fld_poly.shp')

        # Change the flood_map variable to be new shapefile location
        flood_map = gpd.read_file('temp/fld_poly.shp')
        new_crs = flood_map.crs

    # The following two variables are specific to Dominican Republic GeoJSON files.
    # Can be changed for whatever someone would want to include in the final CSV file

    # Makes 'depth_in_df' a boolean of True of False. Then use if statement to load up 'max_depth'
    depth_in_df = "FloodValue" in flood_map
    if depth_in_df == True:
        flood_depth = flood_map['FloodValue'].max()
    else:
        flood_depth = np.nan


    #######################
    #     Agriculture     #
    #######################

    # Clip raster data to the extent of the flood map.
    # Display raster data in Rasterio with flood map on same plot.

    # Load up future clipped raster file path
    crop_clip = "temp/crop_clipped.tif"

    ras2shp_extent(croplands_path, flood_map, crop_clip)

    # ### Using GDAL, leave only the cell value 2 and delete all other cells

    # Load up future reclassified raster file path
    reclass_file = "temp/crop_reclass.tif"

    reclass_raster(crop_clip, reclass_file, 2, 2, 2, 0)

    # Load up future null raster file path
    null_file = "temp/crop_null.tif"

    ras_Null(reclass_file, null_file, 0)

    # ## Convert Raster to Point Data
    # Going to convert raster data to spatial point data frame. Will use .to_pandas() function of GeoRasters package.

    # Data already loaded in variable filename

    data = gr.from_file(null_file)

    # Convert to Pandas DataFrame
    single_df = data.to_pandas()
    single_df.head()

    # Drop some columns
    columns = ['row', 'col', 'value']
    single_df = pd.DataFrame(single_df.drop(columns=columns))
    single_df["Hectares"] = 0.09
    single_df = single_df[['x', 'y', 'Hectares']]  # organize column
    single_df.head()

    # Sequence to make Raster to Point Shapefile

    # Load up future shapefile path
    crop_pts = "temp/crop_pts.shp"

    # Write as CVS file
    single_df.to_csv(str(crop_pts.partition('.')[0] + '.csv'), index=None, header=True)

    # Convert PD dataframe to Geopandas data frame
    single_df_point = gpd.GeoDataFrame(single_df, geometry=gpd.points_from_xy(single_df.x, single_df.y))

    # Define Projection
    single_df_point.crs = {'init': new_crs}

    # Writes as point shapefile
    single_df_point.to_file(crop_pts)

    cpts = gpd.read_file(crop_pts)

    # Intersect the points with the flood map
    clipped_ag = gpd.clip(cpts, flood_map)

    # Obtain total hectares of agriculture in flooded area
    hectares = clipped_ag['Hectares'].sum()



    #######################
    #      Population     #
    #######################

    # ## Population Raster Dataset
    # This will be similar to the croplands dataset process. We just want the total population within the inundation area.

    # Load up future clipped raster file path
    pop_clip = "temp/pop_clipped.tif"

    ras2shp_extent(pop_path, flood_map, pop_clip)

    # ## Converting raster to point datafile
    # Data already loaded in variable pop_path
    data = gr.from_file(pop_clip)

    # Convert to Pandas DataFrame
    pop_df = data.to_pandas()

    # Drop some columns and rename others
    columns = ['row', 'col']
    pop_df = pd.DataFrame(pop_df.drop(columns=columns))
    pop_df.rename(columns={'value': 'Population'}, inplace=True)
    pop_df = pop_df[['x', 'y', 'Population']]  # organize column
    pop_df = pop_df.astype({'Population': int})
    pop_df.head()

    # ### Load up the future population shapefile path
    pop_pts = "temp/pop_pts.shp"

    # Write as CVS file
    pop_df.to_csv(str(pop_pts.partition('.')[0] + '.csv'), index=None, header=True)

    # Convert PD dataframe to Geopandas data frame
    pop_df_point = gpd.GeoDataFrame(pop_df, geometry=gpd.points_from_xy(pop_df.x, pop_df.y))

    # Define projection
    pop_df_point.crs = new_crs

    # Writes as point shape file
    pop_df_point.to_file(pop_pts)

    popct = gpd.read_file(pop_pts)

    # Intersect the points with the flood map
    clipped_pop = gpd.clip(popct, flood_map)

    # Get total population in flooded area
    pop_count = clipped_pop['Population'].sum().astype(int)



    #######################
    #    Infrastructure   #
    #######################

    # ## OpenStreetMap Shapefile Dataset
    osm_pts = gpd.read_file(osm_file)

    # Intersect the points with the flood map
    osm_cl_df = gpd.clip(osm_pts, flood_map)

    # It is possible that the dataframe is empty so this is a conditional argument for that
    if osm_cl_df.empty:
        amen_ct = 0
        amen_gp_ct = 0
    else:
        # Use a regular expression to extract what the amenity is
        # Store the amenity is a new column called Amenity
        osm_cl_df['Amenity'] = osm_cl_df['other_tags'].str.extract('"amenity"=>"(.+?)"').astype(str)

        ######################################
        # Drop some columns and rename others
        ######################################
        columns = ['osm_id', 'name', 'barrier', 'highway', 'ref', 'address', 'is_in', 'place', 'man_made', 'other_tags']
        osm_cl_df = gpd.GeoDataFrame(osm_cl_df.drop(columns=columns))

        # Delete rows that are of value 'nan' in Amenity column
        osm_cl_df = osm_cl_df[osm_cl_df.Amenity != 'nan']

        if len(osm_cl_df.index) == 0:
            amen_ct = 0
            amen_gp_ct = 0
        else:
            # Create a new column for the amenity group
            osm_cl_df["Amenity_Group"] = osm_cl_df.apply(lambda row: amen_group(row.Amenity), axis=1)

            # This converts the dataframe to a geodataframe and therefore can be plotted
            osm_cl_df = gpd.GeoDataFrame(osm_cl_df, geometry='geometry')

            # Store the list and values of the Amenities and Amenity Groups
            amen_ct = osm_cl_df["Amenity"].value_counts()
            amen_gp_ct = osm_cl_df["Amenity_Group"].value_counts()



    #######################
    #    Load up new df   #
    #######################

    # Declare default values for the Amenity Groups (assume zero)
    education = 0
    entertainment = 0
    facilities = 0
    financial = 0
    food = 0
    healthcare = 0
    others = 0
    public = 0
    transportation = 0
    waste = 0

    # Declare count to start at 0
    count = 0

    # If there is nothing in the amen_gp_ct than pass, else loop through the Amenity Group Count DataFrame
    # and redeclare the total Amenity Groups values
    if amen_gp_ct.empty:
        pass
    else:
        # load amen_gp_ct into a DataFrame
        df1 = pd.DataFrame(amen_gp_ct)
        # reset index so that the Amenity Groups are in a column instead of the index
        df1.reset_index(inplace=True)

        # Loop through df1 to redeclare Amenity Group values
        while count < len(df1.index):
            if df1.iloc[count, 0] == 'education':
                education = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'entertainment':
                entertainment = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'facilities':
                facilities = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'financial':
                financial = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'food':
                food = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'healthcare':
                healthcare = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'others':
                others = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'public_service':
                public = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'transportation':
                transportation = df1.iloc[count, 1]
            elif df1.iloc[count, 0] == 'waste_management':
                waste = df1.iloc[count, 1]
            count += 1

    # Append to the list 'impact' with all values that was empty when this original loop was activated
    # Note: make sure the values for the in the list line up with the column names
    #       otherwise they will be in the wrong place in the CSV file
    impact.append([country, province, region, return_period, flood_depth, flowrate, flood_date, event,
                   impact_method, map_method, layers, hectares, pop_count,
                   education, entertainment, facilities, financial, food, healthcare,
                   others, public, transportation, waste])


# Load up the DataFrame of Flood Impact with the 'impact' list
df_impact = pd.DataFrame(impact,columns=column_names)

# Export the DataFrame to a CSV file
# Note: if you want to include the index, make the statement be True
# Note: header is the column name which will be helpful to import the CSV file to a SQL database schema or something similar
# Note: the CSV file is located in the flood polygon directory. The file name is the region + country + flood_impact
df_impact.to_csv(path + 'temp/' + region + '_' + country + '_flood_impact.csv', index=False, header=True)