import os

import pandas as pd

from dlhub_toolbox.models import BaseMetadataModel
from dlhub_toolbox.utils.types import simplify_numpy_dtype


class Dataset(BaseMetadataModel):
    """Base class for describing a dataset

    The Dataset class and any of its subclasses contain opreations 
    for describing what a dataset is and how to use it. 
    """

    def to_dict(self):
        # Get the metadata from the superclass
        output = super(Dataset, self).to_dict()

        # Add the datacite type as Dataset
        output['datacite']['resourceType'] = 'Dataset'

        return output


class TabularDataset(Dataset):
    """Read a dataset stored as a single file in a tabular format.
    
    Will read in the names of the columns, and allow users to associate
    column names with descriptions of the data provided.
    
    This class is compatible with any data format readable by the Pandas
    library. See the list of `read functions in Pandas<https://pandas.pydata.org/pandas-docs/stable/io.html>`_"""

    def __init__(self, path, format="csv", read_kwargs=dict()):
        """Initialize the description of a tabular dataset

        Args:
            path (string): Path to dataset
            format (string): Format of the dataset. We support all of the 
                read operations of Pandas (e.g., read_csv). Provide the format
                of your dataset as the suffix for the Pandas read command (e.g.,
                "csv" for "read_csv").
            read_kwargs (dict): Any keyword arguments for the pandas read command
        """
        super(TabularDataset, self).__init__()
        self.path = None
        self.format = None
        self.read_kwargs = {}
        self.columns = {}
        self.inputs = []
        self.labels = []
        self.load_dataset(path, format, **read_kwargs)

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
        self.path = path
        self.format = format
        self.read_kwargs = kwargs

        # Read in the data
        read_fun = getattr(pd, 'read_{}'.format(format))
        data = read_fun(path, **kwargs)
        self.columns = dict((c, {'name': c, 'type': simplify_numpy_dtype(d)})
                            for c, d in zip(data.columns, data.dtypes))

        # Zero out the input and output columns
        self.inputs = []
        self.labels = []

    def annotate_column(self, column_name, description=None, data_type=None, units=None):
        """Provide documentation about a certain column within a dataset.

        Overwrites any type values inferred from reading the dataset

        Args:
            column_name (string): Name of a column
            description (string): Longer description of a column
            data_type (string): Short description of the data type
            units (string): Units for the columns data (if applicable)
        """
        self._check_column_name(column_name)
        if description is not None:
            self.columns[column_name]['description'] = description
        if data_type is not None:
            self.columns[column_name]['type'] = data_type
        if units is not None:
            self.columns[column_name]['units'] = units
        return self

    def _check_column_name(self, column_name):
        if column_name not in self.columns:
            raise ValueError('No such column {}'.format(column_name))

    def mark_inputs(self, column_names):
        """Mark which columns are inputs to a model

        Args:
            column_names ([string]): Names of columns
        """
        for c in column_names:
            self._check_column_name(c)
        self.inputs = list(column_names)
        return self
 
    def mark_labels(self, column_names):
        """Mark a column as label

        Args:
            column_names ([string]): Names of columns
        """
        for c in column_names:
            self._check_column_name(c)
        self.labels = list(column_names)
        return self

    def list_files(self):
        return [self.path]

    def to_dict(self):
        output = super(TabularDataset, self).to_dict()

        dataset_block = {'location': os.path.abspath(self.path)}
        # Add the format description
        dataset_block['format'] = self.format
        dataset_block['read_options'] = self.read_kwargs

        # Add the column descriptions
        dataset_block['columns'] = list(self.columns.values())
        dataset_block['inputs'] = self.inputs
        dataset_block['labels'] = self.labels

        # Add to the full dataset
        output['dataset'] = dataset_block

        return output
