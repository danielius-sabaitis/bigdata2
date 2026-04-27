# ***Big Data*** **Assignment #2: Creating a Python Code and Packaging it into a Docker Container**

## Description:

Dockerized script for bulk downloading meteorological data from the archive of Lithuanian Hydrometeorological Service under the Ministry of Environment (https://meteo.lt/).

*Docker Hub* repository – https://hub.docker.com/r/danieliuss/lt_meteo_data/.

## Short backstory:

The main part of the python script used in this assingment was originally created for the *Functional Data Analysis* project for a convenient way to download all official meteorological data from 52 weather stations in Lithuania.

Originally, the data was to be scraped from the meteorological archive, previously available deep in the source code at https://archyvas.meteo.lt/. After this page went down in the middle of doing this assingment, I was forced to use the heavily restricting meteo.lt API – https://api.meteo.lt/.

***Update (2026-04-27):*** https://archyvas.meteo.lt/ went back online but I will stick to using the API.

## How the image was created:

1. `requirement.txt` and `.dockerignore` are created and filled out.

2. `meteo_download.dockerfile` is created and set up to use the official *python-slim* Docker image as the base.

3. `./code` directory is created and set as the working directory of the image.

4. `requirement.txt` and `downloader.py` are copied inside the image.

5. The image is built with this command:
```
docker build -f meteo_download.dockerfile -t danieliuss/lt_meteo_data:latest .
```
6. The image is pushed to *Docker Hub* with this command:
```
docker push danieliuss/lt_meteo_data:latest
```
The image is now ready to be downloaded and run.

## How to download:

❗**Important note**: this guide assumes you have Docker set up. 

1. To download the image execute this command:
```
docker pull danieliuss/lt_meteo_data:latest
```
2. Check the available script arguments with `--help`:
```
docker run --rm danieliuss/lt_meteo_data --help
```
3. Output of the `--help` argument:

|     **Argument** |                                         **Description**                                                   |
| ---------------- | --------------------------------------------------------------------------------------------------------- |
|   /--h, /--help  | Prints the help message                                                                                   |
| /--list-stations | Prints all the available station codes                                                                    |
|     /--start     | Start date (YYYY-MM-DD)                                                                                   |
|      /--end      | End date (YYYY-MM-DD) (up to but not including)                                                           |
|    /--stations   | Stations to download: "all" or comma-separated station codes without spaces (e.g. vilniaus-ams,kauno-ams) |
|    /--workers    | Total number of parallel chunk requests                                                                   |
|   /--overwrite   | Whether to overwrite the existing station CSV files (y/n)                                                 |

4. Run the script (in the working directory):
```
docker run --rm -v ${PWD}/meteo_data:/code/meteo_data danieliuss/lt_meteo_data [param1] [param2] ...
```

Enjoy and don't forget to respect the API usage limits.

## Artificial Intelligence usage disclosure:

AI was used to create the main part behind the scraping code since at first, the data was being scraped from .json files hidden deep in the source code of the original archive page. 
