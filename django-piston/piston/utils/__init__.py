from __future__ import unicode_literals

import re

import six

from collections import OrderedDict

from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import RelatedField
from django.template.defaultfilters import lower
from django.db import models
from django.utils import six
from django.utils.encoding import force_text

from copy import deepcopy


class rc_factory(object):
    """
    Status codes.
    """
    CODES = dict(
        ALL_OK=({'success': _('OK')}, 200),
        CREATED=({'success': _('The record was created')}, 201),
        DELETED=('', 204),  # 204 says "Don't send a body!"
        BAD_REQUEST=({'error': _('Bad Request')}, 400),
        FORBIDDEN=({'error':_('Forbidden')}, 403),
        NOT_FOUND=({'error':_('Not Found')}, 404),
        METHOD_NOT_ALLOWED=({'error': _('Method Not Allowed')}, 405),
        DUPLICATE_ENTRY=({'error': _('Conflict/Duplicate')}, 409),
        NOT_HERE=({'error': _('Gone')}, 410),
        UNSUPPORTED_MEDIA_TYPE=({'error': _('Unsupported Media Type')}, 415),
        INTERNAL_ERROR=({'error': _('Internal server error')}, 500),
        NOT_IMPLEMENTED=({'error': _('Not implemented')}, 501),
        THROTTLED=({'error': _('The resource was throttled')}, 503)
    )

    def __getattr__(self, attr):
        """
        Returns a fresh `HttpResponse` when getting
        an "attribute". This is backwards compatible
        with 0.2, which is important.
        """
        try:
            (r, c) = self.CODES.get(attr)
        except TypeError:
            raise AttributeError(attr)

        class HttpResponseWrapper(HttpResponse):
            """
            Wrap HttpResponse and make sure that the internal_base_content_is_iter
            flag is updated when the _set_content method (via the content
            property) is called
            """
            def _set_content(self, content):
                """
                type of the value parameter. This logic is in the construtor
                for HttpResponse, but doesn't get repeated when setting
                HttpResponse.content although this bug report (feature request)
                suggests that it should: http://code.djangoproject.com/ticket/9403
                """
                if not isinstance(content, six.string_types) and hasattr(content, '__iter__'):
                    self._container = {'messages': content}
                    self._base_content_is_iter = True
                else:
                    self._container = [content]
                    self._base_content_is_iter = False

            content = property(HttpResponse.content.getter, _set_content)

        return HttpResponseWrapper(r, content_type='text/plain', status=c)

rc = rc_factory()


def coerce_put_post(request):
    """
    Django doesn't particularly understand REST.
    In case we send data over PUT, Django won't
    actually look at the data and load it. We need
    to twist its arm here.

    The try/except abominiation here is due to a bug
    in mod_python. This should fix it.
    """
    if request.method == "PUT":
        # Bug fix: if _load_post_and_files has already been called, for
        # example by middleware accessing request.POST, the below code to
        # pretend the request is a POST instead of a PUT will be too late
        # to make a difference. Also calling _load_post_and_files will result
        # in the following exception:
        #   AttributeError: You cannot set the upload handlers after the upload has been processed.
        # The fix is to check for the presence of the _post field which is set
        # the first time _load_post_and_files is called (both by wsgi.py and
        # modpython.py). If it's set, the request has to be 'reset' to redo
        # the query value parsing in POST mode.
        if hasattr(request, '_post'):
            del request._post
            del request._files

        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'

        request.PUT = request.POST


def model_default_rest_fields(model):
    rest_fields = []
    for field in model._meta.fields:
        if isinstance(field, RelatedField):
            rest_fields.append((field.name, ('id', '_obj_name', '_rest_links')))
        else:
            rest_fields.append(field.name)
    return rest_fields


def flat_list(list_obj):
    flat_list_obj = []
    for val in list_obj:
        if isinstance(val, (list, tuple)):
            flat_list_obj.append(val[0])
        else:
            flat_list_obj.append(val)
    return flat_list_obj


class JsonObj(dict):

    def __setattr__(self, name, value):
        self[name] = value


def model_resources_to_dict():
    from piston.resource import resource_tracker

    model_resources = {}
    for resource in resource_tracker:
        if hasattr(resource, 'model') and issubclass(resource.model, models.Model):
            model = resource.model
            model_label = lower('%s.%s' % (model._meta.app_label, model._meta.object_name))
            model_resources[model_label] = resource
    return model_resources


def set_rest_context_to_request(request, mapping):
    context = {}
    for key, (header_key, queryset_key) in mapping.items():
        val = request.GET.get(queryset_key, request.META.get(header_key))
        if val:
            context[key] = val
    request._rest_context = context


def is_match(regex, text):
    pattern = re.compile(regex)
    return pattern.search(text) is not None


def get_model_from_descriptor(model, field_name):
    if model:
        model_descriptor = getattr(model, field_name, None)
        if model_descriptor and hasattr(model_descriptor, 'related'):
            return model_descriptor.related.model
        elif model_descriptor and hasattr(model_descriptor, 'field'):
            return model_descriptor.field.rel.to


def split_fields(fields_string):

    brackets = 0

    field = ''
    for char in fields_string:
        if char == ',' and not brackets:
            field = field.strip()
            if field:
                yield field
            field = ''
            continue

        if char == '(':
            brackets += 1

        if char == ')':
            brackets -= 1

        field += char

    field = field.strip()
    if field:
        yield field


