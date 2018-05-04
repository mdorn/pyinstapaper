#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pyinstapaper
----------------------------------

Tests for `pyinstapaper` module.
"""

import unittest

from mock import patch

from pyinstapaper.instapaper import Instapaper, Bookmark


LOGIN_RESPONSE = (
    {'status': '200'},
    b'oauth_token_secret=abc&oauth_token=xyz'
)

# TODO: use pytest fixtures
BOOKMARKS_RESPONSE = (
    {'status': '200'},
    '''
[
    {
        "type":"meta"
    },
    {
        "username":"foo@bar.com",
        "user_id":123,
        "type":"user",
        "subscription_is_active":"1"
    },
    {
        "hash":"D2nAUhDQ",
        "description":"",
        "bookmark_id": 123,
        "private_source":"",
        "title":"Hello World",
        "url":"http://helloworld.com/2015/4/hello",
        "progress_timestamp":0,
        "time":1444260591,
        "progress":0.0,
        "starred":"0",
        "type":"bookmark"
    },
    {
        "hash":"iQoraJpo",
        "description":"",
        "bookmark_id":124,
        "private_source":"",
        "title":"Another Example",
        "url":"http://www.googl.com/blah/blah/",
        "progress_timestamp":0,
        "time":1444260572,
        "progress":0.0,
        "starred":"0",
        "type":"bookmark"
    },
    {
        "hash":"k1lEcIHO",
        "description":"",
        "bookmark_id":125,
        "private_source":"",
        "title":"Foo Bar",
        "url":"http://www.example.com/foo/bar/",
        "progress_timestamp":0,
        "time":1444245139,
        "progress":0.0,
        "starred":"0",
        "type":"bookmark"
    }
]
    '''
)

BOOKMARK_STAR_RESPONSE = (
    {'status': '200'},
    '''
[
    {
        "bookmark_id":125,
        "title":"Foo Bar",
        "url":"http://www.example.com/foo/bar/",
        "starred":"1",
        "type":"bookmark"
    }
]
    '''
)

HIGHLIGHTS_RESPONSE = (
    {'status': '200'},
    '''
[
    {
        "highlight_id": 123,
        "text": "Here is the highlighted text",
        "bookmark_id": 123,
        "time": 1443559223,
        "position": 0,
        "type": "highlight"
    },
    {
        "highlight_id": 456,
        "text": "an important phrase",
        "bookmark_id": 123,
        "time": 1443559223,
        "position": 0,
        "type": "highlight"
    }
]
    ''')


def request_side_effect(*args, **kwargs):
    path = args[0]
    if path.endswith('oauth/access_token'):
        return LOGIN_RESPONSE
    elif path.endswith('bookmarks/list'):
        return BOOKMARKS_RESPONSE
    elif path.endswith('bookmarks/star'):
        return BOOKMARK_STAR_RESPONSE
    elif path.endswith('/highlights'):
        return HIGHLIGHTS_RESPONSE


class TestPyInstapaper(unittest.TestCase):

    def setUp(self):  # noqa
        pass

    @patch('oauth2.Client')
    def _get_pacthed_client(self, oauth2_client_patched):
        client = Instapaper('KEY', 'SECRET')
        oauth_client = oauth2_client_patched.return_value
        oauth_client.request.side_effect = request_side_effect
        client.login('USERNAME', 'PASSWORD')
        return client

    def test_bookmarks(self):
        client = self._get_pacthed_client()
        bookmarks = client.get_bookmarks()
        for ct, bookmark in enumerate(bookmarks):
            self.assertIsInstance(bookmark, Bookmark)

        bookmark = bookmarks[0]
        self.assertEqual(bookmark.title, 'Hello World')
        bookmark.star()
        # TODO: test bookmark.star output

    def test_highlights(self):
        client = self._get_pacthed_client()
        bookmarks = client.get_bookmarks()
        bookmark = bookmarks[0]
        highlights = bookmark.get_highlights()
        self.assertEqual(len(highlights), 2)
        highlight = highlights[0]
        self.assertEqual(highlight.text, 'Here is the highlighted text')

    def tearDown(self):  # noqa
        pass
