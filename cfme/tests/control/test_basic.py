# -*- coding: utf-8 -*-
""" Tests checking the basic functionality of the Control/Explorer section.

Whether we can create/update/delete/assign/... these objects. Nothing with deep meaning.
Can be also used as a unit-test for page model coverage.

Todo:
    * Multiple expression types entering. (extend the update tests)
"""

import pytest

import cfme.fixtures.pytest_selenium as sel

from cfme.control import explorer
from utils import randomness
from utils.update import update
from cfme.web_ui import flash
from cfme.web_ui import expression_editor

VM_EXPRESSIONS_TO_TEST = [
    (
        "fill_field(VM and Instance : Boot Time, BEFORE, Today)",
        'VM and Instance : Boot Time BEFORE "Today"'
    ),
    (
        "fill_field(VM and Instance : Boot Time, BEFORE, 03/04/2014)",
        'VM and Instance : Boot Time BEFORE "03/04/2014 00:00"'
    ),
    (
        "fill_field(VM and Instance : Custom 6, RUBY, puts 'hello')",
        'VM and Instance : Custom 6 RUBY <RUBY Expression>'
    ),
    (
        "fill_field(VM and Instance : Format, IS NOT NULL)",
        'VM and Instance : Format IS NOT NULL'
    ),
    (
        "fill_count(VM and Instance.Files, =, 150)",
        'COUNT OF VM and Instance.Files = 150'
    ),
    # ("fill_tag(VM and Instance.My Company Tags : Owner, Production Linux Team)",)
    # Needs working input/select mutability
]


@pytest.yield_fixture(scope="module")
def vm_condition_for_expressions():
    cond = explorer.VMCondition(
        randomness.generate_random_string(),
        expression="fill_field(VM and Instance : CPU Limit, =, 20)",
        scope="fill_count(VM and Instance.Files, >, 150)"
    )
    cond.create()
    yield cond
    cond.delete()


@pytest.yield_fixture
def random_vm_condition():
    cond = explorer.VMCondition(
        randomness.generate_random_string(),
        expression="fill_field(VM and Instance : CPU Limit, =, 20)",
        scope="fill_count(VM and Instance.Files, >, 150)"
    )
    cond.create()
    yield cond
    cond.delete()


@pytest.yield_fixture
def random_host_condition():
    cond = explorer.HostCondition(
        randomness.generate_random_string(),
        expression="fill_count(Host.Files, >, 150)"
    )
    cond.create()
    yield cond
    cond.delete()


@pytest.yield_fixture
def random_vm_control_policy():
    policy = explorer.VMControlPolicy(randomness.generate_random_string())
    policy.create()
    yield policy
    policy.delete()


@pytest.yield_fixture
def random_host_control_policy():
    policy = explorer.HostControlPolicy(randomness.generate_random_string())
    policy.create()
    yield policy
    policy.delete()


def test_vm_condition_crud(soft_assert):
    condition = explorer.VMCondition(
        randomness.generate_random_string(),
        expression="fill_field(VM and Instance : CPU Limit, =, 20)",
        scope="fill_count(VM and Instance.Files, >, 150)"
    )
    # CR
    condition.create()
    soft_assert(condition.exists, "The condition {} does not exist!".format(
        condition.description
    ))
    # U
    with update(condition):
        condition.notes = "Modified!"
    sel.force_navigate("vm_condition_edit", context={"condition_name": condition.description})
    soft_assert(sel.text(condition.form.notes).strip() == "Modified!", "Modification failed!")
    # D
    condition.delete()
    soft_assert(not condition.exists, "The condition {} exists!".format(
        condition.description
    ))


def test_host_condition_crud(soft_assert):
    condition = explorer.HostCondition(
        randomness.generate_random_string(),
        expression="fill_count(Host.Files, >, 150)"
    )
    # CR
    condition.create()
    soft_assert(condition.exists, "The condition {} does not exist!".format(
        condition.description
    ))
    # U
    with update(condition):
        condition.notes = "Modified!"
    sel.force_navigate("host_condition_edit", context={"condition_name": condition.description})
    soft_assert(sel.text(condition.form.notes).strip() == "Modified!", "Modification failed!")
    # D
    condition.delete()
    soft_assert(not condition.exists, "The condition {} exists!".format(
        condition.description
    ))


def test_action_crud(request, soft_assert):
    action = explorer.Action(
        randomness.generate_random_string(),
        action_type="Tag",
        action_values={"tag": ("My Company Tags", "Department", "Accounting")}
    )
    # CR
    action.create()
    soft_assert(action.exists, "The action {} does not exist!".format(
        action.description
    ))
    # U
    with update(action):
        action.description = "w00t w00t"
    sel.force_navigate("control_explorer_action_edit", context={"action_name": action.description})
    soft_assert(
        sel.get_attribute(action.form.description, "value").strip() == "w00t w00t",
        "Modification failed!"
    )
    # D
    action.delete()
    soft_assert(not action.exists, "The action {} exists!".format(
        action.description
    ))


def test_vm_control_policy_crud(request, soft_assert):
    policy = explorer.VMControlPolicy(randomness.generate_random_string())
    # CR
    policy.create()
    soft_assert(policy.exists, "The policy {} does not exist!".format(
        policy.description
    ))
    # U
    with update(policy):
        policy.notes = "Modified!"
    sel.force_navigate("vm_control_policy_edit", context={"policy_name": policy.description})
    soft_assert(sel.text(policy.form.notes).strip() == "Modified!", "Modification failed!")
    # D
    policy.delete()
    soft_assert(not policy.exists, "The policy {} exists!".format(
        policy.description
    ))


