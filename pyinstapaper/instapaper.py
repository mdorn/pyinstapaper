# -*- coding: utf-8 -*-

import json
import logging
import re
import requests
import time
import urlparse
from urllib import urlencode

import oauth2 as oauth
from lxml import etree

BASE_URL = 'https://www.instapaper.com'
API_VERSION = 'api/1'
ACCESS_TOKEN = 'oauth/access_token'
LOGIN_URL = 'https://www.instapaper.com/user/login'
REQUEST_DELAY_SECS = 0.2

log = logging.getLogger(__name__)


class FakeBrowserClient(object):
    # DISCLAIMER: The code for this class is made available for educational
    #   purposes only. Use of it may or may not conform to the service's
    #   acceptable use policy.

    def __init__(self):
        self.session = None

    def login(self, login_url, username, password):
        post_vals = {
            'username': username,
            'password': password,
            'keep_logged_in': 'yes'
        }
        headers = {}

        self.session = requests.Session()
        log.info('Logging in as user %s' % username)
        response = self.session.post(
            login_url, data=post_vals, headers=headers)
        # TODO: validate login

    def get_response(self, url, method='GET', post_vals=None, headers={},
                     returns_json=False):
        time.sleep(REQUEST_DELAY_SECS)
        log.info('Requesting URL %s', url)
        if method == 'POST':
            request_method = getattr(self.session, 'post')
        else:
            request_method = getattr(self.session, 'get')
        response = request_method(url, data=post_vals, headers=headers)
        if returns_json:
            msg_dict = json.loads(response.content)
            return msg_dict
        else:
            return response.content


class Instapaper(object):
    '''Instapaper client class.

    :param oauth_key str: Instapaper OAuth consumer key
    :param oauth_secret str: Instapaper OAuth consumer secret
    '''

    def __init__(self, oauth_key, oauth_secret, with_scraper=False):
        self.consumer = oauth.Consumer(oauth_key, oauth_secret)
        self.oauth_client = oauth.Client(self.consumer)
        self.token = None
        self.scraper = FakeBrowserClient() if with_scraper else None

    def login(self, username, password):
        '''Authenticate using XAuth variant of OAuth.

        :param str username: Username or email address for the relevant account
        :param str password: Password for the account
        '''
        response = self.request(
            ACCESS_TOKEN,
            {
                'x_auth_mode': 'client_auth',
                'x_auth_username': username,
                'x_auth_password': password
            },
            returns_json=False
        )
        token = dict(urlparse.parse_qsl(response['data']))
        self.token = oauth.Token(
            token['oauth_token'], token['oauth_token_secret'])
        self.oauth_client = oauth.Client(self.consumer, self.token)
        if self.scraper:
            self.scraper.login(LOGIN_URL, username, password)

    def request(self, path, params=None, returns_json=True,
                api_version=API_VERSION):
        '''Process a request using the OAuth client's request method.

        :param str path: Path fragment to the API endpoint, e.g. "resource/ID"
        :param dict params: Parameters to pass to request
        :param str api_version: Optional alternative API version
        :returns: response headers and body
        :retval: dict
        '''
        time.sleep(REQUEST_DELAY_SECS)
        full_path = '/'.join([BASE_URL, api_version, path])
        params = urlencode(params) if params else None
        response, content = self.oauth_client.request(
            full_path, method='POST', body=params
        )
        log.debug('URL: %s; CONTENT: %s ...', full_path, content[:50])
        if returns_json:
            try:
                data = json.loads(content)
                if isinstance(data, list) and len(data) == 1:
                    # ugly -- API always returns a list even when you expect
                    # only one item
                    if data[0]['type'] == 'error':
                        raise Exception('Instapaper error %d: %s' % (
                            data[0]['error_code'],
                            data[0]['message'])
                        )
                    # TODO: PyInstapaperException custom class?
            except ValueError:
                # Instapaper API can be unpredictable/inconsistent, e.g.
                # bookmarks/get_text doesn't return JSON
                data = content
        else:
            data = content
        return {
            'response': response,
            'data': data
        }

    def get_bookmarks(self, folder='unread', limit=10):
        """Return list of user's bookmarks.

        :param str folder: Optional. Possible values are unread (default),
            starred, archive, or a folder_id value.
        :param int limit: Optional. A number between 1 and 500, default 25.
        :returns: List of user's bookmarks
        :rtype: list
        """
        path = 'bookmarks/list'
        response = self.request(path, {'folder_id': folder, 'limit': limit})
        items = response['data']
        bookmarks = []
        for item in items:
            if item.get('type') == 'error':
                raise Exception(item.get('message'))
            elif item.get('type') == 'bookmark':
                bookmarks.append(Bookmark(self, **item))
        return bookmarks

    def get_folders(self):
        """Return list of user's folders.

        :rtype: list
        """
        path = 'folders/list'
        response = self.request(path)
        items = response['data']
        folders = []
        for item in items:
            if item.get('type') == 'error':
                raise Exception(item.get('message'))
            elif item.get('type') == 'folder':
                folders.append(Folder(self, **item))
        return folders


