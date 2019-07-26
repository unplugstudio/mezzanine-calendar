from __future__ import absolute_import, unicode_literals

from datetime import timedelta
from itertools import groupby, islice
from operator import itemgetter

from django import template
from django.template.defaultfilters import urlencode
from django.template.loader import get_template
from django.utils.timezone import now

from mezzanine.utils.sites import current_request

from ..models import EventCategory, Occurrence
from ..utils import duration_info

register = template.Library()
register.simple_tag(duration_info)


@register.filter(is_safe=True)
def google_calendar_url(dt):
    start_str = dt.start.strftime("%Y%m%dT%H%M%SZ")
    end = dt.end or (dt.start + timedelta(hours=1))
    end_str = end.strftime("%Y%m%dT%H%M%SZ")
    tokens = {
        "action": "TEMPLATE",
        "text": dt.event.title,
        "dates": "{}/{}".format(start_str, end_str),
        "details": current_request().build_absolute_uri(dt.event.get_absolute_url()),
        "location": dt.event.location.replace("\n", " "),
    }

    if dt.repeat:
        tokens["recur"] = dt.repeat
        if dt.repeat_until:
            tokens["recur"] += ";UNTIL=" + dt.repeat_until.strftime("%Y%m%d")

    pairs = ("{}={}".format(k, urlencode(v)) for k, v in tokens.items())
    return "https://www.google.com/calendar/event?" + "&".join(pairs)


@register.simple_tag(takes_context=True)
def upcoming_occurrences(
    context, category_slug=None, limit=5, template="calendar/includes/upcoming_occurrences.html"
):
    """
    Return a limited number of upcoming event occurrences.
    Optionally can be filtered by category slug.
    """
    occurrences = Occurrence.objects.published()
    try:
        category = EventCategory.objects.get(slug=category_slug)
        context["category"] = category
        occurrences = occurrences.filter(event__categories=category)
    except EventCategory.DoesNotExist:
        context["category"] = None

    # Sort and group by event (grouping doesn't work without sorting)
    by_event = lambda x: x[2].event_id
    occurrence_tuples = occurrences.all_occurrences(from_date=now())
    occurrence_tuples = sorted(occurrence_tuples, key=by_event)
    unique_occurrences = (next(tuples) for event, tuples in groupby(occurrence_tuples, by_event))
    # Sort by the first item (start date) again
    unique_occurrences = sorted(unique_occurrences, key=itemgetter(0))
    context["occurrences"] = islice(unique_occurrences, limit)
    return get_template(template).render(context.flatten())
