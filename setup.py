# -*- coding: utf-8 -*-
from setuptools import setup, Distribution, find_packages
Distribution().fetch_build_eggs('versiontag')
from versiontag import get_version, cache_git_tag

cache_git_tag()

MY_VERSION = get_version(pypi=True)

Distribution().fetch_build_eggs('pypandoc')
import pypandoc

setup(
    name='sshconf',
    packages=find_packages(),
    version=MY_VERSION,
    description='Lightweight SSH config library',
    long_description=pypandoc.convert_file('README.md', 'rst'),
    author='Søren A D',
    author_email='sorend@acm.org',
    url='https://github.com/sorend/sshconf',
    download_url='https://github.com/sorend/sshconf/tarball/%s' % MY_VERSION,
    license='MIT',
    keywords=['ssh', 'config'],
    py_modules=['sshconf'],
    setup_requires=['pytest-runner', 'pytest-cov', 'wheel', 'pypandoc'],
    tests_require=['pytest'],
    classifiers=(
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
    )
)
