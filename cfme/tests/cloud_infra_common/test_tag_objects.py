# -*- coding: utf-8 -*-
"""This module tests tagging of objects in different locations."""
import diaper
import fauxfactory
import pytest

from cfme.web_ui import Quadicon, mixins, toolbar as tb
from cfme.configure.configuration import Category, Tag
from utils import providers
from utils.version import current_version


@pytest.fixture(scope="module")
def setup_first_provider():
    providers.setup_a_provider(
        prov_class="infra", validate=True, check_existing=True, delete_failure=True)
    providers.setup_a_provider(
        prov_class="cloud", validate=True, check_existing=True, delete_failure=True)


pytestmark = [
    pytest.mark.parametrize("location", [
        # Infrastructure
        "infrastructure_providers",
        "infrastructure_clusters",
        "infrastructure_hosts",
        "infrastructure_datastores",
        "infra_vms",
        "infra_templates",

        # Cloud
        "clouds_providers",
        "clouds_instances",
        "clouds_availability_zones",
        "clouds_flavors",
        "clouds_tenants",
        # "clouds_security_groups",  # Does not have grid view selector
    ]),
    pytest.mark.usefixtures("setup_first_provider")
]


@pytest.yield_fixture(scope="module")
def category():
    cg = Category(name=fauxfactory.gen_alpha(8).lower(),
                  description=fauxfactory.gen_alphanumeric(length=32),
                  display_name=fauxfactory.gen_alphanumeric(length=32))
    cg.create()
    yield cg
    cg.delete()


@pytest.yield_fixture(scope="module")
def tag(category):
    tag = Tag(name=fauxfactory.gen_alpha(8).lower(),
              display_name=fauxfactory.gen_alphanumeric(length=32),
              category=category)
    tag.create()
    yield tag
    tag.delete()


@pytest.mark.uncollectif(
    lambda location: location in {"clouds_tenants"} and current_version() < "5.4")
def test_tag_item_through_selecting(request, location, tag):
    """Add a tag to an item with going through the details page.

    Prerequisities:
        * Have a tag category and tag created.
        * Be on the page you want to test.

    Steps:
        * Select any quadicon.
        * Select ``Policy/Edit Tags`` and assign the tag to it.
        * Click on the quadicon and verify the tag is assigned. (TODO)
        * Go back to the quadicon view and select ``Policy/Edit Tags`` and remove the tag.
        * Click on the quadicon and verify the tag is not present. (TODO)
    """
    pytest.sel.force_navigate(location)
    tb.set_vms_grid_view()
    if not Quadicon.any_present:
        pytest.skip("No Quadicon present, cannot test.")
    Quadicon.select_first_quad()

    def _delete():
        pytest.sel.force_navigate(location)
        tb.set_vms_grid_view()
        Quadicon.select_first_quad()
        mixins.remove_tag(tag)
    request.addfinalizer(lambda: diaper(_delete))
    mixins.add_tag(tag)
    _delete()


@pytest.mark.uncollectif(
    lambda location: location in {"clouds_tenants"} and current_version() < "5.4")
def test_tag_item_through_details(request, location, tag):
    """Add a tag to an item with going through the details page.

    Prerequisities:
        * Have a tag category and tag created.
        * Be on the page you want to test.

    Steps:
        * Click any quadicon.
        * On the details page, select ``Policy/Edit Tags`` and assign the tag to it.
        * Verify the tag is assigned. (TODO)
        * Select ``Policy/Edit Tags`` and remove the tag.
        * Verify the tag is not present. (TODO)
    """
    pytest.sel.force_navigate(location)
    tb.set_vms_grid_view()
    if not Quadicon.any_present:
        pytest.skip("No Quadicon present, cannot test.")
    pytest.sel.click(Quadicon.first())
    request.addfinalizer(lambda: diaper(lambda: mixins.remove_tag(tag)))
    mixins.add_tag(tag)
    mixins.remove_tag(tag)
