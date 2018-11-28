from dlhub_sdk.models.servables.python import PythonStaticMethodModel
from unittest import TestCase
import os


repotestdir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'repo2docker'))


class TestBase(TestCase):

    def test_repo2docker(self):
        odir = os.getcwd()
        try:
            os.chdir(repotestdir)

            # Make sure the servable finds the repo2docker files
            model = PythonStaticMethodModel()
            model.parse_repo2docker_configuration()
            self.assertEquals({os.path.join(repotestdir, 'Dockerfile'),
                               os.path.join(repotestdir, 'postBuild')},
                              set(model['dlhub']['files']['other']))

        finally:
            os.chdir(odir)
