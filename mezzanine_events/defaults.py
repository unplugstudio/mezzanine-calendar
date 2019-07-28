from __future__ import absolute_import, unicode_literals

from mezzanine.conf import register_setting

register_setting(
    name="EVENTS_FEATURED_PER_PAGE",
    label="Featured events per page",
    description="Applies to featured events in the list view",
    editable=True,
    default=10,
)

register_setting(
    name="EVENTS_PER_PAGE",
    label="Events per page",
    description="Applies to regular events in the list view",
    editable=True,
    default=10,
)
