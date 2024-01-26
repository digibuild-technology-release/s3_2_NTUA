from sqlalchemy import create_engine
import pandas as pd


PG_HOST = "digibuild.epu.ntua.gr"
PG_USERNAME = "digibuild"
PG_PASSWORD = "digibuild"
PG_DATABASE = "s323"
PG_PORT = 5601


class BaseConnector(object):
    def __init__(self,
                 this_host=PG_HOST,
                 this_port=PG_PORT,
                 this_user=PG_USERNAME,
                 this_password=PG_PASSWORD,
                 this_dbname=PG_DATABASE
                 ):
        self.engine = create_engine(
            f"postgresql+psycopg2://{this_user}:{this_password}@{this_host}:{this_port}/{this_dbname}"
        )

    def _get_schema_tables(self):
        table_names = self.engine.table_names()
        return table_names

    def _read_sql_table(self, table_name, query=None):
        if query:
            sql_command = query
        else:
            sql_command = f'SELECT * FROM {table_name}'
        df = pd.read_sql(con=self.engine, sql=sql_command)
        return df

    def _store_df(self, df, table_name):
        df.to_sql(table_name, con=self.engine, if_exists='replace', index=True)

    def _close_connection(self):
        self.engine.dispose()