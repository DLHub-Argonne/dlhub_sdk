import pandas as pd

from dlhub_sdk.models import BaseMetadataModel
from dlhub_sdk.utils.types import simplify_numpy_dtype


class Dataset(BaseMetadataModel):
    """Base class for describing a dataset

    The Dataset class and any of its subclasses contain operations
    for describing what a dataset is and how to use it.
    """

    def __init__(self):
        super(Dataset, self).__init__()

        # Add the datacite type as Dataset
        self._output['datacite']['resourceType'] = {'resourceTypeGeneral': 'Dataset'}

        # Initialize the "dataset" block
        self._output['dataset'] = {}

        # Add dataset type to dlhub block
        self._output['dlhub']['type'] = 'dataset'


class TabularDataset(Dataset):
    """Read a dataset stored as a single file in a tabular format.

    Will read in the names of the columns, and allow users to associate
    column names with descriptions of the data provided.

    This class is compatible with any data format readable by the Pandas
    library. See the list of
    `read functions in Pandas <https://pandas.pydata.org/pandas-docs/stable/io.html>`_
    """

    @classmethod
    def create_model(cls, path, format="csv", read_kwargs=None):
        """Initialize the description of a tabular dataset

        Args:
            path (string): Path to dataset
            format (string): Format of the dataset. We support all of the
                read operations of Pandas (e.g., read_csv). Provide the format
                of your dataset as the suffix for the Pandas read command (e.g.,
                "csv" for "read_csv").
            read_kwargs (dict): Any keyword arguments for the pandas read command
        """
        output = cls()
        if read_kwargs is None:
            read_kwargs = {}
        output.load_dataset(path, format, **read_kwargs)
        return output

    def load_dataset(self, path, format, **kwargs):
        """Load in a dataset to get some high-level descriptions of it

        Args:
            path (string): Path to dataset
            format (string): Format of the dataset. We support all of the
                read operations of Pandas (e.g., read_csv). Provide the format
                of your dataset as the suffix for the Pandas read command (e.g.,
                "csv" for "read_csv").
            **kwargs (dict): arguments for the Pandas read function
        """

        # Add the data as the path of interest
        self.add_file(path, 'data')

        # Store the format information
        self._output["dataset"]["format"] = format
        self._output["dataset"]["read_options"] = kwargs

        # Read in the data
        read_fun = getattr(pd, 'read_{}'.format(format))
        data = read_fun(path, **kwargs)
        self._output["dataset"]["columns"] = [
            {'name': c, 'type': simplify_numpy_dtype(d)}
            for c, d in zip(data.columns, data.dtypes)
        ]

        # Zero out the input and output columns
        for x in ["inputs", "labels"]:
            if x in self._output["dataset"]:
                del self._output["dataset"][x]

    def annotate_column(self, column_name, description=None, data_type=None, units=None):
        """Provide documentation about a certain column within a dataset.

        Overwrites any type values inferred from reading the dataset

        Args:
            column_name (string): Name of a column
            description (string): Longer description of a column
            data_type (string): Short description of the data type
            units (string): Units for the columns data (if applicable)
        """
        column = self._get_column(column_name)
        if description is not None:
            column['description'] = description
        if data_type is not None:
            column['type'] = data_type
        if units is not None:
            column['units'] = units
        return self

    def get_unannotated_columns(self):
        """Get the names of columns that have not been described"""

        return [x["name"] for x in self["dataset"]["columns"] if "description" not in x]

    def _get_column(self, column_name):
        """Gets the metadata for a certain column

        Args:
            column_name (string): Name of column to be altered
        Returns:
            (dict) Column metadata. The editable object, not a copy
            """
        for column in self._output["dataset"]["columns"]:
            if column["name"] == column_name:
                return column
        raise ValueError('No such column {}'.format(column_name))

    def mark_inputs(self, column_names):
        """Mark which columns are inputs to a model

        Args:
            column_names ([string]): Names of columns
        """
        # Make sure all the columns exist
        for c in column_names:
            self._get_column(c)
        self._output["dataset"]["inputs"] = list(column_names)
        return self

    def mark_labels(self, column_names):
        """Mark a column as label

        Args:
            column_names ([string]): Names of columns
        """
        for c in column_names:
            self._get_column(c)
        self._output["dataset"]["labels"] = list(column_names)
        return self
