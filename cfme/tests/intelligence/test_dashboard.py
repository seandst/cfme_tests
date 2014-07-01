# -*- coding: utf-8 -*-
import pytest

from cfme import dashboard
from cfme.fixtures import pytest_selenium as sel
from cfme.dashboard import Widget
from cfme.intelligence.reports.dashboards import Dashboard
from utils.randomness import generate_random_string, pick


AVAILABLE_WIDGETS = [
    "Top Memory Consumers (weekly)",
    "Vendor and Guest OS Chart",
    "EVM: Recently Discovered Hosts",
    "Top Storage Consumers",
    "Guest OS Information"
]


def test_widgets_operation(request):
    sel.force_navigate("dashboard")
    request.addfinalizer(lambda: Widget.close_zoom())
    for widget in Widget.all():
        widget.minimize()
        assert widget.is_minimized
        widget.restore()
        assert not widget.is_minimized
        if widget.can_zoom:
            widget.zoom()
            assert Widget.is_zoomed()
            assert widget.name == Widget.get_zoomed_name()
            Widget.close_zoom()
            assert not Widget.is_zoomed()
        widget.footer
        widget.content


# @pytest.mark.bugzilla(1110171)
@pytest.mark.parametrize("number_dashboards", range(1, 4))
def test_custom_dashboards(request, soft_assert, number_dashboards):
    """Create some custom dashboards and check their presence. Then check their contents."""
    # Very useful construct. List is mutable, so we can prepare the generic delete finalizer.
    # Then we add everything that succeeded with creation. Simple as that :)
    dashboards = []
    request.addfinalizer(lambda: map(lambda item: item.delete(), dashboards))

    def _create_dashboard(widgets):
        return Dashboard(
            generate_random_string(),
            "EvmGroup-super_administrator",
            generate_random_string(),
            locked=False,
            widgets=widgets
        )

    for i in range(number_dashboards):
        d = _create_dashboard(pick(AVAILABLE_WIDGETS, 3))
        d.create()
        dashboards.append(d)
    dash_dict = {d.title: d for d in dashboards}
    try:
        for dash_name in dashboard.dashboards():
            soft_assert(dash_name in dash_dict, "Dashboard {} not found!".format(dash_name))
            if dash_name in dash_dict:
                for widget in Widget.all():
                    soft_assert(widget.name in dash_dict[dash_name].widgets,
                                "Widget {} not found in {}!".format(widget.name, dash_name))
                del dash_dict[dash_name]
        soft_assert(not dash_dict, "Some of the dashboards were not found! ({})".format(
            ", ".join(dash_dict.keys())))
    except IndexError:
        pytest.fail("No dashboard selection tabs present on dashboard!")
