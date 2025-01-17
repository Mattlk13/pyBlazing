from enum import IntEnum

import cudf

from .bridge import internal_api

# TODO BIG TODO percy blazing-io didn't expose the wildcard API of FileSystem API


class Type(IntEnum):
    cudf = 0
    pandas = 1
    arrow = 2
    csv = 3
    parquet = 4
    result_set = 5
    distributed_result_set = 6
    json = 7
    orc = 8


class DataSource:

    def __init__(self, client, type, **kwargs):
        self.client = client

        self.type = type

        #remove
        # declare all the possible fields (will be defined in _load)
        self.cudf_df = None  # cudf, pandas and arrow data will be passed/converted into this var
        self.csv = None
        self.parquet = None
        self.path = None

        # init the data source
        self.valid = self._load(type, **kwargs)

    def __repr__(self):
        return "TODO"

    def __str__(self):
        if self.valid == False:
            return 'Invalid datasource'

        type_str = {
            Type.cudf: 'cudf',
            Type.pandas: 'pandas',
            Type.arrow: 'arrow',
            Type.csv: 'csv',
            Type.parquet: 'parquet',
            Type.json: 'json',
            Type.orc: 'orc',
            Type.result_set: 'result_set'
        }

        # TODO percy path and stuff

        return type_str[self.type]

    #def is_valid(self):
    #    return self.valid

    # cudf.DataFrame in-gpu-memory
    def is_cudf(self):
        return self.type == Type.cudf

    # pandas.DataFrame in-memory
    def is_pandas(self):
        return self.type == Type.pandas

    # arrow file on filesystem or arrow in-memory
    def is_arrow(self):
        return self.type == Type.arrow

    # csv file on filesystem
    def is_csv(self):
        return self.type == Type.csv

    # parquet file on filesystem
    def is_parquet(self):
        return self.type == Type.parquet

    # json file on filesystem
    def is_json(self):
        return self.type == Type.json

    # orc file on filesystem
    def is_orc(self):
        return self.type == Type.orc

    # blazing result set handle
    def is_result_set(self):
        return self.type == Type.result_set

    def is_distributed_result_set(self):
        return self.type == Type.distributed_result_set

    def is_from_file(self):
        return self.type == Type.parquet or self.type == Type.csv

    def dataframe(self):
        # TODO percy add more support

        if self.type == Type.cudf:
            return self.cudf_df
        elif self.type == Type.pandas:
            return self.cudf_df
        elif self.type == Type.arrow:
            return self.cudf_df
        elif self.type == Type.result_set:
            return self.cudf_df

        return None

    def schema(self):
        if self.type == Type.csv:
            return self.csv
        elif self.type == Type.parquet:
            return self.parquet
        elif self.type == Type.json:
            return self.json
        elif self.type == Type.orc:
            return self.orc
        elif self.type == Type.cudf:
            return self.cudf_df

        return None

