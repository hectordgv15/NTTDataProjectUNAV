# Libraries
import requests
import pandas as pd

from io import StringIO
import warnings

from UrlDefinition import UrlDefinition

import yaml

from datetime import datetime, timedelta

# Web scraping modules
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

from bs4 import BeautifulSoup

from Utils import Utils

import os


class FlowData:
    """
    Class responsible for managing flow data for a specific station.
    """

    def __init__(self, station):
        """
        Initializes FlowData object with a station name.

        Args:
            station (str): Name of the station.
        """
        self.station = station
        self.func = Utils()
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
        

    def read_csv_data(self, year):
        """
        Reads CSV data for a specified year, performs data cleaning, and returns a DataFrame.

        Args:
            year (int): Year for which CSV data is to be retrieved.

        Returns:
            pandas.DataFrame: DataFrame containing cleaned CSV data.
        """
        # Obtains CSV URL
        warnings.filterwarnings('ignore')
        
        url = self.obj_url.get_url_csv(self.station, year_csv = year)
        response = requests.get(url, verify = False)

        # Checks if request was successful
        if response.status_code != 200:
            print("Enlace erroneo", response.status_code)
            return None

        # Creates a StringIO object from response content
        csv_content = StringIO(response.text)
        try:
            df = pd.read_csv(csv_content, on_bad_lines = 'skip', sep = ',')
        except:
            df = pd.read_csv(csv_content, sep = ';')

        # Filters rows based on date format
        date_filter = df.iloc[:, 0].astype(str).str.contains(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", regex = True)
        s_index, e_index = date_filter.idxmax(), date_filter[::-1].idxmax()
        df = df.loc[s_index:e_index].reset_index(drop = True)

        df.columns = ['data']
        # Splits 'data' column into 'date', 'unknown', 'flow'
        df[['date', 'unknown', 'flow']] = df['data'].str.split('\t', expand = True)

        # Checks if 'flow' has valid data
        if len(df['flow'].unique()) == 1:
            print("Datos disponibles para descarga pero sin información")
            return None

        # Converts columns to appropriate types
        df['date'] = pd.to_datetime(df['date'])
        df['flow'] = df['flow'].astype('float64')
        df = df[['date', 'flow']].copy()

        # Basic data cleaning
        df = self.func.basic_clean(df)
        return df
     
            
    def complete_csv_data(self):
        """
        Retrieves and concatenates CSV data for multiple years, performs data cleaning, and returns a DataFrame.

        Returns:
            pandas.DataFrame: DataFrame containing concatenated and cleaned CSV data.
        """
        data_years = self.config["CSVyears"]["years"]
        df_list = []

        # Reads CSV data for each year
        try:
            for year in data_years:
                df = self.read_csv_data(year)
                if df is not None:
                    df_list.append(df)
        except:
            pass

        if not df_list:
            print("No hay datos disponibles para el año especificado.")
            return pd.DataFrame()

        # Concatenates data from all years
        df_concat = pd.concat(df_list).reset_index(drop = True).sort_values(by = 'date', ascending = True)

        try:
            # Reads auxiliary data
            aux_data = pd.read_csv(self.obj_url.get_dir_auxdata(self.station), encoding = 'ISO-8859-15', on_bad_lines = 'skip', sep = ';')
            date_filter = aux_data.iloc[:, 0].astype(str).str.contains(r"\d{2}/\d{2}/\d{4}", regex = True)
            s_index, e_index = date_filter.idxmax(), date_filter[::-1].idxmax()
            aux_data = aux_data.loc[s_index:e_index].reset_index(drop = True)

            aux_data.columns = ['data']
            
            # Splits 'data' column into 'date', 'Hora', 'flow'
            aux_data[['date', 'Hora', 'flow']] = aux_data['data'].str.split('\t', expand = True)
            aux_data['date'] = pd.to_datetime(aux_data['date'] + ' ' + aux_data['Hora'], format = "%d/%m/%Y %H:%M:%S")
            aux_data = aux_data[['date', 'flow']].copy()
            aux_data['flow'] = aux_data['flow'].astype('string').str.replace(',', '.').astype('float64')

            # Basic data cleaning
            aux_data = self.func.basic_clean(aux_data)
            df_concat = pd.concat([df_concat, aux_data], axis = 0)
        except Exception as e:
            print("Error leyendo la tabla de datos auxiliar:", e)

        # Removes duplicates and performs final cleaning
        df_concat = df_concat.drop_duplicates(subset = 'date', keep = 'first').reset_index(drop = True)
        df_concat = self.func.basic_clean(df_concat)
        
        return df_concat


    def real_time_data(self):
        """
        Retrieves real-time data, performs scraping, and returns a DataFrame.

        Returns:
            pandas.DataFrame: DataFrame containing real-time data.
        """
        try:
            # Browser setup
            chrome_options = Options()
            
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-web-security')
            
            caps = chrome_options.to_capabilities()
            caps["acceptInsecureCerts"] = True
            
            service = Service(ChromeDriverManager().install())
            
            driver = webdriver.Chrome(service = service, options = chrome_options, desired_capabilities = caps)

            url = self.obj_url.get_url_realtime(self.station)
            
            driver.get(url)  # Opens URL in browser

            # Clicks on necessary elements
            caudal_botton = driver.find_element(By.XPATH,
                                                '//a[@class="mdi mdi-chart-histogram" and contains(@href, "xATVRFUR")]')
            caudal_botton.click()

            valores_button = driver.find_element(By.XPATH, '//a[text()="Valores"]')
            valores_button.click()

            wait = WebDriverWait(driver, 5)
            wait.until(lambda driver: driver.find_element(By.ID, 'DataTables_Table_0'))

            select_element = Select(driver.find_element(By.NAME, 'DataTables_Table_0_length'))
            select_element.select_by_value('-1')

            table_element = driver.find_element(By.ID, 'DataTables_Table_0')
            table_html = table_element.get_attribute('outerHTML')

            # Scrapes table data
            soup = BeautifulSoup(table_html, 'html.parser')
            rows = []
            for row in soup.find_all('tr'):
                cols = []
                for col in row.find_all(['th', 'td']):
                    cols.append(col.get_text().replace(',', '.'))
                rows.append(cols)

            # Creates DataFrame from scraped data
            df = pd.DataFrame(rows[1:], columns = rows[0])
            df.columns = ['date', 'flow']

            # Date handling
            for i in range(len(df)):
                try:
                    df.loc[i, 'date'] = datetime.strptime(df.loc[i, 'date'], "%d/%m/%Y %H:%M")
                except Exception as e:
                    print("Ocurrió un error:", e)

            df['date'] = pd.to_datetime(df['date'])
            df['flow'] = df['flow'].astype('float64')

            # Basic cleaning
            df = self.func.basic_clean(df)

            driver.quit()
            
            return df

        except Exception as e:
            print("Ocurrió un error:", e)
            

    def unified_data(self, replace_missings = True):
        """
        Combines historical and real-time data, performs data cleaning, and returns a unified DataFrame.

        Args:
            replace_missings (str, optional): Whether to replace missings or not.

        Returns:
            pandas.DataFrame: DataFrame containing unified and cleaned data.
        """
        try:
            # Load all data from pre defined functions
            hist_data = self.complete_csv_data()
            
            if isinstance(hist_data, pd.DataFrame) and hist_data.shape[0] > 1:
                rtime_data = self.real_time_data()
                
                # Concat the information
                df_u = pd.concat([hist_data, rtime_data])
                
                df_u = df_u.drop_duplicates(keep = 'first').reset_index(drop = True)
                
                # Define a range of dates for the entire dataframe
                df = pd.DataFrame({'date': pd.date_range(start = df_u.loc[0, 'date'], 
                                                          end = df_u.loc[len(df_u) - 1, 'date'], 
                                                          freq = 'H')}
                                  )
                
                
                df = pd.merge(df, df_u, on = 'date', how = 'left')
                df = df.reset_index(drop = True)
                
                # Mising data            
                missing_start = hist_data.loc[len(hist_data) - 1, 'date']
                missing_end = rtime_data.loc[0, 'date']
                
                if replace_missings == True:
                    
                    if (missing_end - missing_start).days > 1:
                    
                        # Year to take the values for the replacement, take the values from the last year
                        days_year_values = 365
                                
                        # Replace the data with with the last year information
                        year_index = (df['date'] > (missing_start - timedelta(days = days_year_values))) & (df['date'] < (missing_end - timedelta(days = days_year_values)))
                        df.loc[df['flow'].isnull(), 'flow'] = df.loc[year_index, 'flow'].values
                        df = df.sort_values(by = 'date', ascending = True).reset_index(drop = True)
                        df = self.func.basic_clean(df)
                        
                    else:
                        df = self.func.basic_clean(df)
                    
                else:
                    # If the missing data is not more than one day, replace it with the previous data
                    df = df.sort_values(by = 'date', ascending = True).reset_index(drop = True)
        
                return(df)            
            
            else:
                print("No hay información histórica para unificar con los datos en tiempo real")
                
        except Exception as e:
            print("Ocurrió un error:", e)