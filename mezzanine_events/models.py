from __future__ import unicode_literals, absolute_import

from eventtools.models import BaseEvent, BaseOccurrence

from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import date, urlencode
from django.utils.encoding import python_2_unicode_compatible

from mezzanine.core.fields import FileField
from mezzanine.core.models import Displayable, Ownable, RichText, Slugged
from mezzanine.utils.models import AdminThumbMixin

from .managers import EventManager, OccurrenceManager
from .utils import duration_info


class Event(BaseEvent, Displayable, Ownable, RichText, AdminThumbMixin):
    """
    Events that get displayed in the calendar.  Start and end represent the range
    of times the event should cover in the calendar.
    """

    categories = models.ManyToManyField(
        "EventCategory", verbose_name="Categories", blank=True, related_name="events"
    )
    location = models.CharField("Location", max_length=200, blank=True)
    address = models.TextField("Address", blank=True)
    link = models.URLField("External link", blank=True, help_text="Link to purchase tickets")
    featured = models.BooleanField("Featured", default=False)
    featured_image = FileField(
        "Featured Image", upload_to="events", format="Image", max_length=255, blank=True
    )
    related_events = models.ManyToManyField("self", verbose_name="Related events", blank=True)

    search_fields = {"title": 10, "keywords": 10, "content": 5}
    admin_thumb_field = "featured_image"
    objects = EventManager()

    class Meta:
        verbose_name = "event"
        verbose_name_plural = "events"
        ordering = ("-featured",)

    def get_absolute_url(self):
        return reverse("mezzanine_events:event_detail", args=[self.slug])

    def directions_url(self):
        return "https://maps.google.com/maps?daddr=" + urlencode(self.location)

    def duplicate(self):
        """
        Create a copy of an existing Event instance.
        Used by staff users to speed-up creation of similar events.
        """
        dup = self.__class__.objects.get(pk=self.pk)
        dup.pk = None
        dup.title = "[Duplicate] %s" % self.title
        dup.slug = ""  # Let Mezzanine generate a unique slug
        dup.save()

        # Add the same categories
        dup.categories.add(*self.categories.all())

        # Duplicate EventDateTime instances
        for dt in self.occurrences.all():
            dt.pk = None
            dt.event = dup
            dt.save()

        return dup


@python_2_unicode_compatible
class Occurrence(BaseOccurrence):
    """
    Particular date and times associated with an event.  For example a play may
    have multiple different dates and times associated with it because it has
    various showings.
    """

    event = models.ForeignKey(Event, related_name="occurrences")

    objects = OccurrenceManager()

    def __str__(self):
        return duration_info(self.start, self.end)

    def repetition_info(self):
        if not self.repeat:
            return ""
        out = "Repeats {}".format(self.get_repeat_display().lower())
        if self.repeat_until:
            out += " until {}".format(date(self.repeat_until))
        return out


class EventCategory(Slugged):
    """
    A category for grouping events into a series.
    """

    order = models.PositiveIntegerField("Order", blank=True, null=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ("order",)

    def save(self, *args, **kwargs):
        """
        Set the initial ordering value.
        """
        if self.order is None:
            self.order = EventCategory.objects.filter(order__isnull=False).count()
        super(EventCategory, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Update the ordering values for siblings.
        """
        after = EventCategory.objects.filter(order__gte=self.order)
        after.update(order=models.F("order") - 1)
        super(EventCategory, self).delete(*args, **kwargs)
