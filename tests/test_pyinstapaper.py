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
    'oauth_token_secret=abc&oauth_token=xyz'
)

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


def request_side_effect(*args, **kwargs):
    path = args[0]
    if path.endswith('oauth/access_token'):
        return LOGIN_RESPONSE
    elif path.endswith('bookmarks/list'):
        return BOOKMARKS_RESPONSE
    elif path.endswith('bookmarks/star'):
        return BOOKMARK_STAR_RESPONSE


class TestPyInstapaper(unittest.TestCase):

    def setUp(self):  # noqa
        pass

    @patch('oauth2.Client')
    def test_api_methods(self, oauth2_client_patched):
        # TODO: break out into more specific tests
        client = Instapaper('KEY', 'SECRET')
        oauth_client = oauth2_client_patched.return_value
        oauth_client.request.side_effect = request_side_effect
        client.login('USERNAME', 'PASSWORD')
        bookmarks = client.get_bookmarks()
        for ct, bookmark in enumerate(bookmarks):
            self.assertIsInstance(bookmark, Bookmark)
        bookmark.star()
        # TODO: test bookmark output

    def tearDown(self):  # noqa
        pass
