#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

# requirements = ['Click>=6.0', ]
requirements = [
    'future',
    'httplib2>=0.9',
    'lxml>=3.4,<=4',
    'oauth2>=1.9,<2',
    'requests>=2.7,<3',
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Matt Dorn",
    author_email='matt.dorn@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="PyInstapaper is a Python wrapper for the full Instapaper API.",
    entry_points={
        # 'console_scripts': [
        #     'pyinstapaper=pyinstapaper.cli:main',
        # ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pyinstapaper',
    name='pyinstapaper',
    packages=find_packages(include=['pyinstapaper']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/mdorn/pyinstapaper',
    version='0.2.2',
    zip_safe=False,
)
