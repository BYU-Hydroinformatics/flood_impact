# Flood Impact

A general method to obtain flood impact metrics through ArcGIS Pro Model Builder, QGIS Graphical Modeler, and stand-alone Python script. These workflows are developed by Rober Evan Smith as part of a Master degree in Civil and Construction Engineering at Brigham Young University. The research was submitted in December 2021. 

## Resources

Thesis link:

Journal article link: 

Hydroshare link with all flood maps and exposure datasets for each area in study: http://www.hydroshare.org/resource/0208bf273b2b4c14b67787db6deb45eb

## Contents and Purposes
### arcgis_pro directory
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
3. All values under 2 are changed to null.
4. This raster is converted to points.
5. A field called "hectares" is added to the new points file.
6. The field is calculated to be (30 * 30) / 10000, or 0.09, which is the size in hectares of the area that each dot represents.
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

### qgis directory
This directory contains a tool that can be imported into the open-source software QGIS. It works essentially the same as the ArcGIS Pro ModelBuilder tool, except for the following differences:
