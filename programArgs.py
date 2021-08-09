import argparse

args = None

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('-p','--pwd', help="Password for sending tipper email.")
    parser.add_argument("email_recipients", nargs='*');

    # Feature flags
    parser.add_argument("--email_template",  action="store_true", help="If enabled, use jinja email templating.")


    # Dev flags
    parser.add_argument(
        "-l", "--local", action="store_true", help="If enabled, prints email to terminal instead of sending.")
    parser.add_argument("--no_cache",  action="store_true", help="If enabled, ignores cache of perviously seen times when generating tee times.")
    parser.add_argument("--sender", help="Overwrite the sender email.")

    return parser

def getArgs():
    global args
    if args is None:
        args = init_argparse().parse_args()
    return args