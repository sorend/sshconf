# -*- coding: utf-8 -*-
from setuptools import setup

MY_VERSION = '0.0.1'

setup(
    name='sshconf',
    version=MY_VERSION,
    description='Lightweight SSH config library',
    author='Søren A D',
    author_email='sorend@acm.org',
    url='https://github.com/sorend/sshconf',
    download_url='https://github.com/sorend/sshconf/tarball/%s' % MY_VERSION,
    license='MIT',
    keywords=['ssh', 'config'],
    py_modules=['sshconf'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    classifiers=(
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
    )
)
