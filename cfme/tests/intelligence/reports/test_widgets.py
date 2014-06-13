# -*- coding: utf-8 -*-
""""""
import pytest

from cfme.fixtures import pytest_selenium as sel
from cfme.dashboard import Widget
from cfme.intelligence.reports.widgets import MenuWidget, ReportWidget, RSSFeedWidget, ChartWidget
from cfme.intelligence.reports.dashboards import DefaultDashboard
from cfme.web_ui import toolbar
from utils.randomness import generate_random_string
from utils.update import update


@pytest.fixture(scope="module")
def default_widgets():
    sel.force_navigate("reports_default_dashboard_edit")
    return DefaultDashboard.form.widgets.selected_items


@pytest.fixture(scope="module")
def dashboard(default_widgets):
    return DefaultDashboard(widgets=default_widgets)


@pytest.fixture(scope="function")
def custom_widgets(request):
    ws = [
        MenuWidget(
            generate_random_string(),
            description=generate_random_string(),
            active=True,
            shortcuts={
                "Services / Catalogs": generate_random_string(),
                "Clouds / Providers": generate_random_string(),
            },
            visibility="<To All Users>"),
        ReportWidget(
            generate_random_string(),
            description=generate_random_string(),
            active=True,
            filter=["Events", "Operations", "Operations VMs Powered On/Off for Last Week"],
            columns=["VM Name", "Message"],
            rows="10",
            timer={"run": "Hourly", "hours": "Hour"},
            visibility="<To All Users>"),
        ChartWidget(
            generate_random_string(),
            description=generate_random_string(),
            active=True,
            filter="Configuration Management/Virtual Machines/Vendor and Guest OS",
            timer={"run": "Hourly", "hours": "Hour"},
            visibility="<To All Users>"),
        RSSFeedWidget(
            generate_random_string(),
            description=generate_random_string(),
            active=True,
            type="Internal",
            feed="Administrative Events",
            rows="8",
            visibility="<To All Users>"),
    ]
    map(lambda w: w.create(), ws)  # create all widgets
    request.addfinalizer(lambda: map(lambda w: w.delete(), ws))  # Delete them after test
    return ws


def test_widgets_on_dashboard(request, dashboard, default_widgets, custom_widgets, soft_assert):
    with update(dashboard):
        dashboard.widgets = map(lambda w: w.title, custom_widgets)

    def _finalize():
        with update(dashboard):
            dashboard.widgets = default_widgets
    request.addfinalizer(_finalize)
    sel.force_navigate("dashboard")
    toolbar.select("Reset Dashboard Widgets to the defaults", invokes_alert=True)
    sel.handle_alert(False)
    soft_assert(len(Widget.all()) == len(custom_widgets), "Count of the widgets differ")
    for custom_w in custom_widgets:
        try:
            Widget.by_name(custom_w.title)
        except NameError:
            soft_assert(False, "Widget {} not found on dashboard".format(custom_w.title))
