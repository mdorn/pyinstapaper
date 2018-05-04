# -*- coding: utf-8 -*-
from datetime import datetime

import json
import logging
import time

import oauth2 as oauth

# for python2/3 compat
from future.moves.urllib.parse import urlencode, parse_qsl

BASE_URL = 'https://www.instapaper.com'
API_VERSION = '1'
ACCESS_TOKEN = 'oauth/access_token'
LOGIN_URL = 'https://www.instapaper.com/user/login'
REQUEST_DELAY_SECS = 0.5

log = logging.getLogger(__name__)


class Instapaper(object):
    '''Instapaper client class.

    :param oauth_key str: Instapaper OAuth consumer key
    :param oauth_secret str: Instapaper OAuth consumer secret
    '''

    def __init__(self, oauth_key, oauth_secret):
        self.consumer = oauth.Consumer(oauth_key, oauth_secret)
        self.oauth_client = oauth.Client(self.consumer)
        self.token = None

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
        token = dict(parse_qsl(response['data'].decode()))
        self.token = oauth.Token(
            token['oauth_token'], token['oauth_token_secret'])
        self.oauth_client = oauth.Client(self.consumer, self.token)

    def request(self, path, params=None, returns_json=True,
                method='POST', api_version=API_VERSION):
        '''Process a request using the OAuth client's request method.

        :param str path: Path fragment to the API endpoint, e.g. "resource/ID"
        :param dict params: Parameters to pass to request
        :param str method: Optional HTTP method, normally POST for Instapaper
        :param str api_version: Optional alternative API version
        :returns: response headers and body
        :retval: dict
        '''
        time.sleep(REQUEST_DELAY_SECS)
        full_path = '/'.join([BASE_URL, 'api/%s' % api_version, path])
        params = urlencode(params) if params else None
        log.debug('URL: %s', full_path)
        request_kwargs = {'method': method}
        if params:
            request_kwargs['body'] = params
        response, content = self.oauth_client.request(
            full_path, **request_kwargs)
        log.debug('CONTENT: %s ...', content[:50])
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

    def get_bookmarks(self, folder='unread', limit=25, have=None):
        """Return list of user's bookmarks.

        :param str folder: Optional. Possible values are unread (default),
            starred, archive, or a folder_id value.
        :param int limit: Optional. A number between 1 and 500, default 25.
        :param list have: Optional. A list of IDs to exclude from results
        :returns: List of user's bookmarks
        :rtype: list
        """
        path = 'bookmarks/list'
        params = {'folder_id': folder, 'limit': limit}
        if have:
            have_concat = ','.join(str(id_) for id_ in have)
            params['have'] = have_concat
        response = self.request(path, params)
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
        for attrib in self.ATTRIBUTES:
            val = data.get(attrib)
            if hasattr(self, 'TIMESTAMP_ATTRS'):
                if attrib in self.TIMESTAMP_ATTRS:
                    try:
                        val = datetime.fromtimestamp(int(val))
                    except ValueError:
                        log.warn(
                            'Could not cast %s for %s as datetime',
                            val, attrib
                        )
            setattr(self, attrib, val)
        self.object_id = getattr(self, self.RESOURCE_ID_ATTRIBUTE)
        for action in self.SIMPLE_ACTIONS:
            setattr(self, action, lambda x: self._simple_action(x))
            instance_method = getattr(self, action)
            try:
                instance_method.__defaults__ = (action,)
            except AttributeError:
                # ugh, for py2.7 compat
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
    TIMESTAMP_ATTRS = [
        'progress_timestamp',
        'time'
    ]
    SIMPLE_ACTIONS = [
        'delete',
        'star',
        'archive',
        'unarchive',
        'get_text'
    ]

    def __str__(self):
        return 'Bookmark %s: %s' % (self.object_id, self.title.encode('utf-8'))

    def get_highlights(self):
        '''Get highlights for Bookmark instance.

        :return: list of ``Highlight`` objects
        :rtype: list
        '''
        # NOTE: all Instapaper API methods use POST except this one!
        path = '/'.join([self.RESOURCE, str(self.object_id), 'highlights'])
        response = self.client.request(path, method='GET', api_version='1.1')
        items = response['data']
        highlights = []
        for item in items:
            if item.get('type') == 'error':
                raise Exception(item.get('message'))
            elif item.get('type') == 'highlight':
                highlights.append(Highlight(self, **item))
        return highlights


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
        'bookmark_id',
        'type',
        'slug',
    ]
    TIMESTAMP_ATTRS = [
        'time',
    ]
    SIMPLE_ACTIONS = [
        'delete',
    ]

    def __str__(self):
        return 'Highlight %s for Article %s' % (
            self.object_id, self.bookmark_id)

    def create(self):
        # TODO
        raise NotImplementedError
