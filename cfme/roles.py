from utils.conf import cfme_data
from utils import version
from utils.log import logger


def _remove_page(roles, group, pages):
    if group in roles:
        for page in pages:
            if page in roles[group]:
                roles[group].remove(page)
            else:
                logger.info("Page {} attempted to be removed from role {}, "
                            "but isn't in there anyway".format(page, group))
    else:
        logger.info("Attempted to remove a page from role {}, but role "
                    "doesn't exist".format(group))


def _remove_from_all(roles, r_page):
    for group in roles:
        for page in roles[group]:
            if page == r_page:
                roles[group].remove(page)
            else:
                logger.info("Page {} attempted to be removed from role {}, "
                            "but isn't in there anyway".format(page, group))


def group_data():
    roles = cfme_data.get('group_roles', {})

    # These roles are not present on 5.2 appliance in these groups
    if version.current_version() < '5.3':
        _remove_page(roles, 'evmgroup-super_administrator', ['clouds_tenants'])
        _remove_page(roles, 'evmgroup-user', ['services_requests', 'infrastructure_requests'])
    if version.current_version() < '5.4':
        _remove_from_all(roles, 'clouds_stacks')
        _remove_from_all(roles, 'infrastructure_config_management')
    return roles
