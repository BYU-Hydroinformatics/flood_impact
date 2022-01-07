# Flood Impact

A general method to obtain flood impact metrics through ArcGIS Pro Model Builder, QGIS Graphical Modeler, and stand-alone Python script. These workflows are developed by Rober Evan Smith as part of a Master degree in Civil and Construction Engineering at Brigham Young University. The research was submitted in December 2021. 

## Resources

Thesis link:

Journal article link: 

Hydroshare link with all flood maps and exposure datasets for each area in study: http://www.hydroshare.org/resource/0208bf273b2b4c14b67787db6deb45eb

## Contents and Purposes
### Arcgis_pro directory
This directory contains a tool that can be imported into ArcGIS ModelBuilder. This model is the most visual way to see the process used to determine flood impact, and this process is mostly the same for the qgis tool and python modules as well (excluding a few differences due to the peculiarities of each toolset). The steps of the model are explained below:
#### Input Files:
- A shapefile containing the outline of the forecasted flood extent for your region of study.
- A raster file containing croplands.
- A raster file containing population densities.
- A shapefile from Open Street Map (OSM) containing points that identify amenities.

#### Process:
##### Branch 1
1. The croplands raster is clipped to the extent of the flood as outlined in the flood extent shapefile.
2. The values of the raster are coerced to integers.
3. All values that are not 2 are changed to null. This is because the raster values describe the land use, and cropland has a value of 2.
4. This raster is converted to points.
5. A field called "hectares" is added to the new points file.
6. The field is calculated to be (30 * 30) / 10000, or 0.09, which is the conversion from the original 30mx30m cells to hectares.
7. This point file is intersected with the flood extent.
8. The summary statistics tool is used to find the total area effected by summing the hectares field.
##### Branch 2
9. The population raster is also clipped to the flood extent.
10. The population values are coerced to an integer.
11. The raster is converted to points.
12. The "GRID_CODE" field name is changed to "Population".
13. The population points are intersected with the flood extent.
14. The sum of all population values is found, indicating the total number of people affected.
##### Branch 3
15. A field called "amenity" is added to the Open Street Map amenities point file.
16. Another field called "Amen_Group" is also added.
17. The calculate field tool is used to find the amenity type for the "Amenity" field. The tool defins a python function that searches the "other_tags" field to find all tags that define the amenity. If a given row in the "Amenity" field has the amenity defined in "other_tags", that value is placed into the "Amenity" field. Otherwise, the field gets a value of Null.
18. The "Amen_Group" field is calculated by defining a function that initializes a list of possible amenity types that would fall into broader groups (ie a "food" list is created that contains values like "bar", "cafe", "food_court", etc.) For a given row in the table, the function checks which group the value of "Amenity" falls into, if any, and sets the "Amen_Group" value to the broader group name (like "food" or "education"). Otherwise the field gets a value of Null.
19. This new OSM shapefile is intersected with the flood extent.
20. The Summary Statistics tool is used to count the number of each amenity, and amenity group, that falls within the flood extent, then these summary tables are merged with the results of the other summations to create a final summary table that contains the acres of cropland, number of people, and number of each amenity and amenity group affected by the flood.

### Qgis Directory
This directory contains a tool that can be imported into the open-source software QGIS. It works essentially the same as the ArcGIS Pro ModelBuilder tool, though the tools typically have different names. However, these should still be self-explanatory based on the description of the ArcGIS model.

### Python Directory
This directory contains the python library for flood impact calculation. The main executable is flood_impact.py, and then there are some secondary ones entitled "...loop_directory.py" and "..._loop_gdb.py". All files in the directory will be explained below:

#### fldimpact_def.py
This file contains the definitions for useful functions that are imported into the main executables. Each function is commented with its use, and they should be understandable upon reading the main process from the ArcGIS description and the description of the executables below.

#### flood_impact.py
This executable follows virtually the same process as the ArcGIS Pro model described earlier. The order of steps will be given again below to make the python script easier to follow:
1. Packages are imported and the working directory is set to a parent directory containing the necessary raster and vector datasets (see [Input Files](#input-files) in the ArcGIS description) (lines 1-48)
2. A temporary directory is created by appending "temp" to the working directory name (lines 49-61)
3. The files are coerced to the same coordinate reference system (crs), EPSG 4326. This is the 1984 World Geodetic System (WGS84), which most datasets come in, so this will work for any region of the world. However, each instance of this crs can be changed in the code if you want to use a regional projection, just remember each dataset must be converted to the same projection before the rest of the code from this point is run. You can clone the package and make a separate branch for your region which will allow you to adjust the crs conversions while retaining the original package.
##### Croplands
4. The Croplands Raster is clipped to the flood extent using the custom `ras2shp_extent()` method fom fldimpact_def.py
5. The custom `reclass_raster()` method is used to reclass all values that are not 2 (in other words, all non-cropland cells) to 0.
6. The `ras_Null()` method converts all 0 values to Null, or no data, and puts that data into a new file "null_file".
7. The georasters package ("gr") allows you to convert a raster file to a spatial point dataframe, essentially converting it to vector data.
8. All but the "row", "col", and "value" columns are dropped, and a "hectares column is added with the value of 0.09 (which you may recall is the size in hectares of each cell)
9. These crop points are saved to a .csv file and also converted to a GeoPandas DataFrame
10. The points are intersected with the flood map, then the total hectares are summed to find the total crop area within the flood. This data is written into a .json file.
##### Population
11. The population dataset follows a similar process, being clipped, converted to points, then intersected and the values summed and added to the .json.
##### OSM
12. The Open Street Map amenity points are read into a GeoPandas DataFrame, then clipped to the flood extent and checked to see if any are within it. If so, the process continues to determine what types of amenities are affected.
13. The amenities are extracted from the "other_tags" column where it contains them (it will say "amenity"=>"(amenity type)") and stored in the new "Amenity" column.
14. Unnessecary columns and rows where the Amenity value is NaN are removed.
15. The custom `amen_group()` method is applied to each row to fill the "Amenity_Group" column, then each column is grouped and counted to write the final counts to the .json.
16. There is a multiline comment containing code to plot the results that can optionally be uncommented.

#### flood_impact_loop_directory.py
This file allows you to run the process on a directory full of different flood extents.
1. The working directory first needs to be set again, and the temporary folder is created. Then all of the rasters and the OSM point file are loaded into variables, as well as a directory containing several flood extents (they should all fit within the rasters and point values you have)
2. Next, the column names are defined. This really depends on the information you have from the flood data, and what information you want to implement.
3. The loop will require several adjustments depending on your data and what you want in the final output, but you can follow the comments to understand each step much better than can be outlined here.
#### flood_impact_loop_gdb.py
This file is essentially the same as the loop_directory file, but adjusted to loop through a GeoDatabase instead of a simple directory. Each piece of it should be evident from the comments present and the explanation for the other file above.
