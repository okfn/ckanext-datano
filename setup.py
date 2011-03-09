from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-datano',
	version=version,
	description="Customisations for DataNO project",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='',
	author_email='',
	url='http://data.no',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.datano'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
	datano=ckanext.datano:DataNOPlugin

        [ckan.forms]
        datano_package_form = ckanext.datano.package_datano:get_datano_fieldset
	""",
)
