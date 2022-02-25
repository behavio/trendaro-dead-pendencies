from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class User(models.Model):

    email = models.EmailField(verbose_name=_('email'), null=False, blank=False, unique=True)
    contract = models.FileField(_('file'), null=True, blank=True, upload_to='documents/')

    def __str__(self):
        return 'user: %s' % self.email


@python_2_unicode_compatible
class Issue(models.Model):

    name = models.CharField(verbose_name=_('name'), max_length=100, null=False, blank=False)
    watched_by = models.ManyToManyField('app.User', verbose_name=_('watched by'), blank=True,
                                        related_name='watched_issues')
    created_by = models.ForeignKey('app.User', verbose_name=_('created by'), null=False, blank=False,
                                   related_name='created_issues')
    solver = models.OneToOneField('app.User', verbose_name=_('solver'), null=True, blank=True,
                                  related_name='solving_issue')
    leader = models.OneToOneField('app.User', verbose_name=_('leader'), null=False, blank=False,
                                  related_name='leading_issue')

    def __str__(self):
        return 'issue: %s' % self.name
