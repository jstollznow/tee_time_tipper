import argparse

args = None

def get_args():
    global args
    if args is None:
        args = __init_argparse().parse_args()
    return args

def __init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument('-f','--front_run', action="store_true", help="If enabled, send email with unreleased tee times for next tee time release (course specific).", default = False)
    parser.add_argument('-c', '--course_config_path', help='Set the course config path.', required=True)

    # Dev flags
    parser.add_argument("-l", "--local", action="store_true", help="If enabled, prints email to terminal instead of sending.", default = False)
    parser.add_argument("--no_cache",  action="store_true", help="If enabled, ignores cache of perviously seen times when generating tee times.", default= False)

    return parser