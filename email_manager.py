import os
import re
from jinja2 import Environment, FileSystemLoader

from email_sender import EmailSender, MockSender
from program_args import get_args

class EmailManager:
    EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def __init__(self, is_local, email_config):
        template_loader = FileSystemLoader(searchpath= os.path.join(os.path.dirname(__file__),'email_templates'))
        self.__template_env = Environment(loader=template_loader)
        self.__email_sender = MockSender() if is_local else EmailSender(email_config['sender_email'], email_config['password'])
        self.__recipients = self.__get_input_emails(email_config.get('recipients', []))

    def create_and_send_email(self, template_name, **template_args):
        template = self.__template_env.get_template(f'{template_name}.html')
        body = template.render(template_args)
        subject = template_name.replace('_', ' ').title()
        self.__email_sender.send_email(self.__recipients, body, subject)

    @staticmethod
    def __get_input_emails(input_emails):
        validated_email_recipients = []
        for pos in range(0, len(input_emails)):
            if re.match(EmailManager.EMAIL_REGEX, input_emails[pos]):
                validated_email_recipients.append(input_emails[pos])

        if validated_email_recipients:
            print('Email Recipients:')
            print(validated_email_recipients)
        return validated_email_recipients