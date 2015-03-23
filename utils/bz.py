# -*- coding: utf-8 -*-
import re
from bugzilla import Bugzilla as _Bugzilla
from collections import Sequence

from utils import lazycache
from utils.conf import cfme_data, credentials
from utils.log import logger
from utils.version import (
    LATEST, LooseVersion, current_version, appliance_build_datetime, appliance_is_downstream)

NONE_FIELDS = {"---", "undefined", "unspecified"}


class Product(object):
    def __init__(self, data):
        self._data = data

    @property
    def default_release(self):
        return LooseVersion(self._data["default_release"])

    @property
    def name(self):
        return self._data["name"]

    @property
    def milestones(self):
        return map(lambda ms: ms["name"], self._data["milestones"])

    @property
    def releases(self):
        return map(lambda release: release["name"], self._data["releases"])

    @property
    def versions(self):
        versions = []
        for version in self._data["versions"]:
            if version["name"] not in NONE_FIELDS:
                versions.append(LooseVersion(version["name"]))
        return sorted(versions)

    @property
    def latest_version(self):
        return self.versions[-1]


class Bugzilla(object):
    def __init__(self, **kwargs):
        self.__product = kwargs.pop("product", None)
        self.__kwargs = kwargs
        self.__bug_cache = {}
        self.__product_cache = {}

    @property
    def bug_count(self):
        return len(self.__bug_cache.keys())

    @property
    def bugs(self):
        for bug in self.__bug_cache.itervalues():
            yield bug

    def products(self, *names):
        return map(Product, self.bugzilla._proxy.Product.get({"names": names})["products"])

    def product(self, product):
        if product not in self.__product_cache:
            self.__product_cache[product] = self.products(product)[0]
        return self.__product_cache[product]

    @property
    def default_product(self):
        if self.__product is None:
            return None
        return self.product(self.__product)

    @classmethod
    def from_config(cls):
        url = cfme_data.get("bugzilla", {}).get("url", None)
        product = cfme_data.get("bugzilla", {}).get("product", None)
        if url is None:
            raise Exception("No Bugzilla URL specified!")
        cr_root = cfme_data.get("bugzilla", {}).get("credentials", None)
        username = credentials.get(cr_root, {}).get("username", None)
        password = credentials.get(cr_root, {}).get("password", None)
        return cls(
            url=url, user=username, password=password, cookiefile=None,
            tokenfile=None, product=product)

    @lazycache
    def bugzilla(self):
        return _Bugzilla(**self.__kwargs)

    @lazycache
    def loose(self):
        return cfme_data.get("bugzilla", {}).get("loose", [])

    @lazycache
    def open_states(self):
        return cfme_data.get("bugzilla", {}).get("skip", set([]))

    @lazycache
    def upstream_version(self):
        if self.default_product is not None:
            return self.default_product.latest_version
        else:
            return LooseVersion(cfme_data.get("bugzilla", {}).get("upstream_version", "9.9"))

    def get_bug(self, id):
        id = int(id)
        if id not in self.__bug_cache:
            self.__bug_cache[id] = BugWrapper(self, self.bugzilla.getbugsimple(id))
        return self.__bug_cache[id]

    def get_bug_variants(self, id):
        if isinstance(id, BugWrapper):
            bug = id
        else:
            bug = self.get_bug(id)
        expanded = set([])
        found = set([])
        stack = set([bug])
        while stack:
            b = stack.pop()
            if b.status == "CLOSED" and b.resolution == "DUPLICATE":
                b = self.get_bug(b.dupe_of)
            found.add(b)
            if b.copy_of:
                stack.add(self.get_bug(b.copy_of))
            if b not in expanded:
                for cp in map(self.get_bug, b.copies):
                    found.add(cp)
                    stack.add(cp)
                expanded.add(b)
        return found

    def resolve_blocker(self, blocker, version=None, ignore_bugs=set([])):
        # ignore_bugs is mutable but is not mutated here!
        if isinstance(id, BugWrapper):
            bug = blocker
        else:
            bug = self.get_bug(blocker)
        if version is None:
            version = current_version()
        if version == LATEST:
            version = bug.product.latest_version
        variants = self.get_bug_variants(bug)
        filtered = set([])
        for variant in variants:
            if variant.id in ignore_bugs:
                continue
            if variant.version is not None and variant.version > version:
                continue
            if variant.release_flag is not None:
                if version.is_in_series(variant.release_flag):
                    # Simple case
                    filtered.add(variant)
                else:
                    logger.info(
                        "Ignoring bug #{}, appliance version not in bug release flag"
                        .format(variant.id))
            elif variant.release_flag is None:
                if variant.target_release is not None and variant.version is not None:
                    filtered.add(variant)
                else:
                    # Ignore this bug, must be a mistake
                    logger.info(
                        "Ignoring bug #{}, no release flag, target release & version specified."
                        .format(variant.id))
        if not filtered:
            return None
        # Prefer release_flag
        for bug in filtered:
            if bug.release_flag and version.is_in_series(bug.release_flag):
                return bug
        # Otherwise, use version, but forceskip these
        for bug in filtered:
            if bug.release_flag and version < bug.release_flag:
                return bug
            elif bug.version and bug.version <= version:
                return bug
        return None


