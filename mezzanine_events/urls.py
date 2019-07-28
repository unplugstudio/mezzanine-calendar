from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

app_name = "mezzanine_events"

urlpatterns = [
    url(r"^$", RedirectView.as_view(pattern_name="mezzanine_events:event_list"), name="home"),
    url(r"^month/$", views.month_redirect, name="month"),
    url(r"^list/$", views.event_list, name="event_list"),
    url(r"^(?P<year>\d{4})/(?P<month>0?[1-9]|1[012])/$", views.event_grid, name="event_grid"),
    url(r"^event/(?P<pk>\d+)/json/$", views.event_json, name="event_json"),
    url(r"^event/(?P<slug>.*)/$", views.event_detail, name="event_detail"),
]
