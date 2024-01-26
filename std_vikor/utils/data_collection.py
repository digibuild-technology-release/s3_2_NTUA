from postgre_connector import BaseConnector
import sys
import os
import logging
import requests
import json
import pandas as pd
import settings
import warnings
from datetime import timedelta

# SETTINGS CELL

DATA_SHARING_URL = f"{settings.PROTOCOL}://{settings.API_HOST}/data_sharing/federated_querying/execute_query/"


IAQ_DATA_LIST = ['heron_domxem3_3494546ec9f0']

IAQ_COLUMN_LIST = ['datetime', 'energy_0', 'energy_1', 'energy_2']

FEATURES_NEEDED = ['datetime', 'energy_0', 'energy_1', 'energy_2']

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def gen_token():
    url = "http://digibuild.epu.ntua.gr/auth/realms/DIGIBUILD/protocol/openid-connect/token"
    payload = f'grant_type=password&client_id=data_sharing&client_secret=20883f27-8f3c-4826-b908-c099b5ab279e&scope=openid&username={USERNAME}&password={PASSWORD}'
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
    response=requests.request("POST", url, headers=headers, data=payload)
    response_json=json.loads(response.text)
    return response_json['access_token']
class DataSharing(object):
    def __init__(self):
        self.url = DATA_SHARING_URL
        self.headers = {'Content-Type': 'application/json'}

    def _execute_query(self, table_name, access_token, features=None):
        self.headers['Authorization'] = f"Bearer {access_token}"
        if features is None:
            query = f"SELECT * FROM {settings.CATALOG}.{settings.SCHEMA}.{table_name}"
        else:
            columns_str = ", ".join(features)
            query = f"SELECT {columns_str} FROM {settings.CATALOG}.{setting.SCHEMA}.{table_name}"
        response = requests.post(
            url=self.url,
            data=json.dumps({'query': query}),
            headers=self.headers
        )
        print(response)
        return response

    def _to_df(self, response, column_names=None):
        if response.status_code == 200:
            json_result = response.json()
            df = pd.DataFrame(json_result)
            if column_names:
                df.columns = column_names
        else:
            df = pd.DataFrame()
        return df

class DataObject(DataSharing):
    def __init__(self, features=None):
        super().__init__()
        self.features_needed = features

    def _load(self, table_names, access_token):
        list_of_dfs = []
        i = 1
        for table in table_names:
            print(i)
            log.info(f"load data for {table}")

            response = self._execute_query(
                table,
                access_token=access_token,
                features=self.features_needed
            )
            df = self._to_df(
                response,
                column_names=None
            )
            #df['n_sensor'] = table
            print(df)

            if df.empty:
                continue
            else:
                list_of_dfs.append(df)
            i += 1
        all_data = list_of_dfs
        print(all_data)
        #all_data = pd.concat(list_of_dfs)
        #all_data['DATE'] = pd.to_datetime(all_data['date'])
        return all_data


def data_collection():
    data_object = DataObject()
    access_token = gen_token()
    all_ieecp_ac_rooms = data_object._load(table_names=IAQ_DATA_LIST, access_token=access_token)
    print(all_ieecp_ac_rooms)


def collect_isp_data(
        connector,
        date
):
    connector._read_sql_table('greek_tso_isp2', query="SELECT * FROM greek_tso_isp2 WHERE index")



def get_ISP2_file(date):
    '''
        function that collects ISP Data from greek TSO and extracts data from it.

        params:
            date: datetime current date

        returns
            if response.status == 200:
                dataframe['datetime'(index), 'load', "losses", "res", "hydro"]
            else:
                empty Dataframe
    '''

    file_date = date
    url = f'https://www.admie.gr/sites/default/files/attached-files/type-file/{file_date.strftime("%Y")}/{file_date.strftime("%m")}/{file_date.strftime("%Y%m%d")}_ISP2Requirements_01.xlsx'

    response = requests.get(url)
    if response.status_code == 200:

        # Save the response content to a file
        with open('file.xlsx', 'wb') as f:
            f.write(response.content)

            # Load the saved XLSX file into a workbook object
            warnings.filterwarnings("ignore", category=UserWarning)
            workbook = openpyxl.load_workbook(filename='file.xlsx')
            warnings.resetwarnings()
            worksheet = workbook.active

            # collect res predictions
            res_list = list([])
            for i in range(1, 49):
                # Access the cell values
                cell_value = worksheet.cell(row=5, column=i + 2).value
                res_list.append(cell_value)
            load_list = list([])
            for i in range(1, 49):
                # Access the cell values
                cell_value = worksheet.cell(row=7, column=i + 2).value
                load_list.append(cell_value)
            loss_list = list([])
            for i in range(1, 49):
                # Access the cell values
                cell_value = worksheet.cell(row=8, column=i + 2).value
                loss_list.append(cell_value)
            hydro_list = list([])
            for i in range(1, 49):
                # Access the cell values
                cell_value = worksheet.cell(row=29, column=i + 2).value
                hydro_list.append(cell_value)

            # Close the workbook
            workbook.close()
            # Delete the Excel file


            # Create dataframe
            start_date = date
            date_range = pd.date_range(start_date, start_date + timedelta(days=1), freq='30min')[:-1]
            df = pd.DataFrame({'load': load_list, "losses": loss_list, "res": res_list, "hydro": hydro_list},
                              index=date_range)
            df = df.resample('1H').sum()
            df.index = df.index.set_names('datetime')

            #os.remove('file.xlsx')
            return df
    else:
        return pd.DataFrame()


data_collection()