import os
import re
from typing import Any, Dict, List, Union, cast
from jinja2 import Environment, FileSystemLoader
from jinja2.environment import Template

from email_sender import EmailSender, MockSender

class EmailManager:
    EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def __init__(self, is_local: bool, email_config: Dict[str, Union[str, List[str]]]) -> None:
        template_loader: FileSystemLoader = FileSystemLoader(searchpath= os.path.join(os.path.dirname(__file__),'email_templates'))
        self._template_env: Environment = Environment(loader=template_loader)
        self._email_sender: EmailSender = MockSender() if is_local else EmailSender(email_config['sender_email'], email_config['password'])
        self._recipients: List[str] = self._get_input_emails(cast(List[str], email_config.get('recipients', [])))

    def create_and_send_email(self, template_name: str, **template_args: Any) -> None:
        template: Template = self._template_env.get_template(f'{template_name}.html')
        body: str = template.render(template_args)
        subject: str = template_name.replace('_', ' ').title()
        self._email_sender.send_email(self._recipients, body, subject)

    @staticmethod
    def _get_input_emails(input_emails: List[str]) -> List[str]:
        validated_email_recipients: List[str] = []
        for pos in range(0, len(input_emails)):
            if re.match(EmailManager.EMAIL_REGEX, input_emails[pos]):
                validated_email_recipients.append(input_emails[pos])

        if validated_email_recipients:
            print('Email Recipients:')
            print(validated_email_recipients)
        return validated_email_recipients