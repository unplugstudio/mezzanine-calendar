from __future__ import absolute_import, unicode_literals

import io
import json

from datetime import datetime

from django.core.management.base import BaseCommand
from mezzanine_events.event_import import combine


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


def map_fields(fields, new_fields):
    for new_field in new_fields:
        old_field = new_field

        # Handle renamed fields
        if isinstance(new_field, tuple):
            new_field, old_field = new_field

        yield (new_field, fields[old_field])


class Command(BaseCommand):
    help = "Convert a Mezzanine Calendar JSON dump to Mezzanine Events"

    def add_arguments(self, parser):
        parser.add_argument(
            "input_file", help="File path to the JSON dump created by Mezzanine Calendar"
        )
        parser.add_argument("output_file", help="File path to the converted JSON output")

    def handle(self, *args, **options):
        with io.open(options["input_file"], "r") as f:
            input_items = json.load(f)

        self.complete = 0
        self.total = len(input_items)

        with io.open(options["output_file"], "wb") as f:
            json.dump([self.convert(item) for item in input_items], f)

    def convert(self, item):
        """
        Convert a single Mezzanine Calendar object into Mezzanine Events
        """
        self.complete += 1
        self.stdout.write("Processing {} of {}".format(self.complete, self.total), ending="\r")
        self.stdout.flush()

        # Event
        if item["model"] == "mezzanine_calendar.event":
            return {
                "model": "mezzanine_events.event",
                "pk": item["pk"],
                "fields": dict(map_fields(item["fields"], EVENT_FIELDS)),
            }

        # EventDateTime (renamed to Occurrence)
        elif item["model"] == "mezzanine_calendar.eventdatetime":
            f = item["fields"]
            fields = dict(map_fields(f, OCCURRENCE_FIELDS))

            start = combine(f["day"], f["start_time"] or datetime.min.time())
            fields["start"] = start.isoformat()

            fields["end"] = None
            if f["end_time"] is not None:
                end = combine(f["day"], f["end_time"])
                fields["end"] = end.isoformat()

            return {"model": "mezzanine_events.occurrence", "pk": item["pk"], "fields": fields}

        # EventCategory
        elif item["model"] == "mezzanine_calendar.eventcategory":
            fields = dict(map_fields(item["fields"], CATEGORY_FIELDS))
            fields["order"] = None
            return {"model": "mezzanine_events.eventcategory", "pk": item["pk"], "fields": fields}

        # Unknown model, output an empty dict
        self.stdout.write("Unknown model {}".format(item["model"]))
        return {}
