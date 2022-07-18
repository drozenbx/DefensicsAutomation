import smtplib
import GlobalVariables
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from email.utils import COMMASPACE


email_subject = 'Defensics Automation - '
email_from = 'Defensics-' + GlobalVariables.LP_machine + '@intel.com'
email_to = ''
COMMASPACE = ', '


def create_message(subject_suffix):
    message = MIMEMultipart('alternative')
    message['Subject'] = email_subject + subject_suffix
    message['From'] = email_from
    message['To'] = COMMASPACE.join(email_to)
    return message


def set_body(message, html):
    message.attach(MIMEText(html, 'html'))


def send_email(message, recipients_list):
    print ('11111111111111111')
    smtp_obj = smtplib.SMTP('localhost')
    print ('22222222222222222222222')

    # sending for all recipients
    for owner in recipients_list:
        print ("3333333333333333333")
        print (owner)
        print (email_from)
        print (message.as_string())
        print len(message.as_string())
        smtp_obj.sendmail(email_from, owner, message.as_string())
        print ("44444444444444444444")
        print (owner)
        print ('5555555555555555555')


