#!/usr/bin/env python

from unittestzero import Assert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.common.by import By


class Page(object):
    '''
    Base class for all Pages
    '''
    _updating_locator = (By.CSS_SELECTOR, "div#notification > div:first-child")

    def __init__(self, testsetup):
        '''
        Constructor
        '''
        self.testsetup = testsetup
        self.base_url = testsetup.base_url
        self.selenium = testsetup.selenium
        self.timeout = testsetup.timeout

    def _wait_for_results_refresh(self):
        # On pages that do not have ajax refresh this wait will have no effect.
        WebDriverWait(self.selenium, self.timeout).until(lambda s: not self.is_element_visible(*self._updating_locator))

    @property
    def is_the_current_page(self):
        if self._page_title:
            WebDriverWait(self.selenium, self.timeout).until(lambda s: self.selenium.title)

        Assert.equal(self.selenium.title, self._page_title,
            "Expected page title: %s. Actual page title: %s" % (self._page_title, self.selenium.title))
        return True

    def get_url_current_page(self):
        WebDriverWait(self.selenium, self.timeout).until(lambda s: self.selenium.title)
        return self.selenium.current_url

    def is_element_present(self, *locator):
        self.selenium.implicitly_wait(0)
        try:
            self.selenium.find_element(*locator)
            return True
        except NoSuchElementException:
            return False
        finally:
            # set back to where you once belonged
            self.selenium.implicitly_wait(self.testsetup.default_implicit_wait)

    def is_element_visible(self, *locator):
        try:
            return self.selenium.find_element(*locator).is_displayed()
        except NoSuchElementException, ElementNotVisibleException:
            return False

    def return_to_previous_page(self):
        self.selenium.back()

    def get_element(self, *element):
        return self.selenium.find_element(*element)

