from __future__ import absolute_import, unicode_literals

from django.test import TestCase


class SimpleTest(TestCase):
    def dummy_test(self):
        self.assertTrue(True)
