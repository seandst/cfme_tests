"""
Top-level conftest.py does a couple of things:

1) Add cfme_pages repo to the sys.path automatically
2) Load a number of plugins and fixtures automatically
"""
from pkgutil import iter_modules

import pytest
import requests

import cfme.fixtures
import fixtures
import markers
import metaplugins
from fixtures.artifactor_plugin import art_client, appliance_ip_address
from cfme.fixtures.rdb import Rdb
from fixtures.pytest_store import store
from utils.log import logger
from utils.path import data_path
from utils.net import net_check
from utils.ssh import SSHClient
from utils.version import current_version
from utils.wait import TimedOutError


class _AppliancePoliceException(Exception):
    def __init__(self, message, port, *args, **kwargs):
        super(_AppliancePoliceException, self).__init__(message, port, *args, **kwargs)
        self.message = message
        self.port = port


@pytest.mark.hookwrapper
def pytest_addoption(parser):
    # Create the cfme option group for use in other plugins
    parser.getgroup('cfme', 'cfme: options related to cfme/miq appliances')
    yield


@pytest.fixture(scope="session", autouse=True)
def set_session_timeout():
    store.current_appliance.set_session_timeout(86400)


@pytest.fixture(scope="session", autouse=True)
def set_default_domain():
    if current_version() < "5.3":
        return  # Domains are not in 5.2.x and lower
    ssh_client = SSHClient()
    # The command ignores the case when the Default domain is not present (: true)
    result = ssh_client.run_rails_command(
        "\"d = MiqAeDomain.where :name => 'Default'; puts (d) ? d.first.enabled : true\"")
    if result.output.lower().strip() != "true":
        # Re-enable the domain
        ssh_client.run_rails_command(
            "\"d = MiqAeDomain.where :name => 'Default'; d = d.first; d.enabled = true; d.save!\"")


@pytest.fixture(scope="session", autouse=True)
def fix_merkyl_workaround():
    """Workaround around merkyl not opening an iptables port for communication"""
    ssh_client = SSHClient()
    if ssh_client.run_command('test -s /etc/init.d/merkyl').rc != 0:
        logger.info('Rudely overwriting merkyl init.d on appliance;')
        local_file = data_path.join("bundles").join("merkyl").join("merkyl")
        remote_file = "/etc/init.d/merkyl"
        ssh_client.put_file(local_file.strpath, remote_file)
        ssh_client.run_command("service merkyl restart")
        art_client.fire_hook('setup_merkyl', ip=appliance_ip_address)


@pytest.fixture(autouse=True, scope="function")
def appliance_police():
    if not store.slave_manager:
        return
    try:
        ports = {'ssh': 22, 'https': 443, 'postgres': 5432}
        port_results = {pn: net_check(pp, force=True) for pn, pp in ports.items()}
        for port, result in port_results.items():
            if not result:
                raise _AppliancePoliceException('Port {} was not contactable'.format(port), port)
        status_code = requests.get(store.current_appliance.url, verify=False,
                                   timeout=60).status_code
        if status_code != 200:
            raise _AppliancePoliceException('Status code was {}, should be 200'.format(
                status_code), port)
        return
    except _AppliancePoliceException as e:
        # special handling for known failure conditions
        if e.port == 443:
            # if the web ui worker merely crashed, give it 15 minutes
            # to come back up
            try:
                store.current_appliance.wait_for_web_ui(900)
                return
            except TimedOutError:
                # the UI didn't come back up after 15 minutes, and is
                # probably frozen; kill it and restart
                # fortunately we already check SSH is working...
                store.current_appliance.restart_evm_service(900, rude=True)

                # take another shot at letting the web UI come up
                try:
                    store.current_appliance.wait_for_web_ui(900)
                    return
                except TimedOutError:
                    # so much for that
                    pass
        e_message = e.message
    except Exception as e:
        e_message = e.args[0]

    # Regardles of the exception raised, we didn't return anywhere above
    # time to call a human
    msg = 'Help! My appliance {} crashed with: {}'.format(store.current_appliance.url, e_message)
    store.slave_manager.message(msg)
    Rdb(msg).set_trace(**{
        'subject': 'RDB Breakpoint: Appliance failure',
        'recipients': ['semyers@redhat.com', 'psavage@redhat.com'],
    })
    store.slave_manager.message('Resuming testing following remote debugging')


def _pytest_plugins_generator(*extension_pkgs):
    # Finds all submodules in pytest extension packages and loads them
    for extension_pkg in extension_pkgs:
        path = extension_pkg.__path__
        prefix = '%s.' % extension_pkg.__name__
        for importer, modname, is_package in iter_modules(path, prefix):
            yield modname

pytest_plugins = tuple(_pytest_plugins_generator(fixtures, markers, cfme.fixtures, metaplugins))
collect_ignore = ["tests/scenarios"]
