from celery import shared_task



@shared_task
def send_email_notification(html_template, subject, email, context):
    html_message = render_to_string(html_template, context=context)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    message = EmailMessage(subject, html_message, email_from, recipient_list)
    message.content_subtype = 'html'
    message.send()

    return None

