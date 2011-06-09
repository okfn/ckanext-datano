import os
from logging import getLogger

from pylons import c
from ckan import model
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurer, IPackageController

log = getLogger(__name__)


class DataNOPlugin(SingletonPlugin):
    implements(IConfigurer, inherit=True)
    implements(IPackageController, inherit=True)

    def update_config(self, config):
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        our_public_dir = os.path.join(rootdir, 'ckanext',
                                      'datano', 'theme', 'public')
        template_dir = os.path.join(rootdir, 'ckanext',
                                    'datano', 'theme', 'templates')
        config['extra_public_paths'] = ','.join([our_public_dir,
                config.get('extra_public_paths', '')])
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])
        config['googleanalytics.id'] = ''
        config['ckan.site_title'] = "data.norge.no datakatalog"
        config['ckan.site_logo'] = "http://drupal1.computas.no/ckan/img/fad_logo_ckan.png"
        config['ckan.favicon'] = "http://drupal1.computas.no/ckan/img/favicon.ico"
        config['package_form'] = "datano_package_form"  # XXX change

    def create(self, package):
        # take my first authzgroup
        # and give it the editor role on this package
        user = model.User.by_name(c.user)
        authzgroups = user and user.authorization_groups
        authzgroup = authzgroups and authzgroups[0]
        if authzgroup:
            role = "editor"
            model.add_authorization_group_to_role(authzgroup, role, package)