# BEGIN remove
    def _load(self, type, **kwargs):
        table_name = kwargs.get('table_name', None)
        if type == Type.cudf:
            cudf_df = kwargs.get('cudf_df', None)
            return self._load_cudf_df(table_name, cudf_df)
        elif type == Type.pandas:
            pandas_df = kwargs.get('pandas_df', None)
            return self._load_pandas_df(table_name, pandas_df)
        elif type == Type.arrow:
            arrow_table = kwargs.get('arrow_table', None)
            return self._load_arrow_table(table_name, arrow_table)
        elif type == Type.result_set:
            result_set = kwargs.get('result_set', None)
            return self._load_result_set(table_name, result_set)
        elif type == Type.distributed_result_set:
            result_set = kwargs.get('result_set', None)
            return self._load_distributed_result_set(table_name, result_set)
        elif type == Type.csv:
            path = kwargs.get('path', None)
            csv_args = kwargs.get('csv_args', None)
            return self._load_csv(table_name, path, csv_args)
        elif type == Type.parquet:
            table_name = kwargs.get('table_name', None)
            path = kwargs.get('path', None)
            return self._load_parquet(table_name, path)
        elif type == Type.json:
            table_name = kwargs.get('table_name', None)
            path = kwargs.get('path', None)
            json_lines = kwargs.get('json_lines', True)
            return self._load_json(table_name, path, json_lines)
        elif type == Type.orc:
            table_name = kwargs.get('table_name', None)
            path = kwargs.get('path', None)
            orc_args = kwargs.get('orc_args', None)
            return self._load_orc(table_name, path, orc_args)
        else:
            # TODO percy manage errors
            raise Exception("invalid datasource type")

        # TODO percy compare against bz proto Status_Success or Status_Error
        # here we need to use low level api pyblazing.create_table
        return False

    def _load_cudf_df(self, table_name, cudf_df):
        self.cudf_df = cudf_df

        column_names = list(cudf_df.dtypes.index)
        column_dtypes = [internal_api.get_np_dtype_to_gdf_dtype(x) for x in cudf_df.dtypes]
        return_result = internal_api.create_table(
            self.client,
            table_name,
            type = internal_api.SchemaFrom.Gdf,
            names = column_names,
            dtypes = column_dtypes,
            gdf = cudf_df
        )

        # TODO percy see if we need to perform sanity check for cudf_df object
        self.valid = True

        return self.valid

    def _load_pandas_df(self, table_name, pandas_df):
        cudf_df = cudf.DataFrame.from_pandas(pandas_df)

        return self._load_cudf_df(table_name, cudf_df)

    def _load_arrow_table(self, table_name, arrow_table):
        pandas_df = arrow_table.to_pandas()

        return self._load_pandas_df(table_name, pandas_df)

    def _load_result_set(self, table_name, result_set):
        cudf_df = result_set.columns

        return self._load_cudf_df(table_name, cudf_df)

    def _load_distributed_result_set(self, table_name, distributed_result_set):
        print(distributed_result_set)
        internal_api.create_table(
            self.client,
            table_name,
            type = internal_api.SchemaFrom.Distributed,
            resultToken = distributed_result_set[0].resultToken
        )

        self.valid = True

        return self.valid


    def _load_csv(self, table_name, path, csv_args):
        if path == None:
            return False

        self.path = path

        return_result = internal_api.create_table(
            self.client,
            table_name,
            type = internal_api.SchemaFrom.CsvFile,
            path = path,
            csv_args = csv_args
        )

        # TODO percy see if we need to perform sanity check for arrow_table object
        #return success or failed
        self.valid = return_result

        return self.valid

    def _load_parquet(self, table_name, path):
        # TODO percy manage datasource load errors
        if path == None:
            return False

        self.path = path

        return_result = internal_api.create_table(
            self.client,
            table_name,
            type = internal_api.SchemaFrom.ParquetFile,
            path = path
        )

        # TODO percy see if we need to perform sanity check for arrow_table object
        #return success or failed
        self.valid = return_result

        return self.valid

    def _load_json(self, table_name, path, lines):
        # TODO percy manage datasource load errors
        if path == None:
            return False

        self.path = path

        return_result = internal_api.create_table(
            self.client,
            table_name,
            type = internal_api.SchemaFrom.JsonFile,
            path = path,
            lines = lines
        )

        # TODO percy see if we need to perform sanity check for arrow_table object
        #return success or failed
        self.valid = return_result

        return self.valid

    def _load_orc(self, table_name, path, orc_args):
        # TODO percy manage datasource load errors
        if path == None:
            return False

        self.path = path

        return_result = internal_api.create_table(
            self.client,
            table_name,
            type = internal_api.SchemaFrom.OrcFile,
            path = path,
            orc_args = orc_args
        )

        # TODO percy see if we need to perform sanity check for arrow_table object
        #return success or failed
        self.valid = return_result

        return self.valid
#END remove

# BEGIN DataSource builders


def from_cudf(cudf_df, table_name):
    return DataSource(None, Type.cudf, table_name = table_name, cudf_df = cudf_df)

def from_pandas(pandas_df, table_name):
    return DataSource(None, Type.pandas, table_name = table_name, pandas_df = pandas_df)

def from_arrow(arrow_table, table_name):
    return DataSource(None, Type.arrow, table_name = table_name, arrow_table = arrow_table)

def from_result_set(result_set, table_name):
    return DataSource(None, Type.result_set, table_name = table_name, result_set = result_set)

def from_distributed_result_set(result_set, table_name):
    return DataSource(None, Type.distributed_result_set, table_name = table_name, result_set = result_set)

def from_csv(client, table_name, path, csv_args):
    return DataSource(client, Type.csv,
        table_name = table_name,
        path = path,
        csv_args = csv_args
    )

# TODO percy path (with wildcard support) is file system transparent
def from_parquet(client, table_name, path):
    return DataSource(client, Type.parquet, table_name = table_name, path = path)

def from_json(client, table_name, path, lines):
    return DataSource(client, Type.json, table_name = table_name, path = path, json_lines = lines)

def from_orc(client, table_name, path, orc_args):
    return DataSource(client, Type.orc, table_name = table_name, path = path, orc_args = orc_args)
# END DataSource builders
