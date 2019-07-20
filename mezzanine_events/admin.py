from __future__ import absolute_import, unicode_literals

from copy import deepcopy

from django.conf.urls import url
from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect

from mezzanine.core.admin import TabularDynamicInlineAdmin, DisplayableAdmin, OwnableAdmin
from mezzanine.utils.admin import admin_url

from .models import Event, Occurrence, EventCategory
from .event_import import EventImportMixin


class OccurrenceInlineAdmin(TabularDynamicInlineAdmin):
    model = Occurrence
    extra = 0
    min_num = 1


@admin.register(Event)
class EventAdmin(DisplayableAdmin, OwnableAdmin, EventImportMixin):
    fieldsets = [
        (None, {"fields": ["title", "status", "featured", "featured_image", "link", "content"]}),
        ("Location", {"classes": ["collapse-closed"], "fields": ["location", "address"]}),
        (
            "Advanced Options",
            {
                "classes": ["collapse-closed"],
                "fields": [("publish_date", "expiry_date"), "categories", "related_events"],
            },
        ),
        deepcopy(DisplayableAdmin.fieldsets[-1]),  # Meta panel
    ]
    filter_horizontal = ("categories", "related_events")
    inlines = (OccurrenceInlineAdmin,)

    list_display = ["admin_thumb", "title", "featured", "user", "status"]
    list_editable = ["featured"]

    def save_form(self, request, form, change):
        """
        Super class ordering is important here - user must get saved first.
        """
        OwnableAdmin.save_form(self, request, form, change)
        return DisplayableAdmin.save_form(self, request, form, change)

    def get_urls(self):
        """
        Add custom admin views.
        """
        urls = super(EventAdmin, self).get_urls()
        extra_urls = [
            url(
                "^import/$",
                self.admin_site.admin_view(self.import_from_url),
                name="mezzanine_events_event_import",
            ),
            url(
                r"^(?P<event_id>\d+)/duplicate/$",
                self.admin_site.admin_view(self.duplicate_event),
                name="mezzanine_events_event_duplicate",
            ),
        ]
        return extra_urls + urls

    def duplicate_event(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        duplicate = event.duplicate()
        msg = "Event duplication complete. You can edit the duplicate below."
        self.message_user(request, msg)
        return redirect(admin_url(Event, "change", duplicate.pk))


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    fields = ["title"]
    list_display = ["title", "order"]
    list_editable = ["order"]
