import formalchemy
from formalchemy import helpers as h
from formalchemy.validators import required
from sqlalchemy.util import OrderedDict
from pylons.i18n import _, gettext

from ckan.lib.helpers import literal
from ckan.forms import common
from ckan.forms import package as package
from ckanext.datano import schema_datano
from ckan.lib import field_types

__all__ = ['get_datano_fieldset']


class GeoCoverageExtraField(common.ConfiguredField):
    def get_configured(self):
        return self.GeoCoverageField(self.name).with_renderer(self.GeoCoverageRenderer)

    class GeoCoverageField(formalchemy.Field):
        def sync(self):
            if not self.is_readonly():
                pkg = self.model
                form_regions = self._deserialize() or []
                regions_db = schema_datano.GeoCoverageType.get_instance().form_to_db(form_regions)
                pkg.extras[self.name] = regions_db

    class GeoCoverageRenderer(formalchemy.fields.FieldRenderer):
        def _get_value(self):
            form_regions = self.value # params
            if not form_regions:
                extras = self.field.parent.model.extras # db
                db_regions = extras.get(self.field.name, []) or []
                form_regions = schema_datano.GeoCoverageType.get_instance().db_to_form(db_regions)
            return form_regions

        def render(self, **kwargs):
            value = self._get_value()
            kwargs['size'] = '40'
            html = u''
            for i, region in enumerate(schema_datano.GeoCoverageType.get_instance().regions):
                region_str, region_munged = region
                id = '%s-%s' % (self.name, region_munged)
                checked = region_munged in value
                cb = literal(h.check_box(id, True, checked=checked, **kwargs))
                html += literal('<label for="%s">%s %s</label>') % (id, cb, region_str)
            return html

        def render_readonly(self, **kwargs):
            munged_regions = self._get_value()
            printable_region_names = schema_datano.GeoCoverageType.get_instance().munged_regions_to_printable_region_names(munged_regions)
            return common.field_readonly_renderer(self.field.key, printable_region_names)

        def _serialized_value(self):
            # interpret params like this:
            # 'Package--geographic_coverage-wales', u'True'
            # return list of covered regions
            covered_regions = []
            for region in schema_datano.GeoCoverageType.get_instance().regions_munged:
                utfname = (self.name + '-' + region).encode("utf-8")
                if self.params.get(utfname, u'') == u'True':
                    covered_regions.append(region)
            return covered_regions

        def deserialize(self):
            return self._serialized_value()

class SuggestTagRenderer(common.TagField.TagEditRenderer):
    def render(self, **kwargs):
        fs = self.field.parent
        pkg_dict = {}
        for field_name, field in fs.render_fields.items():
            pkg_dict[field_name] = field.renderer.value
        tag_suggestions = schema_datano.suggest_tags(pkg_dict)
        html = literal("<div>Suggestions (preview refreshes): %s</div>") % ' '.join(tag_suggestions)
        html += common.TagField.TagEditRenderer.render(self, **kwargs)
        return html
        

