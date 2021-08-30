from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives


def send_mail(subject, name, body,
              send_to='contact@masys.co.uk',
              send_from='contact@masys.co.uk',
              reply_to='contact@masys.co.uk'):

    html_content = render_to_string('mail/email.html', {'name': name,
                                                       'body': body})
    text_content = strip_tags(html_content)

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, send_from, [send_to], reply_to=[reply_to])
    msg.attach_alternative(html_content, "text/html")

    msg.send()

    return