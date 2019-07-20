from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
from itertools import groupby

from calendar import Calendar
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.timezone import make_aware, localtime

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
    return redirect("calendar:event_grid", *today().strftime("%Y %m").split())


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
    return render(request, "calendar/event_grid.html", context)


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

    featured_occurrences = paginate(
        list(occurrences.filter(event__featured=True).all_occurrences(start, end)),
        page_num=request.GET.get("featured-page", 1),
        per_page=15,
        max_paging_links=10,
    )
    regular_occurrences = paginate(
        list(occurrences.filter(event__featured=False).all_occurrences(start, end)),
        page_num=request.GET.get("page", 1),
        per_page=15,
        max_paging_links=10,
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
    return render(request, "calendar/event_list.html", context)


def event_detail(request, slug, template="calendar/event_detail.html"):
    """
    Detail page for an event
    """
    events = Event.objects.published(for_user=request.user).select_related()
    event = get_object_or_404(events, slug=slug)
    templates = ["event/event_detail_{}.html".format(slug), template]
    if request.is_ajax():
        templates.insert(0, "calendar/event_detail_ajax.html")

    context = {
        "event": event,
        "editable_obj": event,
        "filter_form": ListFilterForm(),
        "filter_form_url": reverse("calendar:event_list"),
    }
    return render(request, templates, context)
