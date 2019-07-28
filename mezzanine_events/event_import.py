from __future__ import absolute_import, unicode_literals

import json
import os
import requests

from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from urlparse import urlparse, urljoin, unquote

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.serializers import deserialize
from django.shortcuts import render, redirect

from mezzanine.utils.admin import admin_url
from mezzanine.utils.sites import current_site_id

from .models import Event
from .utils import convert


class EventImportError(Exception):
    pass


class EventImportMixin(object):
    """
    Imports events from other sites by their URL.
    """

    template_name = "admin/mezzanine_events/event/import.html"

    def get_event_data(self, event_url):
        """
        Get the JSON data for an event.
        We start with the public Event URL, then determine and fetch the JSON url.
        Returns the URL of the JSON resource and the serialized event data.
        """
        try:
            response = requests.get(event_url)
            response.raise_for_status()
        except RequestException as e:
            raise EventImportError("Request failed: %s." % e)

        # Find the URL of the JSON data for the event by parsing the HTML
        # We're looking for: <link rel="alternate" type="application/json" href="THE URL">
        try:
            soup = BeautifulSoup(response.text, "html5lib")
            json_url = soup.find(attrs={"rel": "alternate", "type": "application/json"})["href"]
        except (TypeError, KeyError):
            raise EventImportError(
                "Couldn't find JSON URL for this event. Does the site support event importing?"
            )

        # Make sure json_url is absolute and under the right hostname
        # /some/url -> http://host.com/some/url
        if not json_url.startswith(("http://", "https://")):
            parts = urlparse(response.url)
            json_url = urljoin(parts.scheme + "://" + parts.hostname, json_url)

        # Request and parse the JSON data for the event
        try:
            json_response = requests.get(json_url)
            json_response.raise_for_status()
            return json_response.url, json_response.json()
        except RequestException as e:
            raise EventImportError("JSON request failed: %s." % e)
        except ValueError:
            raise EventImportError("Failed to parse JSON data for event.")

    def create_event(self, data, data_url, user):
        """
        Create an Event instance based on serialized data.
        The featured image will be retrieved from the original server
        and the EventDateTime instances will be attached.
        """
        converted = convert(data)
        items = deserialize("json", json.dumps([converted]), ignorenonexistent=True)
        event = list(items)[0].object
        event.id = None  # Ensure new event ID
        event.slug = event.generate_unique_slug()
        event.site_id = current_site_id()
        event.user = user

        if not event.location:
            event.location = data["fields"].get("location_title", "")

        # Get the original featured image and save it locally
        img_path = data["fields"].get("featured_image")
        if img_path:
            parts = urlparse(data_url)
            img_url = urljoin(parts.scheme + "://" + parts.hostname, "static/media/" + img_path)
            img_response = requests.get(img_url)
            if img_response.status_code == requests.codes.ok:
                _, filename = os.path.split(img_path)
                filepath = os.path.join("uploads", "events", unquote(filename))
                filepath = default_storage.save(filepath, ContentFile(img_response.content))
                event.featured_image = filepath

        # Discard all M2M data as it may cause integrity issues when saving
        event.m2m_data = {}
        # Commit the new event to the database (required before saving EventDateTimes)
        event.save()

        # Add EventDateTimes instances (for old Mezzanine Calendar objects)
        for dt in data.get("dateandtimes", []):
            dt = convert(dt)
            occ = deserialize("json", json.dumps([dt]), ignorenonexistent=True)
            occ = list(occ)[0].object
            occ.event = event
            occ.save()

        # Import occurrences (if available)
        for occ_data in data.get("occurrences", []):
            occ = occ_data["fields"].copy()
            occ.pop("event")
            event.occurrences.create(**occ)

        return event

    def import_from_url(self, request):
        """
        Import an event from another site.
        """

        def fail(message):
            """
            Display and error message and reload the page.
            """
            self.message_user(request, message, level=messages.ERROR)
            return redirect(request.path)

        if request.method == "GET":
            template_name = self.template_name
            context = {"title": "Import event"}
            return render(request, template_name, context)

        try:
            event_url = request.POST["event-url"]
        except KeyError:
            return fail("Could not find 'event-url' in form data.")

        try:
            url, data = self.get_event_data(event_url)
        except EventImportError as e:
            return fail(str(e))

        event = self.create_event(data, data_url=url, user=request.user)

        self.message_user(request, "Event imported successfully")
        return redirect(admin_url(Event, "change", event.pk))
