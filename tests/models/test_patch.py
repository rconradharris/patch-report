import datetime
import unittest

from patch_report.models import patch


class ParseMetadataTests(unittest.TestCase):
    data = """\
From ply Mon Sep 17 00:00:00 2001
From: Foo Bar <foo.bar@example.com>
Date: Tue, 4 Jun 2013 03:35:51 -0500
Subject: Category: First line

This is the rest of the commit message.
More lines here.

diff --git a/doc/api_samples/all_extensions/extensions-get-resp.json b/doc/api_samples/all_extensions/extensions-get-resp.json
"""
    def test_success(self):
        metadata = patch._parse_metadata(self.data)
        self.assertEqual('Foo Bar', metadata['author'])
        self.assertEqual('foo.bar@example.com', metadata['author_email'])
        self.assertEqual(datetime.datetime(2013, 6 , 4, 3, 35, 51),
                         metadata['date'])
        expected_commit_message = """\
Category: First line

This is the rest of the commit message.
More lines here."""
        self.assertEqual(expected_commit_message, metadata['commit_message'])
        self.assertEqual(
            ['doc/api_samples/all_extensions/extensions-get-resp.json'],
            metadata['files'])
        self.assertEqual(9, metadata['line_count'])
