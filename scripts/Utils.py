# Libraries
import pandas as pd
import numpy as np

import requests
from bs4 import BeautifulSoup

from pyproj import Proj, transform

import warnings

from UrlDefinition import UrlDefinition

import yaml

import folium

from scipy.spatial.distance import cdist

import os


class Utils:
    """
    Utility class for various helper functions.
    """

    def __init__(self):
        """
        Initializes Utils object and loads configuration parameters.
        """
        self.load_config()
        self.obj_url = UrlDefinition()

    def load_config(self, config_path = "config.yml"):
        """
        Loads external configuration parameters from a YAML file.

        Args:
            config_path (str, optional): Path to the configuration YAML file. Defaults to "config.yml".
        """
        if not os.path.exists(config_path):
            config_path = os.path.join("../scripts", config_path)

        with open(config_path, "r") as file:
            config = yaml.load(file, Loader = yaml.FullLoader)

        self.config = config

    def transform_coordinates(self, x, y):
        """
        Transforms UTM coordinates to latitude-longitude.

        Args:
            x (float): UTM x-coordinate.
            y (float): UTM y-coordinate.

        Returns:
            pandas.Series: Series containing latitude and longitude.
        """
        utm_zone_origen = 30
        utm_origen = Proj(proj = 'utm', zone = utm_zone_origen, ellps = 'WGS84')
        wgs84 = Proj(proj = 'latlong', datum = 'WGS84')

        lon, lat = transform(utm_origen, wgs84, x, y)

        return pd.Series([lat, lon], index = ['latitud', 'longitud'])


    def reformat_coords(self, coordinate):
        """
        Reformat coordinates from a string format to a float format.

        Args:
            coordinate (str): String representation of coordinates.

        Returns:
            float: Reformatted coordinate value.
        """
        degrees = int(coordinate[:2])

        minutes = int(coordinate[2:4])

        seconds_fraction = float(coordinate[4:6]) / 60

        if coordinate[-1] in ['N', 'E']:
            return degrees + minutes / 60 + seconds_fraction
        elif coordinate[-1] in ['S', 'W']:
            return -(degrees + minutes / 60 + seconds_fraction)
        else:
            raise ValueError("Formato de coordenadas no válido")


    def gauges_reservoirs_information(self, station_code, type_st):
        """
        Retrieves information about gauges or reservoirs based on station code and type.

        Args:
            station_code (int): Code of the station.
            type_st (str): Type of station ('aforos' for gauges, 'embalses' for reservoirs).

        Returns:
            pandas.DataFrame: DataFrame containing information about the station.
        """
        try:
            if type_st == 'aforos':
                url = self.obj_url.get_url_gauges_reservoirs(station_code, 'EA')
            elif type_st == 'embalses':
                url = self.obj_url.get_url_gauges_reservoirs(station_code, 'EM')
            else:
                pass

            # Initialization of the data extraction process
            response = requests.get(url)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')
            div_elements = soup.find_all('div', class_ = ['col-md-3 col-xs-6 b-r', 'text-themecolor m-b-0 m-t-0'])

            # Complete the station code
            cod_modified = f"2{station_code:03}"

            titles = ['id']
            numbers = [cod_modified]

            # Iterate over elements to extract information
            for div_element in div_elements:

                title = div_element.find('strong').text.strip()
                number = div_element.find('p', class_ = 'text-muted').text.strip()

                titles.append(title)
                numbers.append(number)

            # Create the dataframe with one row and multiple columns
            data = pd.DataFrame([numbers], columns = titles)
            data['titulo'] = soup.find('h3').text.strip()

            data[['X', 'Y', 'Z', 'id']] = data[['X', 'Y', 'Z', 'id']].astype(str).replace('\.', '', regex = True).astype(int)

            warnings.filterwarnings("ignore")

            data[['X', 'Y']] = data.apply(lambda row: self.transform_coordinates(row['X'], row['Y']), axis = 1)
            data = data.rename_axis(None, axis = 1)

            return(data)

        except:
            pass


    def get_all_gauges_reservoirs(self, type_st, write = False):
        """
        Retrieves information about all gauges or reservoirs.

        Args:
            type_st (str): Type of station ('aforos' for gauges, 'embalses' for reservoirs).
            write (bool, optional): Whether to write the data to a CSV file (default is False).

        Returns:
            pandas.DataFrame: DataFrame containing information about all stations.
        """
        df_list = []

        # Iterate over all posible codes
        for i in range(1, 1000):
            if type_st == 'aforos':
                    df_list.append(self.gauges_reservoirs_information(station_code = i, type_st = 'aforos'))
            elif type_st == 'embalses':
                    df_list.append(self.gauges_reservoirs_information(station_code = i, type_st = 'embalses'))
            else:
                pass

        # Consolidate the information
        df = pd.concat(df_list, axis = 0, ignore_index = True).reset_index(drop = True)


        # Export the data
        if write == True:
            if type_st == 'aforos':
                df.to_csv(self.config["DirResources"]["aforos"], encoding = 'ISO-8859-1', sep = ',', index = False)
            elif type_st == 'embalses':
                df.to_csv(self.config["DirResources"]["embalses"], encoding = 'ISO-8859-1', sep = ',', index = False)
            else:
                pass

        return(df)


    def basic_clean(self, data, freq = 'H'):
        """
        Performs basic cleaning operations on the input DataFrame.

        Args:
            data (pandas.DataFrame): Input DataFrame.
            freq (str): Frequency, 'H' for hour data and 'D' for daily data

        Returns:
            pandas.DataFrame: Cleaned DataFrame.
        """
        # Order data
        data = data.sort_values(by = 'date', ascending = True).reset_index(drop = True)
        
        # Remove missing values just if 70% of columns are NA
        threshold = 0.7
        min_non_nulls = int(data.shape[1] * (1 - threshold))
        data = data.dropna(thresh = min_non_nulls)

        # Drop duplicates
        data = data.drop_duplicates(subset = 'date', keep = 'first').reset_index(drop = True)

        # Complete missing data
        start_date = data.loc[0, 'date']
        end_date = data.loc[len(data) - 1, 'date']

        data_range = pd.DataFrame({'date': pd.date_range(start = start_date, end = end_date, freq = freq)})

        data['date'] = pd.to_datetime(data['date'])
        data = pd.merge(data_range, data, on = 'date', how = 'left')
        
        # Print alert
        missing_data = data.isnull().sum()
        missing_percentage = (missing_data / len(data)) * 100
        columns_with_missing_data = missing_percentage[missing_percentage > 1]
        
        if len(columns_with_missing_data) > 0:
            print('Las siguietes columnas presentan un porcentaje de valores nulos mayor al 5%:')
            print(columns_with_missing_data)
        else:
            pass

        # Fill missing values
        data = data.fillna(method = 'ffill')
        data = data.reset_index(drop = True)

        return data
    

    def get_stations_aemet(self, write):
        """
        Retrieves information about weather stations from AEMET API.

        Args:
            write (bool): Whether to write the data to a CSV file.

        Returns:
            pandas.DataFrame or None: DataFrame containing station information or None if retrieval fails.
        """
        api_key = open(self.config["DirResources"]["api_AEMET"]).read().strip()
        querystring = {"api_key": api_key}

        url = self.obj_url.get_url_AEMET_stations()
        headers = querystring

        response = requests.get(url, headers = headers)
        if response.status_code == 200:
            data = response.json()
            data_url = data['datos']
            data_response = requests.get(data_url)

            if data_response.status_code == 200:
                df = data_response.json()
                df = pd.DataFrame(df.copy())

                # Reformat coordinates
                df['X'] = df['latitud'].apply(self.reformat_coords)
                df['Y'] = df['longitud'].apply(self.reformat_coords)

                # Select relevant columns
                df = df[['indicativo', 'provincia', 'nombre', 'X', 'Y', 'altitud']]
                df = df.rename(
                    columns = {'indicativo': 'id', 'provincia': 'Provincia', 'nombre': 'Nombre', 'altitud': 'Z'})
                df = df[['id', 'Provincia', 'Nombre', 'X', 'Y', 'Z']]

                if write == True:
                    df.to_csv(self.config["DirResources"]["estaciones"], encoding = 'ISO-8859-1', sep = ',', index = False)
                else:
                    pass
                
                return df
            
            else:
                print("Error fetching station data:", data_response.status_code)
                return None
        else:
            print("Error fetching station data:", response.status_code)
            return None