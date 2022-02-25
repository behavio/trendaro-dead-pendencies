from __future__ import unicode_literals

from django.template import Context, Template
from django.db.models.loading import get_model

from mailer import send_html_mail
from mailer.email_templates.models import EmailTemplate
from mailer.email_templates import config


class EmailTemplateSender(object):
    default_context_data = {}
    default_from_email = config.EMAIL_DEFAULT_FROM_EMAIL
    default_priority = config.EMAIL_DEFAULT_PRIORITY
    default_auth_user = None
    default_auth_password = None
    default_headers = {}
    default_fail_silently = False
    default_message = ' '
    default_content_object = None
    default_tag = None

    @classmethod
    def send_html_mail_from_email_template(cls, template_name, recipient_list, attachments=None,
                                           cached_template_obj=None, **kwargs):

        for attr_name in ('context_data', 'from_email', 'priority', 'fail_silently', 'auth_user',
                          'auth_password', 'headers', 'message', 'content_object', 'tag'):
            kwargs[attr_name] = kwargs.get(attr_name, getattr(cls, 'default_%s' % attr_name))

        email_template = cls.get_email_template_object(template_name, cached_template_obj)
        context = cls.get_context(kwargs['context_data'], email_template)

        html_template = cls.before_render(email_template)
        html_message = Template(html_template).render(context).encode('utf-8')
        html_message = cls.after_render(html_message)

        kwargs['subject'] = cls.get_subject(email_template, context, kwargs.get('content_object'))
        kwargs['message_html'] = html_message
        kwargs['recipient_list'] = recipient_list
        kwargs['attachments'] = attachments

        del kwargs['context_data']

        return send_html_mail(**kwargs)

    @classmethod
    def get_context(cls, context_data, email_template):
        return Context(context_data)

    @classmethod
    def before_render(cls, email_template, content_object=None):
        return email_template.html_body

    @classmethod
    def after_render(cls, html):
        return html

    @classmethod
    def get_subject(cls, email_template, context, content_object=None):
        return email_template.subject

    @classmethod
    def get_rendered_email_template(cls, template_name=None, template_obj=None, context_data={}):
        context = Context(context_data)
        email_template = cls.get_email_template_object(template_name, template_obj)
        html_template = email_template.html_body
        return cls.after_render(Template(html_template).render(context).encode('utf-8'))

    @classmethod
    def get_email_template_class(cls):
        return get_model(*config.MAILER_TEMPLATE_MODEL) if config.MAILER_TEMPLATE_MODEL else EmailTemplate

    @classmethod
    def get_email_template_object(cls, template_name=None, template_obj=None):
        model = cls.get_email_template_class()
        if isinstance(template_obj, model):
            return template_obj
        else:
            return model.objects.get(slug=template_name)
