from __future__ import absolute_import, unicode_literals

from django import forms

from .models import EventCategory
from .utils import today


class GridFilterForm(forms.Form):
    """
    Collection of fields to filter EventDateTimes in the grid view.
    """

    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.all(),
        widget=forms.widgets.CheckboxSelectMultiple,
        required=False,
    )

    def filter(self, qs):
        """
        Filter Events according to the field values.
        """
        categories = self.cleaned_data["categories"]

        if categories:
            qs = qs.filter(event__categories__in=categories)
        return qs


class ListFilterForm(GridFilterForm):
    """
    Collection of fields to filter EventDateTimes in the list view.
    This is used to determine the start and end of the events shown.
    """

    start_day = forms.DateField(input_formats=["%m/%d/%Y"], required=False)
    end_day = forms.DateField(input_formats=["%m/%d/%Y"], required=False)

    field_order = ("start_day", "end_day", "categories")  # Set order

    def clean(self):
        """
        Validate start/end days.
        Ideally start_day should always be defined no matter what the user enters
        to ensure the list view doesn't display all events ever.
        """
        cleaned_data = super(ListFilterForm, self).clean()

        # Always set a value for start_day
        start = cleaned_data.get("start_day") or today()
        end = cleaned_data.get("end_day")
        if end is not None and end < start:
            end = None

        cleaned_data.update({"start_day": start, "end_day": end})
        return cleaned_data
