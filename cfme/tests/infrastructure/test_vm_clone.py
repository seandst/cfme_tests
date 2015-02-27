# -*- coding: utf-8 -*-
import pytest

from cfme.services.catalogs.catalog_item import CatalogItem
from cfme.automate.service_dialogs import ServiceDialog
from cfme.services.catalogs.catalog import Catalog
from cfme.services.catalogs.service_catalogs import ServiceCatalogs
from cfme.infrastructure.virtual_machines import Vm
from cfme.services import requests
from cfme.web_ui import flash
from utils.wait import wait_for
from utils import testgen
from utils.log import logger
from utils import version
import utils.randomness as rand
from utils.randomness import generate_random_string
from utils.providers import setup_provider

pytestmark = [
    pytest.mark.fixtureconf(server_roles="+automate")
]


def pytest_generate_tests(metafunc):
    # Filter out providers without provisioning data or hosts defined
    argnames, argvalues, idlist = testgen.infra_providers(
        metafunc, 'provisioning', template_location=["provisioning", "template"])

    new_idlist = []
    new_argvalues = []
    for i, argvalue_tuple in enumerate(argvalues):
        args = dict(zip(argnames, argvalue_tuple))
        if not args['provisioning']:
            # No provisioning data available
            continue

        # required keys should be a subset of the dict keys set
        if not {'template', 'host', 'datastore'}.issubset(args['provisioning'].viewkeys()):
            # Need all three for template provisioning
            continue

        new_idlist.append(idlist[i])
        new_argvalues.append(argvalues[i])

    testgen.parametrize(metafunc, argnames, new_argvalues, ids=new_idlist, scope="module")


@pytest.fixture()
def provider_init(provider_key):
    try:
        setup_provider(provider_key)
    except Exception:
        pytest.skip("It's not possible to set up this provider, therefore skipping")


@pytest.yield_fixture(scope="function")
def dialog():
    dialog = "dialog_" + generate_random_string()
    service_dialog = ServiceDialog(label=dialog, description="my dialog",
                     submit=True, cancel=True,
                     tab_label="tab_" + rand.generate_random_string(), tab_desc="my tab desc",
                     box_label="box_" + rand.generate_random_string(), box_desc="my box desc",
                     ele_label="ele_" + rand.generate_random_string(),
                     ele_name=rand.generate_random_string(),
                     ele_desc="my ele desc", choose_type="Text Box",
                     default_text_box="default value")
    service_dialog.create()
    flash.assert_success_message('Dialog "%s" was added' % dialog)
    yield dialog


@pytest.yield_fixture(scope="function")
def catalog():
    catalog = "cat_" + generate_random_string()
    cat = Catalog(name=catalog,
                  description="my catalog")
    cat.create()
    yield catalog


def cleanup_vm(vm_name, provider_key, provider_mgmt):
    try:
        logger.info('Cleaning up VM %s on provider %s' % (vm_name, provider_key))
        provider_mgmt.delete_vm(vm_name + "_0001")
    except:
        # The mgmt_sys classes raise Exception :\
        logger.warning('Failed to clean up VM %s on provider %s' % (vm_name, provider_key))


@pytest.yield_fixture(scope="function")
def catalog_item(provider_crud, provider_type, provisioning, vm_name, dialog, catalog):
    template, host, datastore, iso_file, catalog_item_type = map(provisioning.get,
        ('template', 'host', 'datastore', 'iso_file', 'catalog_item_type'))

    provisioning_data = {
        'vm_name': vm_name,
        'host_name': {'name': [host]},
        'datastore_name': {'name': [datastore]}
    }

    if provider_type == 'rhevm':
        provisioning_data['provision_type'] = 'Native Clone'
        provisioning_data['vlan'] = provisioning['vlan']
        catalog_item_type = version.pick({
            version.LATEST: "RHEV",
            '5.3': "RHEV",
            '5.2': "Redhat"
        })
    elif provider_type == 'virtualcenter':
        provisioning_data['provision_type'] = 'VMware'
    item_name = generate_random_string()
    catalog_item = CatalogItem(item_type=catalog_item_type, name=item_name,
                  description="my catalog", display_in=True, catalog=catalog,
                  dialog=dialog, catalog_name=template,
                  provider=provider_crud.name, prov_data=provisioning_data)
    yield catalog_item


@pytest.fixture(scope="function")
def clone_vm_name():
    clone_vm_name = 'test_cloning_{}'.format(generate_random_string())
    return clone_vm_name


@pytest.fixture
def create_vm(provider_key, provider_mgmt, provider_init, catalog_item, request):
    vm_name = catalog_item.provisioning_data["vm_name"]
    catalog_item.create()
    service_catalogs = ServiceCatalogs("service_name")
    service_catalogs.order(catalog_item.catalog, catalog_item)
    flash.assert_no_errors()
    logger.info('Waiting for cfme provision request for service %s' % catalog_item.name)
    row_description = 'Provisioning [%s] for Service [%s]' % (catalog_item.name, catalog_item.name)
    cells = {'Description': row_description}
    row, __ = wait_for(requests.wait_for_request, [cells],
        fail_func=requests.reload, num_sec=900, delay=20)
    assert row.last_message.text == 'Request complete'
    return vm_name


@pytest.mark.meta(blockers=[1144207])
@pytest.mark.usefixtures("setup_provider")
@pytest.mark.long_running
def test_vm_clone(provisioning, provider_type, provider_crud, clone_vm_name,
                  provider_mgmt, request, create_vm, provider_key):
    request.addfinalizer(lambda: cleanup_vm(vm_name, provider_key, provider_mgmt))
    request.addfinalizer(lambda: cleanup_vm(clone_vm_name, provider_key, provider_mgmt))
    vm_name = create_vm + "_0001"
    vm = Vm(vm_name, provider_crud)
    vm.clone_vm("email@xyz.com", "first", "last", clone_vm_name)
    row_description = 'Clone from [%s] to [%s]' % (vm_name, clone_vm_name)
    cells = {'Description': row_description}
    row, __ = wait_for(requests.wait_for_request, [cells],
        fail_func=requests.reload, num_sec=4000, delay=20)
    assert row.last_message.text == 'Vm Provisioned Successfully'
