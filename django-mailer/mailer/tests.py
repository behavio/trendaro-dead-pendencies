from django.test import TestCase

from mailer.models import Message, STATUS_PENDING, STATUS_SENT, STATUS_DEFERRED
from mailer.engine import send_all, prioritize

import smtplib

sent_messages = []

class TestMailerEmailBackend(object):
    def __init__(self, **kwargs):
        global sent_messages
        sent_messages = []

    def open(self):
        pass

    def close(self):
        pass

    def send_messages(self, email_messages):
        global sent_messages
        sent_messages.extend(email_messages)


class FailingMailerEmailBackend(TestMailerEmailBackend):
    def send_messages(self, email_messages):
        raise smtplib.SMTPSenderRefused(1, "foo", "foo@foo.com")


class TestBackend(TestCase):

    def test_save_to_db(self):
        """
        Test that using send_mail creates a Message object in DB instead, when EMAIL_BACKEND is set.
        """
        from django.core.mail import send_mail
        self.assertEqual(Message.objects.count(), 0)
        with self.settings(EMAIL_BACKEND="mailer.backend.DbBackend"):
            send_mail("Subject", "Body", "sender@example.com", ["recipient@example.com"])
            self.assertEqual(Message.objects.count(), 1)


class TestSending(TestCase):
    def test_mailer_email_backend(self):
        """
        Test that calling "manage.py send_mail" actually sends mail using the specified MAILER_EMAIL_BACKEND
        """
        global sent_messages
        from mailer import send_mail
        with self.settings(MAILER_EMAIL_BACKEND="mailer.tests.TestMailerEmailBackend"):
            send_mail("Subject", "Body", "sender@example.com", ["recipient@example.com"], priority="medium")
            self.assertEqual(Message.objects.count(), 1)
            msg_obj = Message.objects.all()[0]
            self.assertEqual(msg_obj.status, STATUS_PENDING)
            self.assertEqual(msg_obj.priority, 2)
            self.assertEqual(len(sent_messages), 0)
            from mailer.engine import send_all
            send_all()
            self.assertEqual(len(sent_messages), 1)
            self.assertEqual(Message.objects.count(), 1)
            msg_obj = Message.objects.all()[0]
            self.assertEqual(msg_obj.status, STATUS_SENT)
            self.assertEqual(msg_obj.priority, 2)

    def test_retry_deferred(self):
        global sent_messages
        from mailer import send_mail
        with self.settings(MAILER_EMAIL_BACKEND="mailer.tests.FailingMailerEmailBackend"):
            send_mail("Subject", "Body", "sender@example.com", ["recipient@example.com"], priority="high")
            send_all()
            self.assertEqual(Message.objects.count(), 1)
            self.assertEqual(Message.objects.deferred().count(), 1)
            msg_obj = Message.objects.all()[0]
            self.assertEqual(msg_obj.status, STATUS_DEFERRED)
            self.assertEqual(msg_obj.priority, 1)

        with self.settings(MAILER_EMAIL_BACKEND="mailer.tests.TestMailerEmailBackend"):
            send_all()
            self.assertEqual(len(sent_messages), 0)
            # Should not have sent the deferred ones
            self.assertEqual(Message.objects.count(), 1)

            # Now mark them for retrying
            self.assertEqual(Message.objects.retry_deferred(), 1)
            msg_obj = Message.objects.all()[0]
            self.assertEqual(msg_obj.status, STATUS_PENDING)
            self.assertEqual(msg_obj.priority, 1)
            send_all()
            self.assertEqual(len(sent_messages), 1)
            self.assertEqual(Message.objects.count(), 1)
            msg_obj = Message.objects.all()[0]
            self.assertEqual(msg_obj.status, STATUS_SENT)
            self.assertEqual(msg_obj.priority, 1)


class TestCreatingModel(TestCase):
    def test_mailer_subject_and_recipients(self):
        global sent_messages
        from mailer import send_mail
        with self.settings(MAILER_EMAIL_BACKEND="mailer.tests.TestMailerEmailBackend"):
            send_mail("Subject email xxx", "Body", "sender@example.com", ["recipient@example.com", "second@email.com"])
            self.assertEqual(Message.objects.count(), 1)
            self.assertEqual(len(sent_messages), 0)
            msg_obj = Message.objects.all()[0]
            self.assertEqual(msg_obj.recipients, "recipient@example.com, second@email.com")
            self.assertEqual(msg_obj.to_addresses, ["recipient@example.com", "second@email.com"])
            self.assertEqual(msg_obj.subject, "Subject email xxx")

    def test_mailer_priority(self):
        global sent_messages
        from mailer import send_mail
        with self.settings(MAILER_EMAIL_BACKEND="mailer.tests.TestMailerEmailBackend"):
            send_mail("Medium email", "Body", "sender@example.com", ["recipient@example.com",], priority="medium")
            send_mail("Low email", "Body", "sender@example.com", ["recipient@example.com",], priority="low")
            send_mail("High email", "Body", "sender@example.com", ["recipient@example.com",], priority="high")
            self.assertEqual(Message.objects.count(), 3)
            self.assertEqual(len(sent_messages), 0)
            msg_objects = prioritize(2)
            self.assertEqual(len(msg_objects), 2)
            msg_objects = prioritize(4)
            self.assertEqual(len(msg_objects), 3)
            msg_objects = prioritize(-1)
            self.assertEqual(len(msg_objects), 3)
            self.assertEqual(msg_objects[0].subject, "High email")
            self.assertEqual(msg_objects[1].subject, "Medium email")
            self.assertEqual(msg_objects[2].subject, "Low email")

            msg_objects[1].status = STATUS_SENT
            msg_objects[1].save()
            msg_objects[2].status = STATUS_DEFERRED
            msg_objects[2].save()
            msg_objects = prioritize(-1)
            self.assertEqual(len(msg_objects), 1)
            self.assertEqual(msg_objects[0].subject, "High email")


