from __future__ import absolute_import, unicode_literals

from datetime import datetime

from django.template.defaultfilters import date
from django.utils.timezone import localtime, now


def today():
    return localtime(now()).date()


def duration_info(start, end=None):
    """
    Human readable representation of a time interval.
    """
    if not isinstance(start, datetime):
        return ""

    local_start = localtime(start)
    out = date(local_start, "DATETIME_FORMAT")
    if end not in (None, start):
        local_end = localtime(end)
        if local_end.date() == local_start.date():
            out += " to {}".format(date(local_end, "TIME_FORMAT"))
        else:
            out += " to {}".format(date(local_end, "DATETIME_FORMAT"))
    return out