class BugWrapper(object):
    _copy_matcher = re.compile(
        r"^\+\+\+ This bug was initially created as a clone of Bug #([0-9]+) \+\+\+")

    def __init__(self, bugzilla, bug):
        self._bug = bug
        self._bugzilla = bugzilla

    @property
    def loose(self):
        return self._bugzilla.loose

    @property
    def bugzilla(self):
        return self._bugzilla

    def __getattr__(self, attr):
        """This proxies the attribute queries to the Bug object and modifies its result.

        If the field looked up is specified as loose field, it will be converted to LooseVersion.
        If the field is string and it has zero length, or the value is specified as "not specified",
        it will return None.
        """
        value = getattr(self._bug, attr)
        if attr in self.loose:
            if isinstance(value, Sequence) and not isinstance(value, basestring):
                value = value[0]
            value = value.strip()
            if not value:
                return None
            if value.lower() in NONE_FIELDS:
                return None
            # We have to strip any leading non-number characters to correctly match
            return LooseVersion(re.sub(r"^[^0-9]+", "", value))
        if isinstance(value, basestring):
            if len(value.strip()) == 0:
                return None
            else:
                return value
        else:
            return value

    @property
    def qa_whiteboard(self):
        """Returns a set of QA Whiteboard markers.

        It relies on the fact, that our QA Whiteboard uses format foo:bar:baz.

        Should be able to handle cases like 'foo::bar', or 'abc:'.
        """
        return set([x.strip() for x in self._bug.qa_whiteboard.strip().split(":") if x.strip()])

    @property
    def copy_of(self):
        """Returns either id of the bug this is copy of, or None, if it is not a copy."""
        try:
            first_comment = self._bug.comments[0]["text"].lstrip()
        except IndexError:
            return None
        copy_match = self._copy_matcher.match(first_comment)
        if copy_match is None:
            return None
        else:
            return int(copy_match.groups()[0])

    @property
    def copies(self):
        """Returns list of copies of this bug."""
        result = []
        for bug_id in self._bug.blocks:
            bug = self._bugzilla.get_bug(bug_id)
            if bug.copy_of == self._bug.id:
                result.append(bug_id)
        return map(int, result)

    @property
    def _release_flag_data(self):
        for flag in self.flags:
            if flag["name"].startswith("cfme-"):
                release_flag = flag["name"].split("-", 1)[-1]
                if release_flag.endswith(".z"):
                    return release_flag.rsplit(".", 1)[0], True
                else:
                    return release_flag, False
        else:
            return None, False

    @property
    def release_flag(self):
        return self._release_flag_data[0]

    @property
    def zstream(self):
        return self._release_flag_data[1]

    @property
    def is_upstream_bug(self):
        return self._bugzilla.upstream_version == self.release_flag

    @property
    def is_opened(self):
        if self.is_upstream_bug and not appliance_is_downstream():
            states = self._bugzilla.open_states
        else:
            states = self._bugzilla.open_states + ["POST"]
        return self.status in states

    @property
    def product(self):
        return self._bugzilla.product(self._bug.product)

    @property
    def upstream_bug(self):
        if self.version is None:
            return True
        return self.version >= self.product.latest_version

    @property
    def can_test_on_upstream(self):
        change_states = {"POST", "MODIFIED"}
        # With these states, the change is in upstream
        if self.status not in {"POST", "MODIFIED", "ON_QA", "VERIFIED", "RELEASE_PENDING"}:
            return False
        history = self.get_history()["bugs"][0]["history"]
        changes = []
        # We look for status changes in the history
        for event in history:
            for change in event["changes"]:
                if change["field_name"].lower() != "status":
                    continue
                if change["added"] in change_states:
                    changes.append(event["when"])
                    return event["when"] < appliance_build_datetime()
        else:
            return False

    def __repr__(self):
        return repr(self._bug)

    def __str__(self):
        return str(self._bug)
