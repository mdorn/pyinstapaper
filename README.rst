============
PyInstapaper
============


.. image:: https://img.shields.io/pypi/v/pyinstapaper.svg
        :target: https://pypi.python.org/pypi/pyinstapaper

.. image:: https://img.shields.io/travis/mdorn/pyinstapaper.svg
        :target: https://travis-ci.org/mdorn/pyinstapaper

.. image:: https://readthedocs.org/projects/pyinstapaper/badge/?version=latest
        :target: https://pyinstapaper.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Instapaper_ is a tool for saving web pages to read later, e.g. offline on a
mobile device.  PyInstapaper is a Python wrapper for the `full Instapaper API`_.

.. _Instapaper: https://www.instapaper.com
.. _full Instapaper API: https://www.instapaper.com/api

To use it, in addition to your Instapaper account username and password,
you'll need to request API credentials from Instapaper.

Usage
=====

.. code-block:: python

    from pyinstapaper.instapaper import Instapaper, Folder

    INSTAPAPER_KEY = 'MY_INSTAPAPER_API_KEY'
    INSTAPAPER_SECRET = 'MY_INSTAPAPER_API_SECRET'
    INSTAPAPER_LOGIN = 'me@example.com'
    INSTAPAPER_PASSWORD = 'p@ssw0rd'

    instapaper = Instapaper(INSTAPAPER_KEY, INSTAPAPER_SECRET)
    instapaper.login(INSTAPAPER_LOGIN, INSTAPAPER_PASSWORD)

    # Get the 10 latest instapaper bookmarks for the given account and do
    # something with the article text
    bookmarks = instapaper.get_bookmarks('starred')
    for bookmark in enumerate(bookmarks):
        do_something(bookmark.get_text())
        bookmark.archive()

    # Create a new folder
    folder = Folder(instapaper, title='cool stuff')
    result = folder.add()

Installation
============

To install PyInstapaper, simply:

.. code-block:: bash

    pip install pyinstapaper

Additional info
===============

* Free software: MIT License
* Documentation: https://pyinstapaper.readthedocs.org.
* Boilerplate courtesy of cookiecutter: https://github.com/audreyr/cookiecutter
* Thanks to `Ryan Galloway`_ for pointing the way to using the Python oauth2
  library for Instapaper's XAuth implementation, though ideally pyinstapaper
  would use `requests-oauthlib`_

.. _Ryan Galloway: https://github.com/rsgalloway/instapaper
.. _requests-oauthlib: https://requests-oauthlib.readthedocs.org/en/latest/
