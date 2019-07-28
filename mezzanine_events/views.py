from __future__ import absolute_import, unicode_literals

import json

from calendar import Calendar
from datetime import datetime, timedelta
from itertools import groupby

from django.core.serializers import serialize
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import make_aware, localtime, now

from mezzanine.conf import settings
from mezzanine.utils.views import paginate

from .forms import GridFilterForm, ListFilterForm
from .models import Event, Occurrence
from .utils import today


def get_date(occurrence_tuple):
    start, end, original_occurrence = occurrence_tuple
    return localtime(start).date()


def month_redirect(request):
    """
    Redirect to the grid for the current month.
    """
    return redirect("mezzanine_events:event_grid", *today().strftime("%Y %m").split())


def event_grid(request, year, month):
    """
    Classic grid view of the occurrences for a given month.
    """
    year, month = int(year), int(month)
    current_month = datetime(year, month, 1)
    cal = Calendar(firstweekday=6).monthdatescalendar(year, month)  # Start on Sunday
    days_in_month = max(dt.day for dt in cal[-1])
    first_day = datetime.combine(cal[0][0], datetime.min.time())
    first_day = make_aware(first_day)
    last_day = datetime.combine(cal[-1][-1], datetime.max.time())
    last_day = make_aware(last_day)

    form = GridFilterForm(request.GET)
    occurrences = Occurrence.objects.published().select_related("event")
    if form.is_valid():
        occurrences = form.filter(occurrences)
    occurrence_tuples = occurrences.all_occurrences(first_day, last_day)

    by_day = dict((dt, list(occ)) for dt, occ in groupby(occurrence_tuples, get_date))
    context = {
        "today": today(),
        "filter_form": form,
        "filter_form_url": request.path,
        "current_month": current_month,
        "prev_month": current_month + timedelta(days=-1),
        "next_month": current_month + timedelta(days=+days_in_month),
        "calendar": [[(dt, by_day.get(dt, [])) for dt in week] for week in cal],
    }
    return render(request, "mezzanine_events/event_grid.html", context)


def event_list(request):
    """
    List view of all events.
    The filter form determines the start and end date interval.
    """
    start = None
    end = None
    form = ListFilterForm(request.GET)
    occurrences = Occurrence.objects.published().select_related("event")

    if form.is_valid():
        occurrences = form.filter(occurrences)
        start = form.cleaned_data["start_day"]
        end = form.cleaned_data["end_day"]

    # Adjust to include the current time if start is set to today
    if start == today():
        start = now()

    featured_occurrences = paginate(
        list(occurrences.filter(event__featured=True).all_occurrences(start, end)),
        page_num=request.GET.get("featured-page", 1),
        per_page=settings.EVENTS_FEATURED_PER_PAGE,
        max_paging_links=settings.MAX_PAGING_LINKS,
    )
    regular_occurrences = paginate(
        list(occurrences.filter(event__featured=False).all_occurrences(start, end)),
        page_num=request.GET.get("page", 1),
        per_page=settings.EVENTS_PER_PAGE,
        max_paging_links=settings.MAX_PAGING_LINKS,
    )

    context = {
        "today": today(),
        "start_day": start,
        "end_day": end,
        "filter_form": form,
        "filter_form_url": request.path,
        "featured_occurrences": featured_occurrences,
        "occurrences": regular_occurrences,
    }
    return render(request, "mezzanine_events/event_list.html", context)


def event_detail(request, slug):
    """
    Detail page for an event.
    """
    templates = [
        "mezzanine_events/event_detail_{}.html".format(slug),
        "mezzanine_events/event_detail.html",
    ]
    if request.is_ajax():
        templates.insert(0, "mezzanine_events/event_detail_ajax.html")

    events = Event.objects.published(for_user=request.user).select_related()
    event = get_object_or_404(events, slug=slug)

    context = {
        "event": event,
        "editable_obj": event,
        "filter_form": ListFilterForm(),
        "filter_form_url": reverse("mezzanine_events:event_list"),
    }
    return render(request, templates, context)


def event_json(request, pk):
    """
    Returns a JSON representation of an Event.
    Other sites can use this endpoint to import events.
    """
    event = get_object_or_404(Event.objects.published(), pk=pk)
    event_dict = json.loads(serialize("json", [event]))[0]
    event_dict["occurrences"] = json.loads(serialize("json", event.occurrences.all()))
    return HttpResponse(json.dumps(event_dict), content_type="application/json")
