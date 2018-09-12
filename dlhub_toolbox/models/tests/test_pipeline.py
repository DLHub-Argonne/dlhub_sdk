import unittest

from dlhub_toolbox.models.servables.python import PythonStaticMethodModel
from dlhub_toolbox.utils.schemas import validate_against_dlhub_schema
from dlhub_toolbox.models.pipeline import PipelineModel


class TestPipeline(unittest.TestCase):

    def test_pipeline(self):
        """Make a pipeline composed of two numpy steps"""

        # Generate the two steps
        step1 = PythonStaticMethodModel('numpy', 'max', function_kwargs={'axis': 1})
        step2 = PythonStaticMethodModel('numpy', 'mean')

        # Assign them dlhub IDs
        step1.assign_dlhub_id()
        step2.assign_dlhub_id()

        # Make the pipeline
        pipeline = PipelineModel().set_title('Average of Column Maximums').set_name('numpy_test')
        pipeline.add_step(step1.dlhub_id, 'Maximum of each column', {'axis': 0})
        pipeline.add_step(step2, 'Average of the maximums')

        # Generate the pipeline metadata
        metadata = pipeline.to_dict()
        self.assertEqual(metadata,
            {'datacite': {'creators': [], 'titles': [{'title': 'Average of Column Maximums'}],
                          'publisher': 'DLHub', 'publicationYear': '2018',
                          'identifier': {'identifier': '10.YET/UNASSIGNED',
                                         'identifierType': 'DOI'},
                          'resourceType': {'resourceTypeGeneral': 'InteractiveResource'}},
             'dlhub': {'version': '0.1', 'domain': '', 'visible_to': ['public'],
                       'id': None, 'name': 'numpy_test'},
             'pipeline': {'steps': [{'dlhub_id': step1.dlhub_id,
                           'description': 'Maximum of each column', 'parameters': {'axis': 0}},
                          {'dlhub_id': step2.dlhub_id,
                           'description': 'Average of the maximums'}]}})
        validate_against_dlhub_schema(metadata, 'pipeline')
