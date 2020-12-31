from dlhub_sdk.models.servables.python import PythonStaticMethodModel
import os


repotestdir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'repo2docker'))


def test_repo2docker():
    odir = os.getcwd()
    try:
        os.chdir(repotestdir)

        # Make sure the servable finds the repo2docker files
        model = PythonStaticMethodModel()
        model.parse_repo2docker_configuration()
        assert {os.path.join(repotestdir, 'Dockerfile'), os.path.join(repotestdir, 'postBuild')} == \
               set(model.dlhub.files['other'])
    finally:
        os.chdir(odir)
