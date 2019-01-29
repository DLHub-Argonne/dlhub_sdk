import unittest

from dlhub_sdk.models.servables.python import PythonStaticMethodModel
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema
from dlhub_sdk.models.pipeline import PipelineModel
from dlhub_sdk.version import __version__
from datetime import datetime


_year = str(datetime.now().year)


class TestPipeline(unittest.TestCase):

    def test_pipeline(self):
        """Make a pipeline composed of two numpy steps"""

        # Generate the two steps
        step1 = PythonStaticMethodModel.create_model('numpy', 'max', function_kwargs={'axis': 1})\
            .set_name('step1')
        step2 = PythonStaticMethodModel.create_model('numpy', 'mean').set_name('step2')

        # Make the pipeline
        pipeline = PipelineModel().set_title('Average of Column Maximums').set_name('numpy_test')
        pipeline.add_step('username', step1.name, 'Maximum of each column', {'axis': 0})
        pipeline.add_step('username', step2.name, 'Average of the maximums')

        # Generate the pipeline metadata
        metadata = pipeline.to_dict()
        correct_metadata = {
            'datacite': {
                'creators': [],
                'titles': [{
                    'title': 'Average of Column Maximums'
                }],
                'publisher': 'DLHub',
                'publicationYear': _year,
                'identifier': {
                    'identifier': '10.YET/UNASSIGNED',
                    'identifierType': 'DOI'
                },
                'resourceType': {
                    'resourceTypeGeneral': 'InteractiveResource'
                },
                "descriptions": [],
                "fundingReferences": [],
                "relatedIdentifiers": [],
                "alternateIdentifiers": [],
                "rightsList": []
            },
            'dlhub': {
                'version': __version__,
                'domains': [],
                'visible_to': ['public'],
                'name': 'numpy_test',
                'files': {}
            },
            'pipeline': {
                'steps': [{
                    'author': 'username',
                    'name': step1.name,
                    'description': 'Maximum of each column',
                    'parameters': {
                        'axis': 0
                    }
                }, {
                    'author': 'username',
                    'name': step2.name,
                    'description': 'Average of the maximums'
                }]
            }
        }
        self.assertEqual(metadata, correct_metadata)
        validate_against_dlhub_schema(metadata, 'pipeline')
