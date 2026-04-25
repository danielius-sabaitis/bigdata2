# ***Big Data*** **Assignment #2: Creating a Python Code and Packaging it into a Docker Container**

## Description:

Dockerized script for bulk downloading official Lithuanian meteorological data from the meteo.lt archive, using the meteo.lt API.

*Docker Hub* repo – https://hub.docker.com/repository/docker/danieliuss/lt_meteo_data/.

## Short backstory:

The main part of the python script used in this assingment was originally created for the *Functional Data Analysis* project for a convenient way to download all official meteorological data from 52 weather stations in Lithuania.

Originally, the data was to be scraped from the meteorological archive, previously available deep in the source code at https://archyvas.meteo.lt/. After this page was shutdown, I was forced to use the heavily restricting meteo.lt API – https://api.meteo.lt/.

## Instructions:

❗**Important note**: this guide assumes you have Docker set up. 

1. To download the image:
```
docker pull danieliuss/lt_meteo_data:latest
```
2. Check the available parameters with `--help`:
```
docker run --rm danieliuss/lt_meteo_data --help
```
3. Run the script (in the working directory):
```
docker run --rm -v ${PWD}/meteo_data:/code/meteo_data danieliuss/lt_meteo_data [param1] [param2] ...
```

Enjoy and don't forget to respect the API usage limits.

## Artificial Intelligence usage disclosure:

AI was used to create the main part behind the scraping code since at first, the data was being scraped from .json files hidden deep in the original archive page. 
