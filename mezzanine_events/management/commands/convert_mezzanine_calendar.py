from __future__ import absolute_import, unicode_literals

import io
import json

from django.core.management.base import BaseCommand
from mezzanine_events.utils import convert


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

        complete = 0
        total = len(input_items)
        output_items = []

        for item in input_items:
            output_items.append(convert(item))
            complete += 1
            self.stdout.write("Processing {} of {}".format(complete, total), ending="\r")
            self.stdout.flush()

        with io.open(options["output_file"], "wb") as f:
            json.dump(output_items, f)
