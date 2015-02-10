# -*- coding: utf-8 -*-
import pytest

from utils.providers import setup_provider
from cfme.infrastructure.virtual_machines import Vm
from cfme.services import requests
from cfme.web_ui import flash
from utils.wait import wait_for
from utils import testgen

pytestmark = [
    pytest.mark.meta(server_roles="+automate")
]


def pytest_generate_tests(metafunc):
    argnames, argvalues, idlist = testgen.provider_by_type(metafunc, ['virtualcenter'])
    testgen.parametrize(metafunc, argnames, argvalues, ids=idlist, scope="module")


@pytest.fixture()
def provider_init(provider_key):
    try:
        setup_provider(provider_key)
    except Exception:
        pytest.skip("It's not possible to set up this provider, therefore skipping")


@pytest.mark.meta(blockers=[1174881])
def test_vm_migrate(provider_init, provider_crud, provider_mgmt, request):
    """Tests migration of a vm

    Metadata:
        test_flag: migrate, provision
    """
    vm = Vm("vmtest", provider_crud)
    vm.migrate_vm("email@xyz.com", "first", "last", "host", "datstore")
    flash.assert_no_errors()
    row_description = 'VM Migrate'
    cells = {'Request Type': row_description}
    row, __ = wait_for(requests.wait_for_request, [cells],
        fail_func=requests.reload, num_sec=600, delay=20)
    assert row.last_message.text == 'Request complete'
