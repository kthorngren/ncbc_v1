"""Send an email message from the user's account.
"""

import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os

from apiclient import errors

from apiclient.discovery import build
from apiclient import errors
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/gmail.send'


class Gmail:

    def __init__(self):
        self.creds = None
        self.service = None
        self.path = 'files/gmail/'

    def get_creds(self):
        store = oauth_file.Storage('{}none.json'.format(self.path))
        creds = store.get()

        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('{}client_secret.json'.format(self.path), SCOPES)
            creds = tools.run_flow(flow, store)

        self.creds = creds

    def get_service(self):
        service = build('gmail', 'v1', http=self.creds.authorize(Http()))

        self.service = service



def SendMessage(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    print ('Message Id: %s' % message['id'])
    return message
  except errors.HttpError as error:
    print ('An error occurred: %s' % error)


def CreateMessage(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_bytes())}


def CreateMessageWithAttachment(sender, to, subject, message_text, file_dir,
                                filename):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.
    file_dir: The directory containing the file to be attached.
    filename: The name of the file to be attached.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEMultipart()
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject

  msg = MIMEText(message_text)
  message.attach(msg)

  path = os.path.join(file_dir, filename)
  content_type, encoding = mimetypes.guess_type(path)

  if content_type is None or encoding is not None:
    content_type = 'application/octet-stream'
  main_type, sub_type = content_type.split('/', 1)
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
  else:
    fp = open(path, 'rb')
    msg = MIMEBase(main_type, sub_type)
    msg.set_payload(fp.read())
    fp.close()

  msg.add_header('Content-Disposition', 'attachment', filename=filename)
  message.attach(msg)

  #print(dir(message))
  return {'raw': base64.urlsafe_b64encode(message.as_bytes())}



if __name__ == '__main__':

    g = Gmail()

    g.get_creds()
    g.get_service()



    m = CreateMessage('kevin.thorngren@gmail.com', 'kevin.thorngren@gmail.com', 'Test 1', 'This is a test')
    #m = CreateMessageWithAttachment('kevin.thorngren@gmail.com', 'kevin.thorngren@gmail.com', 'Test 2', 'This is a test', 'files/', 'kevin.thorngren@gmail.com.pdf')

    m['raw'] = m['raw'].decode('utf-8')
    print(m)

    SendMessage(g.service, 'kevin.thorngren@gmail.com', m)
