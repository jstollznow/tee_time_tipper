import json

from email_manager import EmailManager
from program_args import get_args

def main():
    with open(get_args().course_config_path) as f:
        tipper_config = json.load(f)

    email_manager: EmailManager = EmailManager(get_args().local, tipper_config['email_details'])
    email_manager.create_and_send_email("release_notes", features = tipper_config['new_features'])

main()