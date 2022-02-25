import time
import smtplib
import logging

from mailer.lockfile import FileLock, AlreadyLocked, LockTimeout
from socket import error as socket_error

from django.conf import settings
from django.core.mail import send_mail as core_send_mail
from django.core.mail import get_connection

from mailer.models import Message


# when queue is empty, how long to wait (in seconds) before checking again
EMPTY_QUEUE_SLEEP = getattr(settings, "MAILER_EMPTY_QUEUE_SLEEP", 30)

# lock timeout value. how long to wait for the lock to become available.
# default behavior is to never wait for the lock to be available.
LOCK_WAIT_TIMEOUT = getattr(settings, "MAILER_LOCK_WAIT_TIMEOUT", -1)

EMAIL_LOCK_FILE = getattr(settings, "MAILER_LOCK_FILE", "mailer_send_mail")

#maximum mails count wich could be send per one 'send_all' execution
MAXIMUM_MAILS_PER_COMMAND = getattr(settings, "MAILER_MAXIMUM_EMAILS_PER_COMMAND", -1)

ALTERNATIVE_EMAIL_HOST_CONFIG = getattr(settings, 'ALTERNATIVE_EMAIL_HOST_CONFIG', {})


def prioritize(max_mails):
    """
    Return the messages in the queue in the order they should be sent.
    """
    qs = Message.objects.pending()
    if max_mails > 0:
        return qs[:max_mails]
    return qs


def init_connections():
    EMAIL_BACKEND = getattr(settings, "MAILER_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    connections = {
        'default': get_connection(backend=EMAIL_BACKEND)
    }
    for key, config in ALTERNATIVE_EMAIL_HOST_CONFIG.items():
        connections[key] = get_connection(
            backend=EMAIL_BACKEND,
            host=config['HOST'],
            port=config.get('PORT', None),
            username=config.get('USERNAME', ''),
            password=config.get('PASSWORD', ''),
            use_tls=config.get('USE_TLS', False),
            use_ssl=config.get('USE_SSL', False)
        )
    return connections

def send_all():
    """
    Send all eligible messages in the queue.
    """
    # The actual backend to use for sending, defaulting to the Django default.
    # To make testing easier this is not stored at module level.
    EMAIL_BACKEND = getattr(settings, "MAILER_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    
    lock = FileLock(EMAIL_LOCK_FILE)
    
    logging.debug("acquiring lock...")
    try:
        lock.acquire(LOCK_WAIT_TIMEOUT)
    except AlreadyLocked:
        logging.debug("lock already in place. quitting.")
        return
    except LockTimeout:
        logging.debug("waiting for the lock timed out. quitting.")
        return
    logging.debug("acquired.")
    
    start_time = time.time()

    deferred = 0
    sent = 0

    connections = init_connections()
    connections_recipient_domain_mapper = {}
    for key, config in ALTERNATIVE_EMAIL_HOST_CONFIG.items():
        for domain in config.get('DOMAINS', []):
            connections_recipient_domain_mapper[domain] = key
    
    try:
        for message in prioritize(MAXIMUM_MAILS_PER_COMMAND):
            try:
                logging.info("sending message [%s] '%s' to %s" % (message.id, message.subject, message.recipients))
                email = message.email

                connection_key = 'default'
                if len(email.recipients()) == 1 and connections_recipient_domain_mapper:
                    recipient = email.recipients()[0].strip().lower()
                    for domain, key in connections_recipient_domain_mapper.items():
                        if recipient.endswith(domain):
                            connection_key = key
                            break

                email.connection = connections.get(connection_key, connections['default'])
                email.send()
                message.set_sent()
                sent += 1
            except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused,
                    smtplib.SMTPAuthenticationError) as err:
                message.defer()
                logging.info("message deferred due to failure: %s" % err)
                deferred += 1
                # Get new connection, it case the connection itself has an error.
                connections = init_connections()
    finally:
        logging.debug("releasing lock...")
        lock.release()
        logging.debug("released.")
    
    logging.info("")
    logging.info("%s sent; %s deferred;" % (sent, deferred))
    logging.info("done in %.2f seconds" % (time.time() - start_time))


def send_loop():
    """
    Loop indefinitely, checking queue at intervals of EMPTY_QUEUE_SLEEP and
    sending messages if any are on queue.
    """
    
    while True:
        while not Message.objects.all():
            logging.debug("sleeping for %s seconds before checking queue again" % EMPTY_QUEUE_SLEEP)
            time.sleep(EMPTY_QUEUE_SLEEP)
        send_all()
