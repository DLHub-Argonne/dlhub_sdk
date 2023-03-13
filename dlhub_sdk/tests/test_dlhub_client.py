import os
import pickle as pkl
from typing import Dict

import mdf_toolbox
from pytest import fixture, raises, mark
from pytest_mock import mocker  # noqa: F401 (flake8 cannot detect usage)

from dlhub_sdk.models.servables.python import PythonClassMethodModel, PythonStaticMethodModel
from dlhub_sdk.utils.futures import DLHubFuture
from dlhub_sdk.client import DLHubClient
from dlhub_sdk.utils.schemas import validate_against_dlhub_schema

# github specific declarations
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
fx_scope = "https://auth.globus.org/scopes/facd7ccc-c5f4-42aa-916b-a0e270e2c2a9/all"
is_gha = os.getenv('GITHUB_ACTIONS')
_pickle_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "pickle.pkl"))


# make dummy reply for mocker patch to return
class DummyReply:
    def __init__(self) -> None:
        self.status_code = 200
        self.text = "Exception that we shouldn't hit"

    def json(self) -> Dict[str, str]:
        return {"task_id": "bf06d72e-0478-11ed-97f9-4b1381555b22"}  # valid task id, status is known to be FAILED


@fixture()
def dl():
    if is_gha:
        # Get the services via a confidential log in
        services = ["search", "dlhub", fx_scope, "openid"]
        auth_res = mdf_toolbox.confidential_login(client_id=client_id,
                                                  client_secret=client_secret,
                                                  services=services,
                                                  make_clients=False)
        return DLHubClient(
            dlh_authorizer=auth_res["dlhub"], fx_authorizer=auth_res[fx_scope],
            openid_authorizer=auth_res['openid'], search_authorizer=auth_res['search'],
            force_login=False, http_timeout=10
        )
    else:
        return DLHubClient(http_timeout=10)


def test_get_servables(dl):
    r = dl.get_servables()
    assert isinstance(r, list)
    assert 'dlhub' in r[0]

    # Make sure there are no duplicates
    assert len(r) == len(set(i['dlhub']['shorthand_name'] for i in r))

    # Get with all versions of the model
    r = dl.get_servables(False)
    assert len(r) != len(set(i['dlhub']['shorthand_name'] for i in r))

    # Get all servable names
    r = dl.list_servables()
    assert len(r) > 0
    assert 'dlhub.test_gmail/1d_norm' in r


def test_run(dl):
    user = "aristana_uchicago"
    name = "noop_v11"  # published 2/22/2022
    data = True  # accepts anything as input, but listed as Boolean in DLHub

    # Test a synchronous request
    res = dl.run("{}/{}".format(user, name), data, timeout=60)
    # res[0] contains model results, res[1] contains event data JSON
    assert res == 'Hello world!'

    # Do the same thing with input validation
    res = dl.run("{}/{}".format(user, name), data, timeout=60, validate_input=True)
    # res[0] contains model results, res[1] contains event data JSON
    assert res == 'Hello world!'

    # Do the same thing with debug mode
    res = dl.run("{}/{}".format(user, name), data, timeout=60, debug=True)
    # res[0] contains model results, res[1] contains event data JSON
    assert res[0] == 'Hello world!'
    assert isinstance(res[1], dict)

    # Test an asynchronous request
    res = dl.run("{}/{}".format(user, name), data, asynchronous=True)
    assert isinstance(res, DLHubFuture)
    assert res.result(timeout=60) == 'Hello world!'


def test_submit(dl, mocker):  # noqa: F811 (flake8 does not understand usage)

    # patch build_container, register_funcx, and search_ingest
    mocker.patch("funcx.sdk.client.FuncXClient.build_container", return_value="f53e2175-39c5-4522-bc6c-0e68625e3c20")
    mocker.patch("dlhub_sdk.utils.publish.register_funcx", return_value="6af11a75-f751-4e6d-982f-9ae513c56d63")
    mocker.patch("dlhub_sdk.utils.publish.search_ingest", return_value=None)
    # patch requests.post
    mocker.patch("requests.post", return_value=DummyReply())

    # Submit a test model
    container_id = dl.publish_repository("https://github.com/ericblau/dlhub_noop_publish")
    assert container_id == "f53e2175-39c5-4522-bc6c-0e68625e3c20"

    # pickle class method to test
    with open(_pickle_path, 'wb') as fp:
        pkl.dump(DummyReply(), fp)

    # test auto_inspect for class methods
    model = PythonClassMethodModel.create_model(_pickle_path, "json", auto_inspect=True)
    model.dlhub.test = True
    model.set_name("dummy_json")
    model.set_title("Dummy JSON")

    # Submit the model
    container_id = dl.publish_servable(model)
    assert container_id == "f53e2175-39c5-4522-bc6c-0e68625e3c20"

    # make sure invalid call raises proper error
    with raises(TypeError):
        model = PythonStaticMethodModel.create_model("dlhub_sdk.utils.validation")

    # Submit the model using easy publish
    container_id = dl.easy_publish("Validate dl.run Calls", "Darling, Isaac", "validate_run", "static_method",
                                   {"module": "dlhub_sdk.utils.validation", "method": "validate"}, [["University of Chicago"]], "not-a-real-doi")
    assert container_id == "f53e2175-39c5-4522-bc6c-0e68625e3c20"


