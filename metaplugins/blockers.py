# -*- coding: utf-8 -*-
"""A generalized framowork for handling test blockers.

Currently handling Bugzilla nad GitHub issues. For extensions, see this file and
:py:mod:`utils.blockers`.

If you want to mark test with blockers, use meta mark ``blockers`` and specify a list of the
blockers. The blockers can be directly the objects of :py:class:`utils.blockers.Blocker` subclasses,
but you can use just plain strings that will get resolved into the objects when required.

Example comes:

.. code-block:: python

    @pytest.mark.meta(
        blockers=[
            BZ(123456),             # Will get resolved to BZ obviously
            GH(1234),               # Will get resolved to GH if you have default repo set
            GH("owner/repo:issue"), # Otherwise you need to use this syntax
            # Generic blocker writing - (<engine_name>#<blocker_spec>)
            # These work for any engine that is in :py:mod:`utils.blockers`
            "BZ#123456",            # Will resolve to BZ
            "GH#123",               # Will resolve to GH (needs default repo specified)
            "GH#owner/repo:123",    # Will resolve to GH
            # Shortcut writing
            123456,                 # Will resolve to BZ
        ]
    )


Íf you want to unskip, then you have to use the full object (``BZ()``) and pass it a kwarg called
``unblock``. When the function in ``unblock`` resolves to a truthy value, the test won't be skipped.
If the blocker does not block, the ``unblock`` is not called. There is also a ``custom_action`` that
will get called if the blocker blocks. if the action does nothing, then it continues with next
actions etc., until it gets to the point that it skips the test because there are blockers.
"""
import pytest

from kwargify import kwargify as _kwargify

from markers.meta import plugin
from utils import version
from utils.blockers import Blocker


def kwargify(f):
    """Convert function having only positional args to a function taking dictionary.

    If you pass False or None, a function which always returns False is returned.
    If you pass True, a function which always returns True is returned.
    """
    if f is None:
        f = False

    return _kwargify(lambda: f)


@plugin("blockers", ["blockers"])
def resolve_blockers(item, blockers):
    # Prepare the global env for the kwarg insertion
    global_env = dict(
        appliance_version=version.current_version(),
        appliance_downstream=version.appliance_is_downstream(),
        item=item,
        blockers=blockers,
    )
    # We will now extend the env with fixtures, so they can be used in the guard functions
    # We will however add only those that are not in the global_env otherwise we could overwrite
    # our own stuff.
    if hasattr(item, "callspec"):
        params = item.callspec.params
    else:
        # Some of the test items do not have this, so fall back
        # This can cause some problems if the fixtures are used in the guards in this case, but
        # that will tell use where is the problem and we can then find it out properly.
        params = {}
    for funcarg, value in params.iteritems():
        if funcarg not in global_env:
            global_env[funcarg] = value

    # Check blockers
    use_blockers = []
    if not isinstance(blockers, (list, tuple, set)):
        blockers = [blockers]
    # Bugzilla shortcut
    blockers = map(lambda b: "BZ#{}".format(b) if isinstance(b, int) else b, blockers)
    for blocker in map(Blocker.parse, blockers):
        if blocker.blocks:
            use_blockers.append(blocker)
    # Unblocking
    discard_blockers = set([])
    for blocker in use_blockers:
        unblock_func = kwargify(blocker.kwargs.get("unblock", None))
        local_env = {"blocker": blocker}
        local_env.update(global_env)
        if unblock_func(**local_env):
            discard_blockers.add(blocker)
    for blocker in discard_blockers:
        use_blockers.remove(blocker)
    # We now have those that block testing, so we have to skip
    # Let's go in the order that they were added
    # Custom actions first
    for blocker in use_blockers:
        if "custom_action" in blocker.kwargs:
            action = kwargify(blocker.kwargs["custom_action"])
            local_env = {"blocker": blocker}
            local_env.update(global_env)
            action(**local_env)
    # And then skip
    if use_blockers:
        pytest.skip("Skipping due to these blockers:\n{}".format(
            "\n".join(
                "- {}".format(str(blocker))
                for blocker
                in use_blockers
            )
        ))
