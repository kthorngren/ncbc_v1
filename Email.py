import smtplib
import json

from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import mimetypes


import time
from datetime import datetime
import logging

from MySql import Sql
from MySql import local_host


# create logger
import logging
import os



LEVEL = logging.INFO
logger = logging.getLogger(os.path.basename(__file__).split('.')[0] if __name__ == '__main__' else __name__.split('.')[-1])
logger.setLevel(LEVEL)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(LEVEL)

# create formatter
formatter = logging.Formatter('%(asctime)s.%(msecs)03d: %(levelname)s: %(name)s.%(funcName)s(): %(message)s', datefmt='%m-%d-%Y %H:%M:%S')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
# end create logger


class Email:

    def __init__(self, login):
        logger.info('Initiating email client using authentication from {}'.format(login if type(login) == type(' ') else 'Dictionary'))
        if type(login) == type({}):
            self.username = login.get('username', '')
            self.password = login.get('password', '')
        elif type(login) == type(' '):
            with open(login, 'r') as file:
                data = file.read()

            login = json.loads(data)
            self.username = login.get('username', '')
            self.password = login.get('password', '')



    def send_message(self, message, rcpt=''):
        """
        Sned email via SMTP
        :param message: message object to send
        :return:
        """
        logger.info('Attempting to send email from {}, to {}'.format(message['From'], message['To']))
        print(rcpt)
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            #print 'server created'
            server.ehlo()
            #print 'ehlo'
            server.starttls()
            #print 'starttls'
            server.login(self.username, self.password)
            #print 'login'
            server.sendmail(message['From'], rcpt, message.as_bytes())
            #print 'sendmail'
            server.close()
            #print "Successfully sent email"
            logger.info('Message successfully sent')
            return True

        except Exception as e:
            logger.error('Error sending email: {}'.format(str(e)))
        return False


    def create_message(self, sender='', to='', cc='', bcc='', subject='', message_text=''):
        """Create a message for an email.

        Args:
          sender: Email address of the sender.
          to: Email address of the receiver.
          subject: The subject of the email message.
          message_text: The text of the email message.

        Returns:
          message object
        """
        print(sender, to, bcc, cc)
        if to and type(to) == type([]):
            to = ','.join(to)
        if cc and type(cc) == type([]):
            cc = ','.join(cc)
        logger.info('Creating message for sender: {}'.format(sender))
        message = MIMEText(message_text)
        if to:
            message['to'] = to
        if cc:
            message['cc'] = cc
        message['from'] = sender
        message['subject'] = subject


        return message


    def create_html_message(self, sender='', to='', cc='', bcc='', subject='', message_text=''):
        """Create a message for an email.

        Args:
          sender: Email address of the sender.
          to: Email address of the receiver.
          subject: The subject of the email message.
          message_text: The text of the email message.

        Returns:
          message object
        """

        if to and type(to) == type([]):
            to = ','.join(to)
        if cc and type(cc) == type([]):
            cc = ','.join(cc)
        logger.info('Creating HTML message for sender: {}'.format(sender))
        message = MIMEText(message_text, 'html')
        if to:
            message['to'] = to
        if cc:
            message['cc'] = cc
        message['from'] = sender
        message['subject'] = subject
        return message

    def create_message_with_attachment(self, sender='', to='', cc='', bcc='', subject='', message_text='', file_dir='', filename='', content_type=''):
        """Create a message with attachment for an email.

        Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        file_dir: The directory containing the file to be attached.
        filename: The name of the file to be attached. Can be string or list of strings.

        Returns:
        message object
        """
        if to and type(to) == type([]):
            to = ','.join(to)
        if cc and type(cc) == type([]):
            cc = ','.join(cc)
        logger.info('Creating message for sender: {} with file: {}'.format(sender, filename))
        message = MIMEMultipart()
        if to:
            message['to'] = to
        if cc:
            message['cc'] = cc

        message['from'] = sender
        message['subject'] = subject


        if content_type == 'html':
            msg = MIMEText(message_text, 'html')
        else:
            msg = MIMEText(message_text)
        message.attach(msg)


        if type(filename) != type([]):
            filename = [filename]

        for file in filename:
            path = os.path.join(file_dir, file)
            content_type, encoding = mimetypes.guess_type(path)

            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            main_type, sub_type = content_type.split('/', 1)


            try:
                if main_type == 'text':
                    fp = open(path, 'rb')
                    msg = MIMEText(fp.read(), _subtype=sub_type)
                    fp.close()
                elif main_type == 'image':
                    fp = open(path, 'rb')
                    msg = MIMEImage(fp.read(), _subtype=sub_type)
                    fp.close()
                elif main_type == 'audio':
                    fp = open(path, 'rb')
                    msg = MIMEAudio(fp.read(), _subtype=sub_type)
                    fp.close()
                elif main_type == 'application':
                    fp = open(path, 'rb')
                    msg = MIMEApplication(fp.read(), _subtype=sub_type)
                    fp.close()
                else:
                    fp = open(path, 'rb')
                    msg = MIMEBase(main_type, sub_type)
                    msg.set_payload(fp.read())
                    fp.close()
            except Exception as e:
                logger.error('Error attaching files; {}'.format(e))
                return ''

            msg.add_header('Content-Disposition', 'attachment', filename=file)
            message.attach(msg)

        return message




if __name__ == '__main__':

    #e = Email({'username': 'kevin.thorngren@gmail.com', 'password': 'R3alal3)'})
    e = Email('files/kevin.json')

    to = 'kevin.thorngren@gmail.com'
    bcc = 'brewerkev@gmail.com'
    #message = e.create_message('NC Brewers Cup <kevin.thorngren@gmail.com>', 'kevin.thorngren@gmail.com', 'test 3', 'testing number 3')
    message = e.create_message_with_attachment(sender='kevin.thorngren@gmail.com',
                                               to=to,
                                               subject='test 3',
                                               message_text='testing number 3',
                                               file_dir='files/',
                                               filename='phil@turguabrewing.com_entry_labels.pdf'
                                               )

    e.send_message(message, rcpt=[to] + [bcc])