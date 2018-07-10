from itertools import zip_longest
import pandas as pd
import os


class Dataset:
    """Base class for describing a dataset

    The Dataset class and any of its subclasses contain opreations 
    for describing what a dataset is and how to use it. 
    """

    def __init__(self):
        """
        Initialize a dataset record
        """

        self.authors = []
        self.title = None

    def set_authors(self, authors, affiliations=[]):
        """Add authors to a dataset

        Args:
            authors ([string]): List of authors for the dataset.
                In format: "<Family Name>, <Given Name>"
            affiliations ([[string]]): List of affiliations for each author.
        """
        self.authors = []
        for author, aff in zip_longest(authors, affiliations, fillvalue=[]):
            # Get the authors
            temp = author.split(",")
            family = temp[0].strip()
            given = temp[1].strip()

            # Add them to the list
            self.authors.append({
                "givenName": given,
                "familyName": family,
                "affiliations": aff,
            })
        return self

    def set_title(self, title):
        """Add a title to the dataset"""
        self.title = title
        return self

    def to_dict(self):
        """Render the dataset to a JSON description
        
        Returns:
            (dict) A description of the dataset in a form suitable for download"""
        return {"datacite": {"creators": self.authors, "title": self.title}}

    def list_files(self): 
        """Provide a list of files associated with this dataset. This list
        should contain all of the files necessary to recreate the dataset.

        Returns:
            ([string]) list of file paths"""
        raise NotImplementedError()


class TabularDataset(Dataset):
    """Read a dataset stored as a single file in a tabular format.
    
    Will read in the names of the columns, and allow users to associate
    column names with descriptions of the data provided.
    
    This class is compatible with any data format readable by the Pandas
    library. See the list of `read functions in Pandas<https://pandas.pydata.org/pandas-docs/stable/io.html>`_"""

    def __init__(self, path, format="csv", read_kwargs={}):
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
        self.data = self.load_dataset(path, format, **read_kwargs)

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
        self.columns = dict((c,{'name': c}) for c in data.columns)

        # Zero out the input and output columns
        self.inputs = []
        self.labels = []

    def annotate_column(self, column_name, description=None, data_type=None, units=None):
        """Provide documentation about a certain column within a dataset

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
            self.columns[column_name]['data_type'] = data_type
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
        self.inputs = column_names
        return self
 
    def mark_labels(self, column_names):
        """Mark a column as label

        Args:
            column_names ([string]): Names of columns
        """
        for c in column_names:
            self._check_column_name(c)
        self.labels = column_names
        return self

    def list_files(self):
        return [self.path]

    def to_dict(self):
        output = super(TabularDataset, self).to_dict()

        dataset_block = {'path': os.path.abspath(self.path)}
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
