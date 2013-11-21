'''
Created on May 31, 2013

@author: bcrochet
'''
from pages.base import Base
from pages.infrastructure_subpages.provider_subpages.add import ProvidersAdd
from pages.infrastructure_subpages.provider_subpages.detail \
    import ProvidersDetail
from pages.infrastructure_subpages.provider_subpages.discovery \
    import ProvidersDiscovery
from pages.infrastructure_subpages.provider_subpages.edit import ProvidersEdit
from pages.regions.paginator import PaginatorMixin
from pages.regions.policy_menu import PolicyMenu
from pages.regions.quadiconitem import QuadiconItem
from pages.regions.quadicons import Quadicons
from pages.regions.taskbar.taskbar import TaskbarMixin
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from utils.providers import infra_provider_type_map
from utils.wait import wait_for
import re


# pylint: disable=C0103
# pylint: disable=R0904

class Providers(Base, PaginatorMixin, PolicyMenu, TaskbarMixin):
    '''Main Infrastructure Providers page'''
    _page_title = 'CloudForms Management Engine: Infrastructure Providers'
    _configuration_button_locator = (By.CSS_SELECTOR,
            "div.dhx_toolbar_btn[title='Configuration']")
    _discover_providers_locator = (By.CSS_SELECTOR,
            "tr[title='Discover Infrastructure Providers']\
                    >td.td_btn_txt>div.btn_sel_text")
    _edit_providers_locator = (By.CSS_SELECTOR,
            "tr[title='Select a single Infrastructure Provider to edit']\
                    >td.td_btn_txt>div.btn_sel_text")
    _remove_providers_locator = (By.CSS_SELECTOR,
            "tr[title='Remove selected Infrastructure Providers from the VMDB']\
                    >td.td_btn_txt>div.btn_sel_text")
    _add_new_provider_locator = (By.CSS_SELECTOR,
            "tr[title='Add a New Infrastructure Provider']\
                    >td.td_btn_txt>div.btn_sel_text")

    def _get_provider_stats(self, provider):

        provider_type = provider['credentials']
        credentials = self.testsetup.credentials[provider_type]

        provider_kwargs = provider.copy()
        provider_kwargs.update(credentials)

        client = infra_provider_type_map[provider['type']](**provider_kwargs)

        stats = {'num_host': len(client.list_host()),
                 'num_datastore': len(client.list_datastore()),
                 'num_cluster': len(client.list_cluster()),
                 'num_vm': len(client.list_vm())}
        return stats

    @property
    def quadicon_region(self):
        '''The quadicon region'''
        return Quadicons(self.testsetup, self.ProvidersQuadIconItem)

    @property
    def discover_button(self):
        '''The discover button'''
        return self.selenium.find_element(*self._discover_providers_locator)

    @property
    def edit_button(self):
        '''The edit button'''
        return self.selenium.find_element(*self._edit_providers_locator)

    @property
    def remove_button(self):
        '''The remove button'''
        return self.selenium.find_element(*self._remove_providers_locator)

    @property
    def add_button(self):
        '''The add button'''
        return self.selenium.find_element(*self._add_new_provider_locator)

    def select_provider(self, provider_name):
        '''Select a provider given a name'''
        # Needs to be on the quadicon view first
        self.taskbar_region.view_buttons.change_to_grid_view()
        self.quadicon_region.get_quadicon_by_title(provider_name).mark_checkbox()

    def load_provider_details(self, provider_name):
        '''Get provider details page given a name'''
        # Needs to be on the quadicon view first
        self.taskbar_region.view_buttons.change_to_grid_view()
        self.quadicon_region.get_quadicon_by_title(provider_name).click()
        self._wait_for_results_refresh()
        return ProvidersDetail(self.testsetup)

    def is_quad_icon_available(self, provider_name):
        try:
            self.select_provider(provider_name)
        except:
            self.selenium.refresh()
            return False
        return True

    # In one way makes sense to refresh the page just before the check
    # because that gives it the maximum amount of time for background
    # tasks to complete. On the other hand doing so, without passing
    # extra parameters means that an extra refresh is had right at the
    # start of the testing, which to me is undesirable
    def do_stats_match(self, detail_pg, host_stats, vms=False):
        core_stats = False
        if int(detail_pg.host_count) == host_stats['num_host'] and \
           int(detail_pg.datastore_count) == host_stats['num_datastore'] and \
           int(detail_pg.cluster_count) == host_stats['num_cluster']:
            core_stats = True

        if core_stats and not vms:
            return True
        elif vms:
            if core_stats and int(detail_pg.cluster_count) == host_stats['num_cluster']:
                return True

        self.selenium.refresh()
        return False

    def wait_for_provider_or_timeout(self, provider):
        '''Wait for a provider to become available or timeout trying'''
        host_stats = self._get_provider_stats(provider)

        ec, tc = wait_for(self.is_quad_icon_available,
                          [provider['name']])
        detail_pg = self.quadicon_region.selected[0].click()
        ec, tc = wait_for(self.do_stats_match,
                          [detail_pg, host_stats],
                          message="does_host_and_ds_count_match")
        return

    def click_on_discover_providers(self):
        '''Click on discover provider button'''
        ActionChains(self.selenium).click(
            self.configuration_button).click(
            self.discover_button).perform()
        return ProvidersDiscovery(self.testsetup)

    def click_on_edit_providers(self):
        '''Click on edit providers button'''
        ActionChains(self.selenium).click(
            self.configuration_button).click(
            self.edit_button).perform()
        return ProvidersEdit(self.testsetup)

    def click_on_remove_provider(self):
        '''Click on remove provider button'''
        ActionChains(self.selenium).click(
            self.configuration_button).click(
            self.remove_button).perform()
        self.handle_popup()
        return Providers(self.testsetup)

    def click_on_remove_provider_and_cancel(self):
        '''Click on remove provider and cancel via popup'''
        ActionChains(self.selenium).click(
            self.configuration_button).click(
            self.remove_button).perform()
        self.handle_popup(True)
        return Providers(self.testsetup)

    def click_on_add_new_provider(self):
        '''Click on add new provider button'''
        ActionChains(self.selenium).click(
            self.configuration_button).click(
            self.add_button).perform()
        return ProvidersAdd(self.testsetup)

    class ProvidersQuadIconItem(QuadiconItem):
        '''Represents a provider quadicon'''
        @property
        def hypervisor_count(self):
            '''How many hypervisors does this provider have?'''
            return self.get_element(*self._quad_tl_locator).text

        # @property
        # def current_state(self):
        #    image_src = self._root_element.find_element(
        #            *self._quad_tr_locator).find_element_by_tag_name(
        #                    "img").get_attribute("src")
        #    return re.search('.+/currentstate-(.+)\.png',image_src).group(1)

        @property
        def vendor(self):
            '''Which provider vendor?'''
            image_src = self.get_element(*self._quad_bl_locator). \
                find_element_by_tag_name("img").get_attribute("src")
            return re.search(r'.+/vendor-(.+)\.png', image_src).group(1)

        @property
        def valid_credentials(self):
            '''Does the provider have valid credentials?'''
            image_src = self.get_element(*self._quad_br_locator). \
                find_element_by_tag_name("img").get_attribute("src")
            return 'checkmark' in image_src

        def click(self):
            '''Click on the provider quadicon'''
            self._root_element.click()
            self._wait_for_results_refresh()
            return ProvidersDetail(self.testsetup)
