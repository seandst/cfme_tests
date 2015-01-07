# -*- coding: utf-8 -*-

from cfme.infrastructure import host, datastore, cluster, resource_pool, virtual_machines
from cfme.web_ui import Region
from utils import testgen


details_page = Region(infoblock_type='detail')


def pytest_generate_tests(metafunc):
    # Filter out providers without provisioning data or hosts defined
    argnames, argvalues, idlist = testgen.infra_providers(metafunc)

    argnames.append('remove_test')
    new_idlist = []
    new_argvalues = []

    for i, argvalue_tuple in enumerate(argvalues):
        args = dict(zip(argnames, argvalue_tuple))
        if 'remove_test' not in args['provider_crud'].get_yaml_data():
            # No provisioning data available
            continue

        new_idlist.append(idlist[i])
        argvalues[i].append(args['provider_crud'].get_yaml_data()['remove_test'])
        new_argvalues.append(argvalues[i])

    testgen.parametrize(metafunc, argnames, new_argvalues, ids=new_idlist, scope="module")


def test_delete_cluster(setup_provider, provider_crud, remove_test):
    cluster_name = remove_test['cluster']
    test_cluster = cluster.Cluster(name=cluster_name)
    test_cluster.delete(cancel=False)
    test_cluster.wait_for_delete()
    provider_crud.refresh_provider_relationships()
    test_cluster.wait_for_appear()


def test_delete_host(setup_provider, provider_crud, remove_test):
    host_name = remove_test['host']
    test_host = host.Host(name=host_name)
    test_host.delete(cancel=False)
    host.wait_for_host_delete(test_host)
    provider_crud.refresh_provider_relationships()
    host.wait_for_host_to_appear(test_host)


def test_delete_vm(setup_provider, provider_crud, remove_test):
    vm = remove_test['vm']
    test_vm = virtual_machines.Vm(vm, provider_crud)
    test_vm.remove_from_cfme(cancel=False)
    test_vm.wait_for_delete()
    provider_crud.refresh_provider_relationships()
    test_vm.wait_to_appear()


def test_delete_template(setup_provider, provider_crud, remove_test):
    template = remove_test['template']
    test_template = virtual_machines.Template(template, provider_crud)
    test_template.remove_from_cfme(cancel=False)
    test_template.wait_for_delete()
    provider_crud.refresh_provider_relationships()
    test_template.wait_to_appear()


def test_delete_resource_pool(setup_provider, provider_crud, remove_test):
    resourcepool_name = remove_test['resource_pool']
    test_resourcepool = resource_pool.ResourcePool(name=resourcepool_name)
    test_resourcepool.delete(cancel=False)
    test_resourcepool.wait_for_delete()
    provider_crud.refresh_provider_relationships()
    test_resourcepool.wait_for_appear()


def test_delete_datastore(setup_provider, provider_crud, remove_test):
    data_store = remove_test['datastore']
    test_datastore = datastore.Datastore(name=data_store)
    host_count = test_datastore.get_hosts()
    vm_count = test_datastore.get_vms()
    if len(host_count) == 0 and len(vm_count) == 0:
        test_datastore.delete(cancel=False)
    else:
        test_datastore.delete_all_attached_hosts()
        test_datastore.wait_for_delete_all()
        test_datastore.delete_all_attached_vms()
        test_datastore.wait_for_delete_all()
        test_datastore.delete(cancel=False)
    test_datastore.wait_for_delete()
    provider_crud.refresh_provider_relationships()
    test_datastore.wait_for_appear()
