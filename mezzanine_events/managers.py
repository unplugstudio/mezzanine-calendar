from __future__ import absolute_import, unicode_literals

from django.db.models import Q
from django.utils.timezone import now

from mezzanine.core.managers import DisplayableManager, SearchableQuerySet
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

from eventtools.models import (
    EventQuerySet,
    EventManager as BaseEventManager,
    OccurrenceManager as BaseOccurrenceManager,
)


class SearchableEventQuerySet(SearchableQuerySet, EventQuerySet):
    pass


class EventManager(DisplayableManager, BaseEventManager):
    """
    Combine the managers of the parent classes for Event.
    """

    use_for_related_fields = True

    def get_queryset(self):
        search_fields = self.get_search_fields()
        return SearchableEventQuerySet(self.model, search_fields=search_fields)


class OccurrenceManager(BaseOccurrenceManager):
    def published(self):
        """
        Return items with a published status and whose publish and expiry dates
        fall before and after the current date when specified.
        """
        return self.filter(
            Q(event__publish_date__lte=now()) | Q(event__publish_date__isnull=True),
            Q(event__expiry_date__gte=now()) | Q(event__expiry_date__isnull=True),
            Q(event__status=CONTENT_STATUS_PUBLISHED),
        )

    def upcoming(self):
        """
        Retrieve published events that end today or in the future.
        """
        return self.published().for_period(from_date=now()).order_by("start")

    def past(self):
        """
        Retrieve published events that ended in the past.
        """
        return self.published().for_period(to_date=now()).order_by("-start")
