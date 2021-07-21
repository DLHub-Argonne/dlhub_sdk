import os

from pytest import fixture, raises, mark

from dlhub_sdk.models.servables.python import PythonStaticMethodModel
from dlhub_sdk.utils.futures import DLHubFuture
from dlhub_sdk.client import DLHubClient


# Check if we are on travis
#  See: https://blog.travis-ci.com/august-2012-upcoming-ci-environment-updates
is_travis = 'HAS_JOSH_K_SEAL_OF_APPROVAL' in os.environ

# Check if it is a tagged build
is_tag = len(os.environ.get('TRAVIS_TAG', '')) > 1
is_first_build = os.environ.get('TRAVIS_BUILD_NUMBER', '').endswith('.1')


@fixture()
def dl():
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
    user = "zhuozhao_uchicago"
    name = "noop"
    data = {"data": ["V", "Co", "Zr"]}

    # Test a synchronous request
    res = dl.run("{}/{}".format(user, name), data, timeout=60)
    assert res == 'Hello'

    # Test an asynchronous request
    task_id = dl.run("{}/{}".format(user, name), data, asynchronous=True)
    assert isinstance(task_id, DLHubFuture)
    assert task_id.result(timeout=60) == 'Hello'


@mark.skipif(not (is_tag and is_travis and is_first_build),
             reason='Publish test only runs on first version of tagged builds on Travis')
def test_submit(dl):
    # Make an example function
    model = PythonStaticMethodModel.create_model('numpy.linalg', 'norm')
    model.dlhub.test = True
    model.set_name('1d_norm')
    model.set_title('Norm of a 1D Array')
    model.set_inputs('ndarray', 'Array to be normed', shape=[None])
    model.set_outputs('number', 'Norm of the array')

    # Submit the model
    dl.publish_servable(model)


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
    res = dl.query.match_term('servable.type', '"Keras Model"')\
        .match_domains('chemistry').search()
    assert isinstance(res, list)


@mark.skipif(not is_travis, reason='Namespace test is only valid with credentials used on Travis')
def test_namespace(dl):
    assert dl.get_username() == 'dlhub.test_gmail'


def test_status(dl):
    future = dl.run('zhuozhao_uchicago/noop', 'test', asynchronous=True)
    # Need spec for Fx status returns
    assert isinstance(dl.get_task_status(future.task_id), dict)