class RESTField(object):

    def __init__(self, name, subfieldset=None):
        assert isinstance(name, six.string_types)
        assert subfieldset is None or isinstance(subfieldset, RESTFieldset)

        self.name = name
        self.subfieldset = subfieldset or RESTFieldset()

    def __deepcopy__(self, memo):
        return self.__class__(self.name, deepcopy(self.subfieldset))

    def join(self, rest_field):
        self.subfieldset = self.subfieldset.join(rest_field.subfieldset)
        return self

    def intersection(self, rest_field):
        self.subfieldset = self.subfieldset.intersection(rest_field.subfieldset)
        return self

    def __str__(self):
        if self.subfieldset:
            return '%s(%s)' % (self.name, self.subfieldset)
        return '%s' % self.name


class RESTFieldset(object):

    @classmethod
    def create_from_string(cls, fields_string):
        fields = []
        for field in split_fields(fields_string):
            if is_match('^[^\(\)]+\(.+\)$', field):
                field_name, subfields_string = field[:len(field) - 1].split('(', 1)
                if '__' in field_name:
                    field_name, subfields_string = field.split('__', 1)

                subfieldset = RFS.create_from_string(subfields_string)
            else:
                field_name = field
                subfieldset = None
                if '__' in field_name:
                    field_name, subfields_string = field.split('__', 1)
                    subfieldset = RFS.create_from_string(subfields_string)

            fields.append(RESTField(field_name, subfieldset))
        return RESTFieldset(*fields)

    @classmethod
    def create_from_list(cls, fields_list):
        if isinstance(fields_list, RESTFieldset):
            return deepcopy(fields_list)

        fields = []
        for field in fields_list:
            if isinstance(field, (list, tuple)):
                field_name, subfield_list = field

                fields.append(RESTField(field_name, cls.create_from_list(subfield_list)))
            else:
                fields.append(field)

        return RESTFieldset(*fields)

    def __init__(self, *fields):
        self.fields_map = OrderedDict()
        for field in fields:
            if not isinstance(field, RESTField):
                field = RESTField(field)
            self.append(field)

    @property
    def fields(self):
        return self.fields_map.values()

    def join(self, rest_fieldset):
        assert isinstance(rest_fieldset, RESTFieldset)

        for rf in rest_fieldset.fields:
            if rf.name not in self.fields_map:
                self.fields_map[rf.name] = deepcopy(rf)
            else:
                self.fields_map[rf.name] = self.fields_map[rf.name].join(rf)

        return self

    def intersection(self, rest_fieldset):
        assert isinstance(rest_fieldset, RESTFieldset)

        fields_map = self.fields_map
        self.fields_map = OrderedDict()

        for name, rf in fields_map.items():
            if name in rest_fieldset.fields_map:
                self.append(rf.intersection(rest_fieldset.fields_map[name]))

        return self

    def extend_fields_fieldsets(self, rest_fieldset):
        assert isinstance(rest_fieldset, RESTFieldset)

        for rf in rest_fieldset.fields:
            if rf.subfieldset and rf.name in self.fields_map and not self.fields_map[rf.name].subfieldset:
                self.fields_map[rf.name].join(rf)

        return self

    def subtract(self, rest_fieldset):
        if isinstance(rest_fieldset, (list, tuple, set)):
            rest_fieldset = RFS(*rest_fieldset)

        assert isinstance(rest_fieldset, RESTFieldset)

        fields_map = self.fields_map
        self.fields_map = OrderedDict()

        for name, rf in fields_map.items():
            if name not in rest_fieldset.fields_map:
                self.fields_map[name] = rf

        return self

    def __deepcopy__(self, memo):
        return self.__class__(*map(deepcopy, self.fields))

    def __str__(self):
        return ','.join(map(force_text, self.fields))

    def __add__(self, rest_fieldset):
        a_rfs = deepcopy(self)
        return a_rfs.join(rest_fieldset)

    def __sub__(self, rest_fieldset):
        if isinstance(rest_fieldset, (list, tuple, set)):
            rest_fieldset = RFS(*rest_fieldset)

        assert isinstance(rest_fieldset, RESTFieldset)

        values = []
        for rf in self.fields:
            if rf.name not in rest_fieldset.fields_map:
                values.append(deepcopy(rf))

        return self.__class__(*values)

    def __bool__(self):
        return bool(self.fields_map)
    __nonzero__ = __bool__

    def get(self, key):
        return self.fields_map.get(key)

    def append(self, field):
        if isinstance(field, RESTField):
            rest_field = field
        else:
            rest_field = RESTField(field)

        if rest_field.name in self.fields_map:
            rest_field = rest_field.join(self.fields_map[rest_field.name])

        self.fields_map[rest_field.name] = rest_field
        return self

    def update(self, rest_fieldset):
        if isinstance(rest_fieldset, (list, tuple, set)):
            rest_fieldset = RFS(*rest_fieldset)

        assert isinstance(rest_fieldset, RESTFieldset)

        for rf in rest_fieldset.fields:
            rf = deepcopy(rf)
            if rf.name not in self.fields_map:
                self.fields_map[rf.name] = rf
            else:
                self.fields_map[rf.name] = self.fields_map[rf.name].join(rf)

        return self

    def flat(self):
        return set(self.fields_map.keys())


RF = RESTField
RFS = RESTFieldset
rfs = RFS.create_from_list
