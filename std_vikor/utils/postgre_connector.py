from sqlalchemy import create_engine
import pandas as pd



class BaseConnector(object):
    def __init__(self,
                 this_host,
                 this_port,
                 this_user,
                 this_password,
                 this_dbname
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

    def _replace_df(self, df, table_name):
        df.to_sql(table_name, con=self.engine, if_exists='replace', index=True)

    def _close_connection(self):
        self.engine.dispose()