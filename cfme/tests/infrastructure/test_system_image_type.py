import pytest

from cfme.infrastructure import pxe
import utils.error as error
from utils.randomness import generate_random_string
from utils.update import update

pytestmark = [pytest.mark.usefixtures("logged_in")]


def test_system_image_type_crud():
    """
    Tests a System Image Type using CRUD operations.
    """
    sys_image_type = pxe.SystemImageType(
        name=generate_random_string(size=8),
        provision_type='Vm')
    sys_image_type.create()
    with update(sys_image_type):
        sys_image_type.name = sys_image_type.name + "_update"
    sys_image_type.delete(cancel=False)


def test_duplicate_name_error_validation():
    """
    Tests a System Image for duplicate name.
    """
    sys_image_type = pxe.SystemImageType(
        name=generate_random_string(size=8),
        provision_type='Vm')
    sys_image_type.create()
    with error.expected('Name has already been taken'):
        sys_image_type.create()
    sys_image_type.delete(cancel=False)


def test_name_required_error_validation():
    """
    Tests a System Image with no name.
    """
    sys_image_type = pxe.SystemImageType(
        name=None,
        provision_type='Vm')
    with error.expected('Name is required'):
        sys_image_type.create()

# Commenting the maximum charater validation due to
# http://cfme-tests.readthedocs.org/guides/gotchas.html#
#    selenium-is-not-clicking-on-the-element-it-says-it-is
#def test_name_max_character_validation():
#    """
#    Tests a System Image name with max characters.
#    """
#    sys_image_type = pxe.SystemImageType(
#        name=generate_random_string(size=256),
#        provision_type='Vm')
#    sys_image_type.create()
#    sys_image_type.delete(cancel=False)
