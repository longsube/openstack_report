import config
from email.mime import application
from email.mime import multipart
from email.mime import text as tx
from email.utils import formatdate
from os.path import basename
import smtplib


def send_mail(send_from=None, password=None, send_to=None,
              path_file=None, server=None):
    """This function is to send a notify email to Admin.
    :param send_from: Email of dispatcher.
    :param password: Password of dispatcher.
    :param send_to: Email of receiver.
    :param path_file: File attachment.
    :param server: Email server. If no input then gmail is a default server.
    Form server: ip_server:port_server
    :return:
    """
    # Set default options
    subject = "Report OpenStack status"
    text = "Dear Admin \n," \
           "I would like to send an email to report the status of Openstack"

    hostname, port = server.split(':')
    msg = multipart.MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(tx.MIMEText(text))

    with open(path_file, "rb") as fil:
        part = application.MIMEApplication(fil.read(), Name=basename(path_file))
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(path_file)
        msg.attach(part)

    smtp = smtplib.SMTP(host=hostname, port=port)
    smtp.starttls()
    smtp.login(user=send_from, password=password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
