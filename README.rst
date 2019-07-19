Mezzanine Events
==================

Event system for Mezzanine CMS.

Install
-------

1. Install via pip: ``pip install mezzanine-events``.
2. Add ``mezzanine_events`` to your ``INSTALLED_APPS``.
3. Run migrations.
4. Add ``url("^events/", include("mezzanine_events.urls", namespace="events"))`` to you urls.py (you can also replace url prefix with any anything you prefer, but keep the namespace as "events")

Contributing
------------

Review contribution guidelines at CONTRIBUTING.md_.

.. _CONTRIBUTING.md: CONTRIBUTING.md