def test_datacite_validation():
    # Make an example function
    model = PythonStaticMethodModel.create_model("numpy.linalg", "norm")
    model.set_name("1d_norm")
    model.set_title("Norm of a 1D Array")
    model.set_inputs("ndarray", "Array to be normed", shape=[None])
    model.set_outputs("number", "Norm of the array")

    # Set some datacite fields
    model.set_abstract("THIS IS AN ABSTRACT.")
    model.set_doi("10.NOT/REAL")

    # Confirm validation runs as expected
    validate_against_dlhub_schema(model.to_dict(), "servable")


def test_describe_model(dl):
    # Find the 1d_norm function from the test user (should be there)
    description = dl.describe_servable('dlhub.test_gmail/1d_norm')
    assert 'dlhub.test_gmail' == description['dlhub']['owner']
    assert '1d_norm' == description['dlhub']['name']

    # Give it a bogus name, check the error
    with raises(AttributeError) as exc:
        dl.describe_servable('dlhub.test_gmail/nonexistant')
    assert 'No such servable' in str(exc)

    # Get only the method details
    expected = dict(description['servable']['methods'])
    del expected['run']['method_details']
    methods = dl.describe_methods('dlhub.test_gmail/1d_norm')
    assert expected == methods

    method = dl.describe_methods('dlhub.test_gmail/1d_norm', 'run')
    assert expected['run'] == method

    with raises(ValueError) as exc:
        dl.describe_methods('dlhub.test_gmail/1d_norm', 'notamethod')
    assert 'No such method' in str(exc)


def test_search_by_servable(dl):
    with raises(ValueError) as exc:
        dl.search_by_servable()
    assert str(exc.value).startswith("One of")

    # Search for all models owned by "dlhub.test_gmail"
    res = dl.search_by_servable(owner="dlhub.test_gmail", only_latest=False)
    isinstance(res, list)
    assert len(res) > 1

    # TODO: This test will break if we ever delete models after unit tests
    # Get only those that are named 1d_norm
    res = dl.search_by_servable(owner="dlhub.test_gmail", servable_name="1d_norm", only_latest=False)
    assert {'1d_norm'} == set(x['dlhub']['name'] for x in res)
    # TODO: Converting to int is a hack to deal with strings in Search
    most_recent = max(int(x['dlhub']['publication_date']) for x in res)

    # Get only the latest one
    res = dl.search_by_servable(owner="dlhub.test_gmail", servable_name="1d_norm", only_latest=True)
    assert 1 == len(res)
    assert most_recent == int(res[0]['dlhub']['publication_date'])

    # Specify a version
    res = dl.search_by_servable(owner="dlhub.test_gmail", servable_name="1d_norm", version=most_recent)
    assert len(res) == 1
    assert most_recent == int(res[0]['dlhub']['publication_date'])

    # Get the latest one, and return search information
    res, info = dl.search_by_servable(owner="dlhub.test_gmail", servable_name="1d_norm",
                                      only_latest=False, get_info=True)
    assert len(res) > 0
    assert isinstance(info, dict)
    assert 'dlhub' in res[0]


def test_query_authors(dl):
    # Make sure we get at least one author
    res = dl.search_by_authors('Cherukara')
    assert len(res) > 0

    # Search with firstname and last name
    res = dl.search_by_authors('Cherukara, Mathew')
    assert len(res) > 0

    # Test with the middle initial
    res = dl.search_by_authors(['Cherukara, Mathew J'])
    assert len(res) > 0

    # Test searching with multiple authors, allow partial matches
    res = dl.search_by_authors(['Cherukara, Mathew J', 'Not, Aperson'], match_all=False)
    assert len(res) > 0

    # Test with authors from the paper, and require all
    res = dl.search_by_authors(['Cherukara, Mathew J', 'Not, Aperson'], match_all=True)
    assert len(res) == 0

    # Advanced query to do both search by author and something else
    res = dl.query.match_doi("10.1038/s41598-018-34525-1").match_authors('Not, Aperson').search()
    assert len(res) == 0

    # Make sure that passing no authors is a no-op function
    res = dl.query.match_doi("10.1038/s41598-018-34525-1").match_authors([]).search()
    assert len(res) > 0


def test_query_by_paper(dl):
    res = dl.search_by_related_doi("10.1038/s41598-018-34525-1")
    assert len(res) > 0


def test_query_domains(dl):
    # Must match at last the Cherukara model
    res = dl.query.match_domains('materials science').search()
    assert len(res) > 0
    res = dl.query.match_domains(['materials science']).search()
    assert len(res) > 0

    # Match all means this will return nothing
    res = dl.query.match_domains(['materials science', 'not a domain']).search()
    assert len(res) == 0

    # Not matching all should find something
    res = dl.query.match_domains(['materials science', 'not a domain'],
                                 match_all=False).search()
    assert len(res) > 0


def test_basic_search(dl):
    # Should at least hit the Cherukara model
    res = dl.search('"coherent"')
    assert len(res) > 0

    res = dl.search('servable.type:"Keras Model" AND dlhub.domains:"materials science"', advanced=True)
    assert len(res) > 0

    # Test another query from the documentation
    res = dl.query.match_term('servable.type', '"Keras Model"') \
        .match_domains('chemistry').search()
    assert isinstance(res, list)


@mark.skipif(not is_gha, reason='Namespace test is only valid with credentials used on GHA')
def test_namespace(dl):
    assert dl.get_username().endswith('_clients')


def test_status(dl):
    future = dl.run('aristana_uchicago/noop_v11', True, asynchronous=True)
    # Need spec for Fx status returns
    assert isinstance(dl.get_task_status(future.task_id), dict)
