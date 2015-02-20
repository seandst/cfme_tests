import pytest
from utils.randomness import generate_random_string
from utils.update import update
import utils.error as error
import cfme.tests.automate as ta

pytestmark = [pytest.mark.usefixtures("logged_in")]


@pytest.fixture(scope='module')
def make_class(request):
    return ta.make_class(request=request)


@pytest.fixture(scope="function")
def an_instance(request, make_class):
    return ta.an_instance(make_class, request=request)


def test_instance_crud(an_instance):
    an_instance.create()
    origname = an_instance.name
    with update(an_instance):
        an_instance.name = generate_random_string(8)
        an_instance.description = "updated"
    with update(an_instance):
        an_instance.name = origname
    an_instance.delete()
    assert not an_instance.exists()


def test_duplicate_disallowed(an_instance):
    an_instance.create()
    with error.expected("Name has already been taken"):
        an_instance.create()


@pytest.mark.meta(blockers=[1148541])
def test_display_name_unset_from_ui(request, an_instance):
    an_instance.create()
    request.addfinalizer(an_instance.delete)
    with update(an_instance):
        an_instance.display_name = generate_random_string()
    assert an_instance.exists
    with update(an_instance):
        an_instance.display_name = ""
    assert an_instance.exists
