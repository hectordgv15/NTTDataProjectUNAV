class UrlDefinition:
    """
    Class for defining URLs for various data sources.
    """

    def __init__(self):
        pass

    def get_url_csv(self, station_code, year_csv):
        """
        Generates URL for CSV files based on station code and year.

        Args:
            station_code (str): Code of the station.
            year_csv (int): Year of the CSV file.

        Returns:
            str: URL for the CSV file.
        """
        self._url_csv = f"https://www.saihduero.es/historico-risr-csv?f={station_code}_AH{year_csv}_HQ.csv"
        return self._url_csv

    def get_url_realtime(self, station_code):
        """
        Generates URL for real-time data based on station code.

        Args:
            station_code (str): Code of the station.

        Returns:
            str: URL for real-time data.
        """
        self._url_realtime = f"https://www.saihduero.es/ficha-risr?r=EA{str(station_code)[-3:]}"
        return self._url_realtime

    def get_url_gauges_reservoirs(self, station_code, complement):
        """
        Generates URL for gauges and reservoirs data based on station code and complement.

        Args:
            station_code (str): Code of the station.
            complement (str): Additional information for the URL.

        Returns:
            str: URL for gauges and reservoirs data.
        """
        self._url_gauges_reservoirs = f"https://www.saihduero.es/risr/{complement}{station_code:03d}"
        return self._url_gauges_reservoirs

    def get_url_OWM_history_hourly(self, lat, lon, start, end, api_key):
        """
        Generates URL for hourly historical weather data from OpenWeatherMap.

        Args:
            lat (float): Latitude.
            lon (float): Longitude.
            start (str): Start date for data retrieval.
            end (str): End date for data retrieval.
            api_key (str): API key for OpenWeatherMap.

        Returns:
            str: URL for historical hourly weather data.
        """
        self._url_OWM_history_hourly = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&end={end}&appid={api_key}"
        return self._url_OWM_history_hourly

    def get_url_OWM_forecast_hourly(self, lat, lon, api_key):
        """
        Generates URL for hourly weather forecast from OpenWeatherMap.

        Args:
            lat (float): Latitude.
            lon (float): Longitude.
            api_key (str): API key for OpenWeatherMap.

        Returns:
            str: URL for hourly weather forecast.
        """
        self._url_OWM_forecast_hourly = f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&appid={api_key}"
        return self._url_OWM_forecast_hourly

    def get_url_AEMET_history_daily(self, start_date, end_date, st):
        """
        Generates URL for daily historical weather data from AEMET.

        Args:
            start_date (str): Start date for data retrieval.
            end_date (str): End date for data retrieval.
            st (str): Station identifier for AEMET.

        Returns:
            str: URL for daily historical weather data.
        """
        self._url_AEMET_history_daily = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{start_date}T00%3A00%3A00UTC/fechafin/{end_date}T23%3A59%3A59UTC/estacion/{st}"
        return self._url_AEMET_history_daily

    def get_url_AEMET_stations(self):
        """
        Generates URL for retrieving AEMET weather stations.

        Returns:
            str: URL for AEMET weather stations.
        """
        self._url_AEMET_stations = f"https://opendata.aemet.es/opendata/api/valores/climatologicos/inventarioestaciones/todasestaciones/"
        return self._url_AEMET_stations
    
    
    def get_url_history_ometeo(self):
        """
        Generates URL for retrieving history weather.

        Returns:
            str: URL for Open Meteo weather data.
        """
        self._url_history_ometeo = "https://archive-api.open-meteo.com/v1/archive"
        return self._url_history_ometeo
    
    
    def get_url_forecast_ometeo(self):
        """
        Generates URL for retrieving forecast weather.

        Returns:
            str: URL for Open Meteo weather forecast data.
        """
        self._url_forecast_ometeo = "https://api.open-meteo.com/v1/forecast"
        return self._url_forecast_ometeo
    
    
    def get_url_forecast_ometeo_alt(self):
        """
        Generates URL for retrieving alternative forecast weather.

        Returns:
            str: URL for Open Meteo weather forecast data.
        """
        self._url_forecast_ometeo_alt = "https://api.open-meteo.com/v1/ecmwf"
        return self._url_forecast_ometeo_alt
    
    def get_dir_auxdata(self, station_code):
        """
        Generates the directory name for retrieving auxiliar flow data.

        Returns:
            str: Dirname for auxiliar flow data.
        """
        
        self._dir_aux_data = f"../resources/aux data/0{station_code}.Q.Q.60.Med.csv"
        return self._dir_aux_data
    
    