def test_vm_compliance_policy_crud(request, soft_assert):
    policy = explorer.VMCompliancePolicy(randomness.generate_random_string())
    # CR
    policy.create()
    soft_assert(policy.exists, "The policy {} does not exist!".format(
        policy.description
    ))
    # U
    with update(policy):
        policy.notes = "Modified!"
    sel.force_navigate("vm_compliance_policy_edit", context={"policy_name": policy.description})
    soft_assert(sel.text(policy.form.notes).strip() == "Modified!", "Modification failed!")
    # D
    policy.delete()
    soft_assert(not policy.exists, "The policy {} exists!".format(
        policy.description
    ))


def test_host_control_policy_crud(request, soft_assert):
    policy = explorer.HostControlPolicy(randomness.generate_random_string())
    # CR
    policy.create()
    soft_assert(policy.exists, "The policy {} does not exist!".format(
        policy.description
    ))
    # U
    with update(policy):
        policy.notes = "Modified!"
    sel.force_navigate("host_control_policy_edit", context={"policy_name": policy.description})
    soft_assert(sel.text(policy.form.notes).strip() == "Modified!", "Modification failed!")
    # D
    policy.delete()
    soft_assert(not policy.exists, "The policy {} exists!".format(
        policy.description
    ))


def test_host_compliance_policy_crud(request, soft_assert):
    policy = explorer.HostCompliancePolicy(randomness.generate_random_string())
    # CR
    policy.create()
    soft_assert(policy.exists, "The policy {} does not exist!".format(
        policy.description
    ))
    # U
    with update(policy):
        policy.notes = "Modified!"
    sel.force_navigate("host_compliance_policy_edit", context={"policy_name": policy.description})
    soft_assert(sel.text(policy.form.notes).strip() == "Modified!", "Modification failed!")
    # D
    policy.delete()
    soft_assert(not policy.exists, "The policy {} exists!".format(
        policy.description
    ))


def test_assign_events_to_vm_control_policy(random_vm_control_policy, soft_assert):
    random_vm_control_policy.assign_events("VM Retired", "VM Clone Start")
    soft_assert(random_vm_control_policy.is_event_assigned("VM Retired"))
    soft_assert(random_vm_control_policy.is_event_assigned("VM Clone Start"))


def test_assign_events_to_host_control_policy(random_host_control_policy, soft_assert):
    random_host_control_policy.assign_events("Host Auth Error", "Host Compliance Passed")
    soft_assert(random_host_control_policy.is_event_assigned("Host Auth Error"))
    soft_assert(random_host_control_policy.is_event_assigned("Host Compliance Passed"))


def test_assign_vm_condition_to_vm_policy(
        random_vm_control_policy, random_vm_condition, soft_assert):
    random_vm_control_policy.assign_conditions(random_vm_condition)
    soft_assert(random_vm_control_policy.is_condition_assigned(random_vm_condition))
    random_vm_control_policy.assign_conditions()  # unassign


def test_assign_host_condition_to_host_policy(
        random_host_control_policy, random_host_condition, soft_assert):
    random_host_control_policy.assign_conditions(random_host_condition)
    soft_assert(random_host_control_policy.is_condition_assigned(random_host_condition))
    random_host_control_policy.assign_conditions()  # unassign


def test_policy_profile_crud(random_vm_control_policy, random_host_control_policy, soft_assert):
    profile = explorer.PolicyProfile(
        randomness.generate_random_string(),
        policies=[random_vm_control_policy, random_host_control_policy]
    )
    profile.create()
    soft_assert(profile.exists, "Policy profile {} does not exist!".format(profile.description))
    with update(profile):
        profile.notes = "Modified!"
    sel.force_navigate("policy_profile", context={"policy_profile_name": profile.description})
    soft_assert(sel.text(profile.form.notes).strip() == "Modified!")
    profile.delete()
    soft_assert(not profile.exists, "The policy profile {} exists!".format(profile.description))


@pytest.mark.parametrize(("expression", "verify"), VM_EXPRESSIONS_TO_TEST)
def test_modify_vm_condition_expression(
        vm_condition_for_expressions, expression, verify, soft_assert):
    with update(vm_condition_for_expressions):
        vm_condition_for_expressions.expression = expression
    flash.assert_no_errors()
    if verify is not None:
        sel.force_navigate("vm_condition_edit",
            context={"condition_name": vm_condition_for_expressions.description})
        if not vm_condition_for_expressions.is_editing_expression:
            sel.click(vm_condition_for_expressions.buttons.edit_expression)
        soft_assert(expression_editor.get_expression_as_text() == verify)


def test_alert_crud(soft_assert):
    alert = explorer.Alert(
        randomness.generate_random_string(), timeline_event=True, driving_event="Hourly Timer"
    )
    # CR
    alert.create()
    soft_assert(alert.exists, "The alert {} does not exist!".format(
        alert.description
    ))
    # U
    with update(alert):
        alert.notification_frequency = "2 Hours"
    sel.force_navigate("control_explorer_alert_edit", context={"alert_name": alert.description})
    soft_assert(
        sel.text(
            alert.form.notification_frequency.first_selected_option
        ).strip() == "2 Hours", "Modification failed!"
    )
    # D
    alert.delete()
    soft_assert(not alert.exists, "The alert {} exists!".format(
        alert.description
    ))
