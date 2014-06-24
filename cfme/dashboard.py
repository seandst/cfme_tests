"""Provides functions to manipulate the dashboard landing page.

:var page: A :py:class:`cfme.web_ui.Region` holding locators on the dashboard page
"""
import cfme.fixtures.pytest_selenium as sel
from cfme.web_ui import Region, Table, toolbar
from utils.timeutil import parsetime
from utils.wait import wait_for

_css_reset_button = 'div.dhx_toolbar_btn[title="Reset Dashboard Widgets to the defaults"] img'

page = Region(
    title="Dashboard",
    locators={
        'reset_widgets_button': toolbar.root_loc('Reset Dashboard Widgets'),
        'csrf_token': "//meta[@name='csrf-token']",
        'user_dropdown': '//div[@id="page_header_div"]//li[contains(@class, "dropdown")]',
    },
    identifying_loc='reset_widgets_button')


def reset_widgets(cancel=False):
    """Resets the widgets on the dashboard page.

    Args:
        cancel: Set whether to accept the popup confirmation box. Defaults to ``False``.
    """
    sel.click(page.reset_widgets_button, wait_ajax=False)
    sel.handle_alert(cancel)


class Widget(object):
    _name = "//div[@id='{}']//span[contains(@class, 'modtitle_text')]"
    _remove = "//div[@id='{}']//a[@title='Remove from Dashboard']"
    _minimize = "//div[@id='{}']//a[@title='Minimize']"
    _restore = "//div[@id='{}']//a[@title='Restore']"
    _footer = "//div[@id='{}']//div[@class='modboxfooter']"
    _zoom = "//div[@id='{}']//a[@title='Zoom in on this chart']"
    _zoomed_name = "//div[@id='lightbox_div']//span[contains(@class, 'modtitle_text')]"
    _zoomed_close = "//div[@id='lightbox_div']//a[@title='Close']"
    _all = "//div[@id='modules']//div[contains(@id, 'w_')]"
    _content = "//div[@id='{}']//div[contains(@class, 'modboxin')]"

    def __init__(self, div_id):
        self._div_id = div_id

    @property
    def name(self):
        return sel.text(self._name.format(self._div_id)).encode("utf-8")

    @property
    def content_type(self):
        return sel.get_attribute(self._content.format(self._div_id), "class").rsplit(" ", 1)[-1]

    @property
    def content(self):
        print self.content_type
        if self.content_type == "rss_widget":
            return RSSWidgetContent(self._div_id)
        elif self.content_type == "report_widget":
            return ReportWidgetContent(self._div_id)
        else:
            return BaseWidgetContent(self._div_id)

    @property
    def footer(self):
        cleaned = [
            x.strip()
            for x
            in sel.text(self._footer.format(self._div_id)).encode("utf-8").strip().split("|")
        ]
        result = {}
        for item in cleaned:
            name, time = item.split(" ", 1)
            time = time.strip()
            if time.lower() == "never":
                result[name.strip().lower()] = None
            else:
                result[name.strip().lower()] = parsetime.from_american_minutes(time.strip())
        return result

    @property
    def time_updated(self):
        return self.footer["updated"]

    @property
    def time_next(self):
        return self.footer["next"]

    @property
    def is_minimized(self):
        self.close_zoom()
        return not sel.is_displayed(self._minimize.format(self._div_id))

    @property
    def can_zoom(self):
        """Can this Widget be zoomed?"""
        return sel.is_displayed(self._zoom.format(self._div_id))

    def remove(self, cancel=False):
        """Remove this Widget."""
        self.close_zoom()
        sel.click(self._remove.format(self._div_id), wait_ajax=False)  # alert
        sel.handle_alert(cancel)

    def minimize(self):
        """Minimize this Widget."""
        self.close_zoom()
        if not self.is_minimized:
            sel.click(self._minimize.format(self._div_id))

    def restore(self):
        """Return the Widget back from minimalization."""
        self.close_zoom()
        if self.is_minimized:
            sel.click(self._restore.format(self._div_id))

    def zoom(self):
        """Zoom this Widget."""
        self.close_zoom()
        if not self.is_zoomed():
            sel.click(self._zoom.format(self._div_id))

    @classmethod
    def is_zoomed(cls):
        return sel.is_displayed(cls._zoomed_name)

    @classmethod
    def get_zoomed_name(cls):
        return sel.text(cls._zoomed_name).encode("utf-8")

    @classmethod
    def close_zoom(cls):
        if cls.is_zoomed():
            sel.click(cls._zoomed_close)
            # Here no ajax, so we have to check it manually
            wait_for(lambda: not cls.is_zoomed(), delay=0.1, num_sec=5, message="cancel zoom")

    @classmethod
    def all(cls):
        """Returns objects with all Widgets currently present."""
        result = []
        for el in sel.elements(cls._all):
            result.append(cls(sel.get_attribute(el, "id")))
        return result

    @classmethod
    def by_name(cls, name):
        """Returns Widget with specified name."""
        for widget in cls.all():
            if widget.name == name:
                return widget
        else:
            raise NameError("Could not find widget with name {} on current dashboard!".format(name))


class BaseWidgetContent(object):
    def __init__(self, widget_box_id):
        self.root = lambda: sel.element(
            "//div[@id='{}']//div[contains(@class, 'modboxin')]".format(widget_box_id))

    @property
    def data(self):
        return sel.element("./div[contains(@id, 'dd_')]", root=self.root)


class RSSWidgetContent(BaseWidgetContent):
    @property
    def data(self):
        result = []
        for row in sel.elements("./div/table/tbody/tr/td", root=self.root):
            # Regular expressions? Boring.
            desc, date = sel.text(row).encode("utf-8").strip().rsplit("\n", 1)
            date = date.split(":", 1)[-1].strip()
            date = parsetime.from_iso_with_utc(date)
            result.append((desc, date))
        return result


class ReportWidgetContent(BaseWidgetContent):
    @property
    def data(self):
        return Table(lambda: sel.element("./div/table[@class='style3']", root=self.root))


def get_csrf_token():
    """Retuns current CSRF token.

    Returns: Current  CSRF token.
    """
    return sel.get_attribute(page.csrf_token, "content")


def set_csrf_token(csrf_token):
    """Changing the CSRF Token on the fly via the DOM by iterating over the meta tags

    Args:
        csrf_token: Token to set as the CSRF token.
    """
    script = '''
        var elements = document.getElementsByTagName("meta");
        for (var i=0, element; element = elements[i]; i++) {
            var ename = element.getAttribute("name");
            if (ename != null && ename.toLowerCase() == "csrf-token") {
                element.setAttribute("content", "%s");
                break;
            }
        }
    ''' % csrf_token
    return sel.execute_script(script)
