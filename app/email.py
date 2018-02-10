from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    """
    Send an email to user asynchronously
    :param to:          an email of the recipient
    :param subject:     a subject of the message
    :param template:    a name of email template file without an extension
                        (e.g. 'confirmation' for 'confirmation.html' and 'confirmation.txt')
    :return:            thread
    """
    app = current_app._get_current_object()
    msg = Message(app.config['YURAIST_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['YURAIST_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=(app, msg))
    thr.start()
    return thr
