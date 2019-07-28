from __future__ import absolute_import, unicode_literals

from datetime import datetime, date, time

from django.template.defaultfilters import date as datefmt
from django.utils.timezone import localtime, now, make_aware

EVENT_FIELDS = (
    "keywords_string",
    "site",
    "title",
    "slug",
    "_meta_title",
    "description",
    "gen_description",
    "created",
    "updated",
    "status",
    "publish_date",
    "expiry_date",
    "short_url",
    "in_sitemap",
    "content",
    "user",
    # "all_day",
    # "start",
    # "end",
    ("location", "location_title"),
    "address",
    "link",
    "featured",
    "featured_image",
    # "require_rsvp"
    # "rsvp_instructions"
    # "rsvp_response"
    # "rsvp_notification_emails"
    # "show_calendaring_links"
    "categories",
    "related_events",
)

CATEGORY_FIELDS = (
    "title",
    "site",
    "slug",
    # "sortable",
)

OCCURRENCE_FIELDS = ("event",)


def today():
    """
    Local current date
    """
    return localtime(now()).date()


def duration_info(start, end=None):
    """
    Human readable representation of a time interval.
    """
    if not isinstance(start, datetime):
        return ""

    local_start = localtime(start)
    out = datefmt(local_start, "DATETIME_FORMAT")
    if end not in (None, start):
        local_end = localtime(end)
        if local_end.date() == local_start.date():
            out += " to {}".format(datefmt(local_end, "TIME_FORMAT"))
        else:
            out += " to {}".format(datefmt(local_end, "DATETIME_FORMAT"))
    return out


def convert(obj):
    """
    Convert a single Mezzanine Calendar object into Mezzanine Events
    """

    def map_fields(fields, new_fields):
        for new_field in new_fields:
            old_field = new_field

            # Handle renamed fields
            if isinstance(new_field, tuple):
                new_field, old_field = new_field

            try:
                yield (new_field, fields[old_field])
            except KeyError:
                continue

    def combine_dt(d, t):
        """
        Combine naive date and time into an aware datetime
        """
        if not isinstance(d, date):
            d = datetime.strptime(d, "%Y-%m-%d").date()
        if not isinstance(t, time):
            t = datetime.strptime(t, "%H:%M:%S").time()
        return make_aware(datetime.combine(d, t))

    # Event
    if obj["model"] == "mezzanine_calendar.event":
        return {
            "model": "mezzanine_events.event",
            "pk": obj["pk"],
            "fields": dict(map_fields(obj["fields"], EVENT_FIELDS)),
        }

    # EventDateTime (renamed to Occurrence)
    elif obj["model"] == "mezzanine_calendar.eventdatetime":
        f = obj["fields"]
        fields = dict(map_fields(f, OCCURRENCE_FIELDS))

        start = combine_dt(f["day"], f["start_time"] or datetime.min.time())
        fields["start"] = start.isoformat()

        fields["end"] = None
        if f["end_time"] is not None:
            end = combine_dt(f["day"], f["end_time"])
            fields["end"] = end.isoformat()

        return {"model": "mezzanine_events.occurrence", "pk": obj["pk"], "fields": fields}

    # EventCategory
    elif obj["model"] == "mezzanine_calendar.eventcategory":
        fields = dict(map_fields(obj["fields"], CATEGORY_FIELDS))
        fields["order"] = None
        return {"model": "mezzanine_events.eventcategory", "pk": obj["pk"], "fields": fields}

    # Let everything else go through unchanged
    return obj
