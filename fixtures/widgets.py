# -*- coding: utf-8 -*-
import pytest

from cfme.dashboard import Widget
from cfme.intelligence.reports import widgets


@pytest.fixture(scope="session")
def widgets_generated(any_provider_session):
    pytest.sel.force_navigate("dashboard")
    widget_list = []
    for widget in Widget.all():
        widget_list.append((widget.name, widget.content_type))
    for w_name, w_type in widget_list:
        w = widgets.Widget.detect(w_type, w_name)
        w.generate()
