from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    EMAIL_DEFAULT_FROM_EMAIL = settings.EMAIL_DEFAULT_FROM_EMAIL
except:
    raise ImproperlyConfigured('email_templates needs EMAIL_DEFAULT_FROM_EMAIL set in settings.py')

try:
    EMAIL_DEFAULT_PRIORITY = settings.EMAIL_DEFAULT_PRIORITY
except:
    raise ImproperlyConfigured('email_templates needs EMAIL_DEFAULT_PRIORITY set in settings.py')

try:
    if hasattr(settings, 'MAILER_TEMPLATE_MODEL'):
        app_name, class_name = settings.MAILER_TEMPLATE_MODEL.split('.')
        MAILER_TEMPLATE_MODEL = (app_name, class_name)
    else:
        MAILER_TEMPLATE_MODEL = None
except:
    raise ImproperlyConfigured('MAILER_TEMPLATE_MODEL in settings.py is not valid. Should be "app_name.class_name".')
