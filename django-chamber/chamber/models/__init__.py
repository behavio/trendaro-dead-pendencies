from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.db.models.query_utils import DeferredAttribute
from chamber.exceptions import PersistenceException

def get_deferred_field_names(instance):
    """
    Returns a set containing names of deferred fields for this instance.
    """
    return {
        f.name for f in instance._meta.concrete_fields
        if isinstance(instance.__class__.__dict__.get(f.attname), DeferredAttribute)
    }

def model_to_dict(instance, fields=None, exclude=None):
    """
    The same implementation as django model_to_dict but editable fields are allowed
    """
    # avoid a circular import
    from django.db.models.fields.related import ManyToManyField
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, ManyToManyField):
            # If the object doesn't have a primary key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []
            else:
                # MultipleChoiceWidget needs a list of pks, not object instances.
                data[f.name] = list(f.value_from_object(instance).values_list('pk', flat=True))
        else:
            data[f.name] = f.value_from_object(instance)
    return data


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def initial_values(self):
        return self.__initial

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        fields = [
            field.name
            for field in self._meta.fields
        ]
        # need to use the local alternative to get_deferred_fields
        # because this class uses .name instead of .attname
        return model_to_dict(self, fields=fields, exclude=get_deferred_field_names(self))

class ComparableModelMixin(object):

    def equals(self, obj, comparator):
        """
        Use comparator for evaluating if objects are the same
        """
        return comparator.compare(self, obj)


class Comparator(object):

    def compare(self, a, b):
        """
        Return True if objects are same otherwise False
        """
        raise NotImplementedError


class AuditModel(models.Model):
    created_at = models.DateTimeField(verbose_name=_('created at'), null=False, blank=False, auto_now_add=True)
    changed_at = models.DateTimeField(verbose_name=_('changed at'), null=False, blank=False, auto_now=True)

    class Meta:
        abstract = True


class SmartModel(AuditModel):

    def full_clean(self, *args, **kwargs):
        errors = {}
        for field in self._meta.fields:
            if hasattr(self, 'clean_%s' % field.name):
                try:
                    getattr(self, 'clean_%s' % field.name)()
                except ValidationError as er:
                    errors[field.name] = er.messages

        if errors:
            raise ValidationError(errors)
        super(SmartModel, self).full_clean(*args, **kwargs)

    def pre_save(self, change, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        change = bool(self.pk)
        self.pre_save(change, *args, **kwargs)
        try:
            self.full_clean(exclude=self.get_deferred_fields())
        except ValidationError as er:
            if hasattr(er, 'error_dict'):
                raise PersistenceException(', '.join(
                    ('%s: %s' % (key, ', '.join(map(force_text, val))) for key, val in er.message_dict.items())))
            else:
                raise PersistenceException(', '.join(map(force_text, er.messages)))
        super(SmartModel, self).save(*args, **kwargs)
        self.post_save(change, *args, **kwargs)

    def post_save(self, change, *args, **kwargs):
        pass

    class Meta:
        abstract = True
