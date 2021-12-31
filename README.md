# Flood Impact

A general method to obtain flood impact metrics through ArcGIS Pro Model Builder, QGIS Graphical Modeler, and stand-alone Python script. These workflows are developed by Rober Evan Smith as part of a Master degree in Civil and Construction Engineering at Brigham Young University. The research was submitted in December 2021. 

## Resources

Thesis link:

Journal article link: 

Hydroshare link with all flood maps and exposure datasets for each area in study: http://www.hydroshare.org/resource/0208bf273b2b4c14b67787db6deb45eb

## Contents and Purposes
### arcgis_pro directory
This directory contains a tool that can be imported into ArcGIS ModelBuilder. Steps of the model are explained below:
#### Input Files:
<li>A shapefile containing the outline of the forecasted flood extent for your region of study
<li>A raster file containing croplands
<li>A raster file containing population densities
<li>A shapefile from Open Street Map (OSM) containing points that identify amenities