# Setup the fieldset
def build_package_no_form(is_admin=False, user_editable_groups=None, **kwargs):
    # Restrict fields
    restrict = str(kwargs.get('restrict', False)).lower() not in \
               ('0', 'no', 'false', 0, False)

    builder = package.build_package_form(user_editable_groups=user_editable_groups)

    # Extra fields
    builder.add_field(common.TextExtraField('external_reference'))
    builder.add_field(common.DateExtraField('date_released'))
    builder.add_field(common.DateExtraField('date_updated'))
    builder.add_field(common.TextExtraField('update_frequency'))
    builder.add_field(common.SuggestedTextExtraField('geographic_granularity', options=schema_datano.geographic_granularity_options))
    builder.add_field(GeoCoverageExtraField('geographic_coverage'))
    builder.add_field(common.SuggestedTextExtraField('temporal_granularity', options=schema_datano.temporal_granularity_options))
    builder.add_field(common.DateRangeExtraField('temporal_coverage'))
    builder.add_field(common.SuggestedTextExtraField('categories', options=schema_datano.category_options))
    builder.add_field(common.CheckboxExtraField('national_statistic'))
    builder.add_field(common.TextExtraField('precision'))
    builder.add_field(common.SuggestedTextExtraField('department', options=schema_datano.government_depts))
    builder.add_field(common.TextExtraField('agency'))
    builder.add_field(common.TextExtraField('taxonomy_url'))
    builder.add_field(common.TextExtraField('title_en'))
    builder.add_field(common.TextExtraField('notes_en'))
    builder.add_field(common.TextExtraField('external_rss'))
    builder.add_field(common.TextExtraField('example_data'))


    # Labels and instructions
    builder.set_field_text('national_statistic', _('National Statistic'))
    builder.set_field_text('external_rss', _('External RSS'), instructions=_('Link to the data owner\'s external RSS feed.'))
    builder.set_field_text('title_en', _('Title EN'), instructions=_('Title in English. Translate what you wrote in the previous field to English.'))
    builder.set_field_text('notes_en', _('Notes EN'), instructions=_('Description in English. Translate what you wrote in the previous field to English.'))
    builder.set_field_text('date_released', _('Date released'), instructions=_('Date when data source was made available.'), hints=_('Format: DD/MM/YYYY'))
    builder.set_field_text('update_frequency', _('Update frequency'), instructions=_('How often will the data be updated.'), hints=_('e.g. annually, monthly'))
    builder.set_field_text('geographic_coverage', _('Geographic coverage'), instructions=_('Select geographic coverage for your data set.'))
    builder.set_field_text('temporal_coverage', _('Temporal coverage'), instructions=_('Temporal coverage for the data set.'), hints=_('Format: DD/MM/YYYY'))
    builder.set_field_text('author_email', _('Author email'), instructions=_('Email of the main contact for this data source.'))
    builder.set_field_text('maintainer_email', _('Maintainer email'), instructions=_('Email of a person that can be contacted for questions regarding this data source.'))
    builder.set_field_text('example_data', _('Data package example'), instructions=_('Example preview of the data available in this package.'))


    # Options/settings
    builder.set_field_option('tags', 'with_renderer', SuggestTagRenderer)
    builder.set_field_option('notes_en', 'textarea', {'size':'60x15'})
    builder.set_field_option('title', 'validate', required)
    builder.set_field_option('notes', 'validate', required)
    builder.set_field_option('example_data', 'textarea', {'size':'60x15'})

    
    if restrict:
        for field_name in ('name', 'department', 'national_statistic'):
            builder.set_field_option(field_name, 'readonly', True)

    # Layout
    field_groups = OrderedDict([
        (_('Basic information'), ['title', 'title_en', 'name', 'version',
                                  'notes', 'notes_en', 'tags']),
        (_('Details'), ['date_released', 'update_frequency',
                        'geographic_coverage',
                        'temporal_coverage',
                        'author', 'author_email',
                        'maintainer', 'maintainer_email',
                        'license_id',
                        'url', 'external_rss', 'example_data']),
        (_('Resources'), ['resources']),
        (_('More details'), []),
        ])
    if is_admin:
        field_groups[gettext('More details')].append('state')
    builder.set_displayed_fields(field_groups)
    return builder
    # Strings for i18n
    [_('External reference'),  _('Date released'), _('Date updated'),
     _('Update frequency'), _('Geographic granularity'),
     _('Geographic coverage'), _('Temporal granularity'),
     _('Temporal coverage'), _('Categories'), _('National Statistic'),
     _('Precision'), _('Taxonomy URL'), _('Department'), _('Agency'), 
     _('External RSS'), _('Data package example'),
     ]

def get_datano_fieldset(is_admin=False, user_editable_groups=None, **kwargs):
    return build_package_no_form(is_admin=is_admin, user_editable_groups=user_editable_groups, **kwargs).get_fieldset()
