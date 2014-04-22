from cfme.fixtures import pytest_selenium as sel
from pages.base import Base
from pages.configuration_subpages.access_control import AccessControl
from pages.configuration_subpages.settings import Settings
from pages.configuration_subpages.diagnostics import Diagnostics
from pages.configuration_subpages.tasks_tabs import Tasks
from pages.regions.list import ListRegion, ListItem
from selenium.webdriver.common.by import By


class Configuration(Base):
    @property
    def submenus(self):
        return {"ops"        : Configuration.Configuration,
                "ui"         : Configuration.MySettings,
                "my_tasks"   : Tasks.MyVmAnalysisTasks,
                "miq_proxy"  : Configuration.SmartProxies,
                "about"      : Configuration.About
                }

    class Configuration(Base):
        _page_title = "CloudForms Management Engine: Configuration"
        _checkbox_automation_engine = (By.ID, "server_roles_automate")
        _save_button = (By.CSS_SELECTOR, \
                      "div#buttons_on > ul#form_buttons > li > \
                      img[alt='Save Changes']")

        @property
        def tabbutton_region(self):
            from pages.regions.tabbuttons import TabButtons
            return TabButtons(self.testsetup, locator_override = \
                    (By.CSS_SELECTOR, "div#ops_tabs > ul > li"))

        @property
        def accordion(self):
            from pages.regions.accordion import Accordion
            from pages.regions.treeaccordionitem import LegacyTreeAccordionItem
            return Accordion(self.testsetup, LegacyTreeAccordionItem)

        @property
        def automation_engine_checkbox(self):
            return self.get_element(*self._checkbox_automation_engine)

        @property
        def save_button(self):
            return self.get_element(*self._save_button)

        def click_on_access_control(self):
            self.accordion.accordion_by_name('Access Control').click()
            sel.handle_alert(wait=1.0, squash=True)
            self._wait_for_results_refresh()
            return AccessControl(self.testsetup)

        def click_on_settings(self):
            self.accordion.accordion_by_name('Settings').click()
            sel.handle_alert(wait=1.0, squash=True)
            self._wait_for_results_refresh()
            return Settings(self.testsetup)

        def click_on_diagnostics(self):
            self.accordion.accordion_by_name('Diagnostics').click()
            sel.handle_alert(wait=1.0, squash=True)
            self._wait_for_results_refresh()
            return Diagnostics(self.testsetup)

        def enable_automation_engine(self):
            '''Enables Automation Engine'''
            if not automation_engine_checkbox.is_selected():
                automation_engine_checkbox.click()
                self._wait_for_visible_element(*self._save_button)
                save_button.click()
            self._wait_for_results_refresh()
            return Settings(self.testsetup)

        def click_on_redhat_updates(self):
            from pages.configuration_subpages.settings_subpages.\
                    region_subpages.redhat_updates import RedhatUpdates
            self.accordion.current_content.click()
            self._wait_for_results_refresh()
            self.tabbutton_region.tabbutton_by_name("Red Hat Updates").click()
            self._wait_for_results_refresh()
            return RedhatUpdates(self.testsetup)

    class MySettings(Base):
        _page_title = "CloudForms Management Engine: Configuration"

        @property
        def tabbutton_region(self):
            from pages.regions.tabbuttons import TabButtons
            return TabButtons(self.testsetup, locator_override = None)

    class SmartProxies(Base):
        _page_title = "CloudForms Management Engine: SmartProxies"

    class About(Base):
        _page_title = "CloudForms Management Engine: About"
        _session_info = (
            By.CSS_SELECTOR,
            "dl.col2 > dd > fieldset > table.style1 > tbody")
        _docs_info = (
            By.XPATH,
            '//dd[contains(.//p[@class="legend"],"Assistance")]')

        def key_search(self, search):
            for item in self.session_info_list.items:
                if search in item.key:
                    return item.value
            return None

        @property
        def session_info_list(self):
            return ListRegion(
                self.testsetup,
                self.get_element(*self._session_info), self.AboutItem)

        @property
        def version_number(self):
            tupled_version = tuple(self.key_search('Version').split("."))
            return tupled_version

        @property
        def server_name(self):
            return self.key_search('Server Name')

        @property
        def docs_links(self):
            docs_info = self.get_element(*self._docs_info)
            page_links = docs_info.find_elements_by_tag_name('a')
            links = []
            # assume we have an icon, followed by text link
            # as not in a table and don't want to use sibling find
            # this is quickest way for now
            num_docs = len(page_links) / 2
            for index in range(num_docs):
                n_index = index * 2
                icon_url = page_links[n_index].get_attribute('href')
                icon_img = page_links[n_index].find_elements_by_tag_name('img')
                icon_alt = icon_img[0].get_attribute('alt')
                icon_title = page_links[n_index].get_attribute('title')
                text_url = page_links[n_index + 1].get_attribute('href')
                text_title = page_links[n_index + 1].text
                links.append({
                    "icon_url": icon_url,
                    "icon_title": icon_title,
                    "icon_alt": icon_alt,
                    "text_url": text_url,
                    "text_title": text_title})
            return links

        class AboutItem(ListItem):
            _columns = ["Key", "Value"]
            _rows = ["Server Name", "Version", "User Name",
                     "User Role", "Browser", "Browser Version",
                     "Browser OS"]

            @property
            def key(self):
                return self._item_data[0].text

            @property
            def value(self):
                return self._item_data[1].text
