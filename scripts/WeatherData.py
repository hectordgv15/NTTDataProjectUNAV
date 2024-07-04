# Libraries
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np

import yaml

from UrlDefinition import UrlDefinition

from Utils import Utils

from tqdm import tqdm
import time
import os

import openmeteo_requests
import requests_cache
from openmeteo_requests import Client as OpenMeteoClient
from retry_requests import retry


class WeatherAPI:
    def __init__(self):
        """
        Initialize WeatherAPI object.
        """
        self.load_config()
        self.obj_url = UrlDefinition()
        self.api_key = open(self.config["DirResources"]["api_OWM"]).read().strip()
        self.func = Utils()


    # Load external parameters
    def load_config(self, config_path = "config.yml"):
        """
        Load external parameters from a YAML configuration file.

        Args:
            config_path (str): Path to the YAML configuration file.

        Returns:
            None
        """
        # Get config path
        if not os.path.exists(config_path):
            config_path = os.path.join("../scripts", config_path)

        # Read and parse config file
        with open(config_path, "r") as file:
            config = yaml.load(file, Loader = yaml.FullLoader)

        self.config = config


    def get_history_owm(self, lat, lon, start, end, freq = 'H'):
        """
        Retrieve historical weather data from OpenWeatherMap API.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            start (str): Start date and time in the format 'YYYY-MM-DD HH:MM:SS'.
            end (str): End date and time in the format 'YYYY-MM-DD HH:MM:SS'.
            freq (str): Frequency of the data ('H' for hourly, 'D' for daily).

        Returns:
            pandas.DataFrame: DataFrame containing historical weather data.
        """
        start_date = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

        all_data_frames = []

        # Split time range into 1 day intervals
        interval = timedelta(days = self.config["IntervalOWM"]["interval"])
        current_start = start_date

        # Progress bar
        total_iterations = int((end_date - start_date).total_seconds() / interval.total_seconds())

        time.sleep(1)

        progress_bar = tqdm(total = total_iterations, desc = 'Downloading Data', unit = ' interval')

        while current_start < end_date:
            # Calculate the end date of the current interval
            current_end = min(current_start + interval, end_date)

            start_unix = int(current_start.timestamp())
            end_unix = int(current_end.timestamp())

            data_frame = self._fetch_weather_data_single_owm(lat, lon, start_unix, end_unix)

            all_data_frames.append(data_frame)

            # Update start date for next interval
            current_start += interval

            progress_bar.update(1)

        progress_bar.close()

        result = pd.concat(all_data_frames, ignore_index = True)

        # Clean data
        result = self.func.basic_clean(result)

        # If there are some missing values left
        if result.isnull().sum().sum() > 0:
            result = result.fillna(method = 'bfill')

        result = result.dropna(axis = 1, how = 'all')

        if freq == 'D':
            # Create dictionaries for aggregate columns
            cat_dict = {}
            number_dict = {}

            for col in result.columns:
                if result[col].dtype == 'object' or result[col].dtype == 'string':
                    cat_dict[col] = 'last'
                elif result[col].dtype == 'float64' or result[col].dtype == 'int64':
                    number_dict[col] = 'median'

            # Combine results
            transform_variables = {**number_dict, **cat_dict}

            # Group information
            result = result.groupby(pd.Grouper(key = 'Fecha', freq = 'D')).agg(transform_variables).reset_index()

        return result


    def get_forecast_owm(self, lat, lon, freq = 'H'):
        """
        Retrieve forecast weather data from OpenWeatherMap API.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            freq (str): Frequency of the data ('H' for hourly, 'D' for daily).

        Returns:
            pandas.DataFrame: DataFrame containing forecast weather data.
        """
        result = self._fetch_weather_data_single_owm(lat, lon)

        # Clean data
        result = self.func.basic_clean(result)

        # If there are some missing values left
        if result.isnull().sum().sum() > 0:
            result = result.fillna(method = 'bfill')

        result = result.dropna(axis = 1, how = 'all')

        if freq == 'D':
            # Create dictionaries for aggregate columns
            cat_dict = {}
            number_dict = {}

            for col in result.columns:
                if result[col].dtype == 'object' or result[col].dtype == 'string':
                    cat_dict[col] = 'last'
                elif result[col].dtype == 'float64' or result[col].dtype == 'int64':
                    number_dict[col] = 'median'

            # Combine results
            transform_variables = {**number_dict, **cat_dict}

            # Group information
            result = result.groupby(pd.Grouper(key = 'Fecha', freq = 'D')).agg(transform_variables).reset_index()


        return result


    def _fetch_weather_data_single_owm(self, lat, lon, start = None, end = None):
        """
        Fetch weather data from OpenWeatherMap API for a single location.

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            start (int): Start timestamp for historical data retrieval.
            end (int): End timestamp for historical data retrieval.

        Returns:
            pandas.DataFrame: DataFrame containing weather data.
        """

        if start and end:
            url = self.obj_url.get_url_owm_history_hourly(lat, lon, start, end, self.api_key)
        else:
            url = self.obj_url.get_url_owm_forecast_hourly(lat, lon, self.api_key)

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            data_rows = []

            for entry in data['list']:

                timestamp = entry['dt']
                fecha = datetime.utcfromtimestamp(timestamp)

                # Extract all data in the json file
                row = {'date': fecha,
                       **entry.get('main', {}),
                       **entry.get('wind', {}),
                       **entry.get('clouds', {}),
                       **entry.get('rain', {}),
                       **entry.get('snow', {})
                       }

                # Add weather categorical values
                weather_data = entry.get('weather', [{}])[0]
                row.update(weather_data)

                data_rows.append(row)

                df_consolidated = pd.DataFrame(data_rows)


            return df_consolidated

        else:

            raise Exception("Error:", response.status_code)


    def get_history_aemet(self, start_date, end_date, st):
        """
        Retrieve historical weather data from AEMET API.

        Args:
            start_date (str): Start date for historical data retrieval (format: 'YYYY-MM-DD').
            end_date (str): End date for historical data retrieval (format: 'YYYY-MM-DD').
            st (str): Station code for the weather station.

        Returns:
            pandas.DataFrame: DataFrame containing historical weather data.
        """
        # Set query parameters
        api_key = open(self.config["DirResources"]["api_AEMET"]).read().strip()

        querystring = {"api_key": api_key}
        
        url = self.obj_url.get_url_AEMET_history_daily(start_date, end_date, st)
        
        headers = querystring
        
        # First url call
        response = requests.get(url, headers = headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Fetch data from secondary URL
            datos_url = data['datos']
            
            data_response = requests.get(datos_url)
            
            if data_response.status_code == 200:
                
                aemet_data = pd.DataFrame(data_response.json())
            
                aemet_data['fecha'] = pd.to_datetime(aemet_data['fecha'])
                aemet_data = aemet_data.rename(columns = {'fecha': 'Fecha'})
                
                # Identify numerical columns and in time format
                cols_numericas = ['altitud', 'tmed', 'prec', 'tmin', 'tmax', 'velmedia', 'racha', 'hrMedia', 'hrMax', 'hrMin']
                for col in cols_numericas:
                    aemet_data[col] = aemet_data[col].str.replace(',', '.').astype(float)
                
                cols_horas = ['horatmin', 'horatmax', 'horaracha', 'horaHrMax', 'horaHrMin']
                for col in cols_horas:
                    aemet_data[col] = aemet_data[col].apply(lambda x: 0 if x == '24:00' or x == 'Varias' else pd.to_datetime(x, format = '%H:%M').hour + pd.to_datetime(x, format = '%H:%M').minute / 60)
                
                cols_texto = ['indicativo', 'nombre', 'provincia', 'dir']
                for col in cols_texto:
                    aemet_data[col] = aemet_data[col].str.strip()
                    
                
                # Make a basic clean over the data    
                aemet_data = self.func.basic_clean(aemet_data, 'D')

                return aemet_data
            
            else:
                print("Error fetching data:", data_response.status_code)
                return None
        else:
            print("Error fetching data:", response.status_code)
            return None
        
        
    def get_openmeteo_client(self):
        """
        Function to create and return an OpenMeteoClient instance with a retry-enabled session.

        This function initializes a CachedSession to cache requests and wraps it with retry logic 
        to handle transient errors gracefully.

        Returns:
        - OpenMeteoClient: Instance of OpenMeteoClient configured with retry-enabled session.
        """
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        
        return OpenMeteoClient(session = retry_session)
    

    def process_response(self, response, variables):
        """
        Process the response received from OpenMeteoClient into a DataFrame.

        Args:
        - response: The response object from OpenMeteoClient.
        - variables: List of variables to be processed.

        Returns:
        - DataFrame: Processed data with variables as columns and timestamps as index.
        """
        
        # Extract hourly data for each variable from the response and store it in a dictionary
        hourly_data = {var: response.Hourly().Variables(idx).ValuesAsNumpy() for idx, var in enumerate(variables)}
                
        # Convert start and end times to datetime objects in UTC timezone
        start_time = pd.to_datetime(response.Hourly().Time(), unit = "s", utc = True)
        end_time = pd.to_datetime(response.Hourly().TimeEnd(), unit = "s", utc = True)
        interval = pd.Timedelta(seconds = response.Hourly().Interval())
        
        # Generate a date range using start and end times with the calculated interval.
        hourly_data["date"] = pd.date_range(start = start_time, end = end_time, freq = interval, inclusive = 'left')
        
        df = pd.DataFrame(hourly_data)
        
        # Correct the time zone
        df["date"] = pd.to_datetime(df['date']).dt.tz_convert('Europe/Madrid').dt.strftime('%Y-%m-%d %H:%M:%S')

        
        # Reorder columns with 'date' as the first column.
        columnas = df.columns.tolist()
        columnas = ['date'] + [col for col in columnas if col != 'date']
        df = df[columnas]
        
        # Clean data
        df = self.func.basic_clean(df, freq = 'H')
        
        return df
        

    def get_hourly_history_ometeo(self, lat, lon, start_date, end_date):
        """
        Retrieve hourly historical weather data from OpenMeteo for a specified location and time period.

        Args:
        - lat: Latitude of the location.
        - lon: Longitude of the location.
        - start_date: Start date of the data period (format: "YYYY-MM-DD").
        - end_date: End date of the data period (format: "YYYY-MM-DD").

        Returns:
        - DataFrame: Hourly historical weather data for the specified location and time period.
        """
        # Get an OpenMeteoClient instance
        openmeteo = self.get_openmeteo_client()
        
        # Define variables
        variables = [
            'temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'apparent_temperature', 'rain', 
            'snowfall', 'snow_depth', 'pressure_msl', 'surface_pressure', 'cloud_cover',
            'cloud_cover_low', 'cloud_cover_mid', 'cloud_cover_high', 'et0_fao_evapotranspiration', 
            'vapour_pressure_deficit', 'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m', 
            'sunshine_duration', 'shortwave_radiation', 'direct_radiation', 'diffuse_radiation', 
            'direct_normal_irradiance', 'global_tilted_irradiance', 'terrestrial_radiation', 'shortwave_radiation_instant', 
            'direct_radiation_instant', 'diffuse_radiation_instant', 'direct_normal_irradiance_instant', 
            'global_tilted_irradiance_instant', 'terrestrial_radiation_instant', 'soil_temperature_0_to_7cm', 
            'soil_moisture_7_to_28cm'
            ]
        
        url = self.obj_url.get_url_history_ometeo()
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": variables,
            "timezone": "auto",
            "models": "best_match"
        }
        
        # Retrieve responses from OpenMeteo API
        
        # Iterate to avoid error due to excessive API calls
        max_attempts = 5
        attempts = 0
        
        while attempts < max_attempts:
            try:
                responses = openmeteo.weather_api(url, params = params)
                
                # Print metadata information
                print(f"Coordinates {responses[0].Latitude()}°N {responses[0].Longitude()}°E")
                print(f"Elevation {responses[0].Elevation()} m asl")
                print(f"Timezone {responses[0].Timezone()} {responses[0].TimezoneAbbreviation()}")
                print(f"Timezone difference to GMT+0 {responses[0].UtcOffsetSeconds()} s")
                
                return self.process_response(responses[0], variables)
            
            except Exception as e:
                attempts += 1
                print(f"Ocurrió un error: {e}. Intento {attempts} de {max_attempts}")
                if attempts < max_attempts:
                    print("Esperando 70 segundos antes de reintentar...")
                    time.sleep(70)
                else:
                    print("Se alcanzó el máximo de intentos permitidos.")
                    raise
            

    def get_perm_hourly_forecast_ometeo(self, lat, lon):
        """
        Retrieve permanent hourly forecast data from OpenMeteo for a specified location.

        Args:
        - lat: Latitude of the location.
        - lon: Longitude of the location.

        Returns:
        - DataFrame: Permanent hourly forecast data for the specified location.
        """
        
        # Get an OpenMeteoClient instance
        openmeteo = self.get_openmeteo_client()
        
        # Define variables
        variables = [
            "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
            "rain", "snowfall", "snow_depth", "pressure_msl", "surface_pressure",
            "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "et0_fao_evapotranspiration", 
            "vapour_pressure_deficit", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", 
            "sunshine_duration", "shortwave_radiation", "direct_radiation", "diffuse_radiation", "direct_normal_irradiance",
            "global_tilted_irradiance", "terrestrial_radiation", "shortwave_radiation_instant",
            "direct_radiation_instant", "diffuse_radiation_instant", "direct_normal_irradiance_instant",
            "global_tilted_irradiance_instant", "terrestrial_radiation_instant"
        ]
        
        url = self.obj_url.get_url_forecast_ometeo()
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": variables,
            "timezone": "auto",
            "past_days": 2,
            "models": "best_match",
            "forecast_days": 14
        }
        
        # Retrieve responses from OpenMeteo API
        
        # Iterate to avoid error due to excessive API calls
        max_attempts = 5
        attempts = 0
        
        while attempts < max_attempts:
            try:
                responses = openmeteo.weather_api(url, params = params)
        
                # Print metadata information
                print(f"Coordinates {responses[0].Latitude()}°N {responses[0].Longitude()}°E")
                print(f"Elevation {responses[0].Elevation()} m asl")
                print(f"Timezone {responses[0].Timezone()} {responses[0].TimezoneAbbreviation()}")
                print(f"Timezone difference to GMT+0 {responses[0].UtcOffsetSeconds()} s")
                
                return self.process_response(responses[0], variables)
            
            except Exception as e:
                attempts += 1
                print(f"Ocurrió un error: {e}. Intento {attempts} de {max_attempts}")
                if attempts < max_attempts:
                    print("Esperando 70 segundos antes de reintentar...")
                    time.sleep(70)
                else:
                    print("Se alcanzó el máximo de intentos permitidos.")
                    raise


    def get_alt_hourly_forecast_ometeo(self, lat, lon):
        """
        Retrieve alternative hourly forecast data from OpenMeteo for a specified location.

        This function fetches hourly forecast data for soil temperature and soil moisture 
        from the ECMWF model.

        Args:
        - lat: Latitude of the location.
        - lon: Longitude of the location.

        Returns:
        - DataFrame: Hourly forecast data for soil temperature and soil moisture for the specified location.
        """
        
        # Get an OpenMeteoClient instance
        openmeteo = self.get_openmeteo_client()
        
        # Define variables to be retrieved
        variables = [
            "soil_temperature_0_to_7cm", "soil_moisture_7_to_28cm"
        ]
        
        url = self.obj_url.get_url_forecast_ometeo_alt()
        
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": variables,
            "timezone": "auto",
            "past_days": 2,
            "models": "best_match",
            "forecast_days": 14
        }
        
        # Retrieve responses from OpenMeteo API
        
        # Iterate to avoid error due to excessive API calls
        max_attempts = 5
        attempts = 0
        
        while attempts < max_attempts:
            try:
                responses = openmeteo.weather_api(url, params = params)
                
                # Print metadata information
                print(f"Coordinates {responses[0].Latitude()}°N {responses[0].Longitude()}°E")
                print(f"Elevation {responses[0].Elevation()} m asl")
                print(f"Timezone {responses[0].Timezone()} {responses[0].TimezoneAbbreviation()}")
                print(f"Timezone difference to GMT+0 {responses[0].UtcOffsetSeconds()} s")
                
                return self.process_response(responses[0], variables)
            
            except Exception as e:
                attempts += 1
                print(f"Ocurrió un error: {e}. Intento {attempts} de {max_attempts}")
                if attempts < max_attempts:
                    print("Esperando 70 segundos antes de reintentar...")
                    time.sleep(70)
                else:
                    print("Se alcanzó el máximo de intentos permitidos.")
                    raise


    def get_hourly_forecast_ometeo(self, lat, lon):
        """
        Retrieve hourly forecast data from both permanent and alternative sources and merge them.

        This function combines hourly forecast data obtained from two different sources:
        1. Permanent forecast data retrieved using the 'get_perm_hourly_forecast_ometeo()' function.
        2. Alternative forecast data retrieved using the 'get_alt_hourly_forecast_ometeo()' function.

        Args:
        - lat: Latitude of the location.
        - lon: Longitude of the location.

        Returns:
        - DataFrame: Merged hourly forecast data from both sources.
        """
        df1 = self.get_perm_hourly_forecast_ometeo(lat, lon)
        df2 = self.get_alt_hourly_forecast_ometeo(lat, lon)
        
        df = pd.merge(df1, df2, on = 'date', how = 'left')
        
        # Clean data
        df = self.func.basic_clean(df)
        
        return(df)