class InstapaperObject(object):

    '''Base class for Instapaper objects like Bookmark.

    :param client: instance of the OAuth client for making requests
    :type client: ``oauth2.Client``
    :param dict data: key/value pairs of object attributes, e.g. title, etc.
    '''

    def __init__(self, client, **data):
        self.client = client
        self.scraped_content = None
        for attrib in self.ATTRIBUTES:
            setattr(self, attrib, data.get(attrib))
        self.object_id = getattr(self, self.RESOURCE_ID_ATTRIBUTE)
        for action in self.SIMPLE_ACTIONS:
            setattr(self, action, lambda x: self._simple_action(x))
            instance_method = getattr(self, action)
            instance_method.func_defaults = (action,)

    def add(self):
        '''Save an object to Instapaper after instantiating it.

        Example::

            folder = Folder(instapaper, title='stuff')
            result = folder.add()
        '''
        # TODO validation per object type
        submit_attribs = {}
        for attrib in self.ATTRIBUTES:
            val = getattr(self, attrib, None)
            if val:
                submit_attribs[attrib] = val
        path = '/'.join([self.RESOURCE, 'add'])
        result = self.client.request(path, submit_attribs)
        return result

    def _simple_action(self, action=None):
        '''Issue a request for an API method whose only param is the obj ID.

        :param str action: The name of the action for the resource
        :returns: Response from the API
        :rtype: dict
        '''
        if not action:
            raise Exception('No simple action defined')
        path = "/".join([self.RESOURCE, action])
        response = self.client.request(
            path, {self.RESOURCE_ID_ATTRIBUTE: self.object_id}
        )
        return response


class Bookmark(InstapaperObject):

    '''Object representing an Instapaper bookmark/article.'''

    RESOURCE = 'bookmarks'
    RESOURCE_ID_ATTRIBUTE = 'bookmark_id'
    # TODO: identify which fields to convert from timestamp to Python datetime
    ATTRIBUTES = [
        'bookmark_id',
        'title',
        'description',
        'hash',
        'url',
        'progress_timestamp',
        'time',
        'progress',
        'starred',
        'type',
        'private_source'
    ]
    SIMPLE_ACTIONS = [
        'delete',
        'star',
        'archive',
        'unarchive',
        'get_text'
    ]

    def __str__(self):
        return 'Bookmark %s: %s' % (self.object_id, self.title)

    def get_highlights(self):
        '''Get highlights for Bookmark instance.

        :return: list of ``Highlight`` objects
        :rtype: list
        '''
        # NOTE: get highlights the normal way when API is fixed, as below;
        #   highlights API endpoint still broken as of 5-Oct-2015
        # path = '/'.join(self.RESOURCE, str(self.object_id), 'highlights')
        # response = self.request(path, api_version='1.1')
        # return response

        highlights = []
        if not self.scraped_content:
            raise Exception('Scraped content not set.')
        pattern = 'highlightWithJson\((.*)\)'
        result = re.findall(pattern, self.scraped_content)
        highlights = []
        if result:
            items = json.loads(result[0])
            for item in items:
                highlights.append(Highlight(self, **item))
        return highlights

    ###
    # "Unofficial" API methods below. DISCLAIMER: for educational purposes only
    ###

    def set_scraped_content(self):
        if not self.client.scraper:
            raise Exception('Must instantiate client with scraper.')
        result = self.client.scraper.get_response(
            'https://www.instapaper.com/read/%s' % self.object_id)
        self.scraped_content = result

    def get_origin_line(self):
        # NOTE: Author name and publication date not included in API, maybe
        #   because auto-retrieving that information is not reliable ... ?
        if not self.scraped_content:
            raise Exception('Scraped content not set.')
        parser = etree.HTMLParser()
        tree = etree.fromstring(self.scraped_content, parser)
        origin_element = tree.xpath('//*[@class="origin_line"]')[0]
        origin_html = etree.tostring(origin_element)
        return origin_html


class Folder(InstapaperObject):

    '''Object representing an Instapaper folder.'''

    RESOURCE = 'folders'
    RESOURCE_ID_ATTRIBUTE = 'folder_id'
    ATTRIBUTES = [
        'folder_id',
        'title',
        'display_title',
        'sync_to_mobile',
        'folder_id',
        'position',
        'type',
        'slug',
    ]
    SIMPLE_ACTIONS = [
        'delete',
    ]

    def __str__(self):
        return 'Folder %s: %s' % (self.object_id, self.title)

    def set_order(self, folder_ids):
        """Order the user's folders

        :param list folders: List of folder IDs in the desired order.
        :returns: List Folder objects in the new order.
        :rtype: list
        """
        # TODO
        raise NotImplementedError


class Highlight(InstapaperObject):

    '''Object representing an Instapaper highlight.'''

    RESOURCE = 'highlights'
    RESOURCE_ID_ATTRIBUTE = 'highlight_id'

    ATTRIBUTES = [
        'highlight_id',
        'text',
        'note',
        'time',
        'position',
        'article_id',
        'type',
        'slug',
    ]
    SIMPLE_ACTIONS = [
        'delete',
    ]

    def __str__(self):
        return 'Highlight %s for Article %s' % (
            self.object_id, self.article_id)

    def create(self):
        # TODO
        raise NotImplementedError
