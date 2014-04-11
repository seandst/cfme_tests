"""Soft assert context manager and assert function

A "soft assert" is an assertion that, if it fails, does not fail the entire test.
Soft assertions can be mixed with normal assertions as needed, and will be automatically
collected/reported after a test runs.

Functionality Overview
----------------------

1. If :py:func:`soft_assert` is used by a test, that test's call phase is wrapped in
   a context manager. Entering that context sets up a thread-local store for failed assertions.
2. Inside the test, :py:func:`soft_assert` is a function with access to the thread-local store
   of failed assertions, allowing it to store failed assertions during a test run.
3. After a test runs, the context manager wrapping the test's call phase exits, which inspects the
   thread-local store of failed assertions, raising a
   :py:class:`custom AssertionError <SoftAssertionError>` if any are found.

No effort is made to clear the thread-local store; rather it's explicitly overwritten with an empty
list by the context manager. Because the store is a :py:func:`list <python:list>`, failed assertions
will be reported in the order that they failed.

"""
import inspect
from contextlib import contextmanager
from threading import local

import pytest

from utils.path import get_rel_path

# Use a thread-local store for failed soft asserts, making it thread-safe
# in parallel testing and shared among the functions in this module.
_thread_locals = local()


def pytest_runtest_call(__multicall__, item):
    """pytest hook to handle :py:func:`soft_assert` fixture usage"""
    # If a test is using soft_assert, wrap it in the context manager
    # This ensures SoftAssertionError will be raised in the call phase.
    if 'soft_assert' in item.fixturenames:
        with _soft_assert_cm():
            __multicall__.execute()
    else:
        __multicall__.execute()


class SoftAssertionError(AssertionError):
    """exception class containing failed assertions

    Functions like :py:class:`AssertionError <python:exceptions.AssertionError>`, but
    also stores the failed soft exceptions that it represents in order to properly
    display them when cast as :py:func:`str <python:str>`

    Args:
        failed_assertions: List of collected assertion failure messages
        where: Where the SoftAssert context was entered, can be omitted

    Attributes:
        failed_assertions: ``failed_assertions`` handed to the initializer,
            useful in cases where inspecting the failed soft assertions is desired.

    """
    def __init__(self, failed_assertions):
        self.failed_assertions = failed_assertions
        super(SoftAssertionError, self).__init__(str(self))

    def __str__(self):
        failmsgs = ['']

        for failed_assert in self.failed_assertions:
            failmsgs.append(failed_assert)
        return '\n'.join(failmsgs)


@pytest.fixture
def soft_assert():
    """soft assert fixture, used to defer AssertionError to the end of a test run

    Usage:

        # contents of test_soft_assert.py, for example
        def test_uses_soft_assert(soft_assert):
            soft_assert(True)
            soft_assert(False, 'failure message')
            soft_assert(None)

    This test will report two soft assertion failures, with the following message::

        SoftAssertionError:
        failure message (test_soft_assert.py:3)
        soft_assert(None) (test_soft_assert.py:4)

    """
    def _soft_assert_func(expr, fail_message=''):
        if not expr:
            # inspect the calling frame to find where the original assertion failed
            # explicitly requesting one line of code context so we can set fail_message if needed
            frameinfo = inspect.getframeinfo(inspect.stack(1)[1][0])
            if not fail_message:
                fail_message = str(frameinfo.code_context[0]).strip()

            path = '%s:%r' % (get_rel_path(frameinfo.filename), frameinfo.lineno)
            fail_message = '%s (%s)' % (fail_message, path)
            _thread_locals.caught_asserts.append(fail_message)
    return _soft_assert_func


@contextmanager
def _soft_assert_cm():
    """soft assert context manager

    * clears the thread-local caught asserts before a test run
    * inspects the thread-local caught asserts after a test run, raising an error if needed

    """
    _thread_locals.caught_asserts = []
    yield _thread_locals.caught_asserts
    if _thread_locals.caught_asserts:
        raise SoftAssertionError(_thread_locals.caught_asserts)
