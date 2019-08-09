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

TEST_EMAIL = 'oscar.smoscar+ncbctest@gmail.com'
CC_TEST_EMAIL = 'fj40.kev+ncbcCCtest@gmail.com'
BCC_TEST_EMAIL = 'fj40.kev+ncbcBCCtest@gmail.com'

class Email:

    def __init__(self, login, test_mode=False):
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

        self.test_mode = test_mode
        logger.info(f'Email test mode: {test_mode}')



    def send_message(self, message, rcpt=''):
        """
        Sned email via SMTP
        :param message: message object to send
        :return:
        """
        logger.info('Attempting to send email from {}, to {}'.format(message['From'], message['To']))
        print('rcpt', rcpt)

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
            message['to'] = to if not self.test_mode else TEST_EMAIL
        if cc:
            message['cc'] = cc if not self.test_mode else TEST_EMAIL
        message['from'] = sender
        message['subject'] = subject
        print(message)
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
            message['to'] = to if not self.test_mode else TEST_EMAIL
        if cc:
            message['cc'] = cc if not self.test_mode else TEST_EMAIL
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
            message['to'] = to if not self.test_mode else TEST_EMAIL
        if cc:
            message['cc'] = cc if not self.test_mode else TEST_EMAIL

        message['from'] = sender
        message['subject'] = subject

        logger.info('Sending message to {}'.format(message['to']))
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

    to = 'oscar.smoscar+ncbctest@gmail.com'
    bcc = 'kthorngr@cisco.com'
    """
    message = e.create_message(sender='NC Brewers Cup <kevin.thorngren@gmail.com>',
                               to=to,
                               subject='test of create_message',
                               message_text='testing number 3'
                               )
    """
    brewer = 'chris@glass-jug.com'

    msg = 'Hi {},\n'.format('Chris')
    msg += '\n'
    msg += 'The NC Craft Brewers Guild and I would like to thank you for your entries.  '
    msg += 'Attached you will find your required entry labels and zero dollar invoice.  '
    msg += 'The Entry ID is pre-filled on the label.  Please verify the information on the labels.  '
    msg += 'Each entry will be judged against the Category and Subcategory on the label.  '
    msg += 'You may leave any branded labels on the submitted containers, as the judged samples '
    msg += 'are poured in the cellar, and therefore never seen by the judges.  \n'
    msg += '\n'
    msg += 'Please fill in the quantities and include the zero dollar invoice with your entries '
    msg += 'when they are dropped of at Pro Refrigeration.  Please let Lisa (operations@ncbeer.org) and I know '
    msg += 'if you have any questions or issues.\n'
    msg += '\n'
    msg += 'Drop off info:\n'
    msg += 'August 15th and 16th, 2019 (Thursday + Friday)\n'
    msg += '9am - 5pm\n'
    msg += 'Pro Refrigeration, Inc.\n'
    msg += '319 Farmington Road\n'
    msg += 'Mocksville, NC 27028\n'
    msg += '\n'
    msg += 'Thanks,\nLisa and Kevin\n\n'
    msg += 'Lisa Parker\n'
    msg += 'NC Brewers Cup Superintendent\n'
    msg += 'NCCBG Operations Manager\n'
    msg += 'e. operations@ncbeer.org\n'
    msg += 'c. 919.951.8588\n\n'

    msg += 'Kevin Thorngren\n'
    msg += 'NC Brewers Cup Manager\n'
    msg += 'e. kevin.thorngren@gmail.com\n'
    msg += 'c. 919.418.2350\n'

    message = e.create_message_with_attachment(sender='NC Brewers Cup <kevin.thorngren@gmail.com>',
                                               to=to,
                                               #bcc=bcc,
                                               subject='NC Brewers Cup Entry Labels34',
                                               message_text=msg,
                                               file_dir='files/',
                                               #filename='ncbg-logo.png'
                                               filename=['{}_entry_labels.pdf'.format(brewer),
                                                                        '{}_invoice.pdf'.format(brewer)]
                                               )


    #e.send_message(message, rcpt=[to if not e.test_mode else TEST_EMAIL] + [bcc if not e.test_mode else BCC_TEST_EMAIL])
    e.send_message(message, rcpt=[to])