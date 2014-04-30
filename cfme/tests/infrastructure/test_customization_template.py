import pytest

from cfme.infrastructure import pxe
from utils import error
from utils.randomness import generate_random_string
from utils.update import update

pytestmark = [pytest.mark.usefixtures("logged_in")]


def test_customization_template_crud():
    """Basic CRUD test for customization templates."""
    template_crud = pxe.CustomizationTemplate(
        name=generate_random_string(size=8),
        description=generate_random_string(size=16),
        image_type='RHEL-6',
        script_type='Kickstart',
        script_data='Testing the script')

    template_crud.create()
    with update(template_crud):
        template_crud.name = template_crud.name + "_update"
    template_crud.delete(cancel=False)


def test_name_required_error_validation():
    """Test to validate name in customization templates."""
    template_name = pxe.CustomizationTemplate(
        name=None,
        description=generate_random_string(size=16),
        image_type='RHEL-6',
        script_type='Kickstart',
        script_data='Testing the script')

    with error.expected('Name is required'):
        template_name.create()


def test_type_required_error_validation():
    """Test to validate type in customization templates."""
    template_name = pxe.CustomizationTemplate(
        name=generate_random_string(size=8),
        description=generate_random_string(size=16),
        image_type='RHEL-6',
        script_type='<Choose>',
        script_data='Testing the script')

    with error.expected('Type is required'):
        template_name.create()


def test_pxe_image_type_required_error_validation():
    """Test to validate pxe image type in customization templates."""
    template_name = pxe.CustomizationTemplate(
        name=generate_random_string(size=8),
        description=generate_random_string(size=16),
        image_type='<Choose>',
        script_type='Kickstart',
        script_data='Testing the script')

    with error.expected("Pxe_image_type can't be blank"):
        template_name.create()


@pytest.mark.xfail(message='https://bugzilla.redhat.com/show_bug.cgi?id=1092951')
def test_duplicate_name_error_validation():
    """Test to validate duplication in customization templates."""
    template_name = pxe.CustomizationTemplate(
        name=generate_random_string(size=8),
        description=generate_random_string(size=16),
        image_type='RHEL-6',
        script_type='Kickstart',
        script_data='Testing the script')

    template_name.create()
    with error.expected('Name has already been taken'):
        template_name.create()
    template_name.delete(cancel=False)


@pytest.mark.xfail(message='http://cfme-tests.readthedocs.org/guides/gotchas.html#'
    'selenium-is-not-clicking-on-the-element-it-says-it-is')
def test_name_max_character_validation():
    """Test to validate name with maximum characters in customization templates."""
    template_name = pxe.CustomizationTemplate(
        name=generate_random_string(size=256),
        description=generate_random_string(size=16),
        image_type='RHEL-6',
        script_type='Kickstart',
        script_data='Testing the script')

    with error.expected('Name is required'):
        template_name.create()
    template_name.delete(cancel=False)
