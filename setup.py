# -*- coding: utf-8 -*-
from setuptools import setup

MY_VERSION = '0.0.1'

setup(
    name='sshconfig',
    version=MY_VERSION,
    description='Lightweight SSH config library',
    author='Søren Atmakuri Davidsen',
    author_email='sorend@cs.svuni.in',
    url='https://github.com/sorend/sshconfig',
    download_url='https://github.com/sorend/sshconfig/tarball/%s' % (MY_VERSION,),
    license='MIT',
    keywords=['ssh', 'config'],
    install_requires=[
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
