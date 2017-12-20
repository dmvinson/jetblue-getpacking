"""Created by dmvinson (https://github.com/dmvinson)"""
from datetime import datetime
import random
import string
import traceback
import time
import threading
import requests


# Configuration variables
FIRST_NAME = "First"
LAST_NAME = "Last"
CAPTCHA_API_KEY = ''  # 2Captcha API Key
# Can be a domain or email for example: example.com or bob@gmail.com
# Domains assume you have enabled catchall email forwarding, regular
# emails uses gmail dot trick
EMAIL = 'example.com'
NUM_THREADS = 10  # Number of threads to be solving captchas and entering
PROXY_FILE = "example.txt"  # proxy file with proxies separated by new lines


ENTRY_URL = 'https://www.jetbluegetpacking.com/php/entry.php'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:58.0) Gecko/20100101 Firefox/58.0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.jetbluegetpacking.com/',
    'DNT': '1',
}


def generate_email(email: str) -> str:
    if "@" not in email:
        prefix = ''.join(random.choice(string.ascii_lowercase)
                         for i in range(12))
        return prefix + "@" + email
    return randomize_email(email)


def random_suffix():
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))


def randomize_email(email):
    email_name = email.split("@")[0]
    dot_positions = random.sample(
        range(1, len(email_name), 1), random.choice(range(1, 5)))
    list_email = list(email_name)
    for dp in dot_positions:
        list_email.insert(dp, ".")
    email_name = ''.join(list_email)
    if ".." in email_name:
        return randomize_email(email)
    email_name += "+" + random_suffix()
    return email_name + "@gmail.com"


def get_token():
    captcha_payload = {
        'key': CAPTCHA_API_KEY,
        'method': 'userrecaptcha',
        'googlekey': '6LfHOj0UAAAAAN5pazlX7UgoXltcV-aFs7U47Xbi',
        'json': 1,
        'pageurl': 'https://www.jetbluegetpacking.com/'
    }

    create_task = requests.get(
        'http://2captcha.com/in.php', params=captcha_payload)
    if "ERROR" in create_task.text:
        print(now(), "-", create_task.text)
        return get_token()
    time.sleep(10)
    while True:
        time.sleep(2)
        get_task_result = requests.get('http://2captcha.com/res.php', params={
                                       'key': CAPTCHA_API_KEY, 'id': create_task.json()['request'], 'action': 'get'})
        if '|' in get_task_result.text:
            print(str(datetime.now()), "- Captcha solved!",
                  get_task_result.text.split('|')[1])
            return get_task_result.text.split('|')[1]
        if 'ERROR_ZERO_BALANCE' in get_task_result:
            print("2Captcha balance empty, exiting")
            quit()


def submit_entry():
    s = requests.Session()
    if len(proxy_list) > 0:
        s.proxies = parse_proxy(random.choice(proxy_list))
    s.headers = headers
    resp = s.get('https://www.jetbluegetpacking.com/')

    email = generate_email(EMAIL)
    token = get_token()

    files = {
        "entry-form-first-name": (None, FIRST_NAME),
        "entry-form-last-name": (None, LAST_NAME),
        "entry-form-email": (None, email),
        "entry-form-email-confirm": (None, email),
        "entry-form-check-opt": (None, "1"),
        "g-recaptcha-response": (None, token),
        "captcha": (None, token),
    }

    r = s.post(ENTRY_URL, files=files, headers={
        "X-Requested-With": "XMLHttpRequest",
    })

    try:
        data = r.json()
    except ValueError:
        print("Error parsing response JSON")
        print(r.text)
        return

    try:
        if 'registrationId' in data:
            print(now(), "- Registration result:", data[
                'message'], "ID:", data['registrationId'])
        elif data["message"] == "CAPTCHA":
            print(now(), "Invalid captcha message, token was", token)
        else:
            print(now(), "- Registration result:", r.json()["message"])
    except KeyError:
        print(now(), "- Error:", r.text)


def now():
    return str(datetime.now().replace(microsecond=0))


def parse_proxy(raw_proxy):
    split_proxy = raw_proxy.split(':')
    if raw_proxy.count(':') == 1:
        proxy = {'https': 'https://' + raw_proxy +
                 '/', 'http': 'http://' + raw_proxy + '/'}
    else:
        proxy = {'https': 'https://' + split_proxy[2] + ':' + split_proxy[3] + '@' + split_proxy[0] + ':' +
                 split_proxy[1] + '/',
                 'http': 'http://' + split_proxy[2] + ':' + split_proxy[3] + '@' + split_proxy[0] + ':' +
                 split_proxy[1] + '/'}
    return proxy


def repeat_entries():
    while True:
        try:
            submit_entry()
        except:
            traceback.print_exc()

if __name__ == "__main__":
    proxy_list = []

    try:
        with open(PROXY_FILE, "r") as f:
            for proxy in f:
                proxy_list.append(proxy.strip('\r\n'))
            print("{} proxies loaded".format(len(proxy_list)))
    except IOError:
        input("Enter anything to continue without proxies, else Control+C")

    entry_threads = []
    for i in range(NUM_THREADS):
        e = threading.Thread(target=repeat_entries)
        e.start()
        entry_threads.append(e)

    for t in entry_threads:
        t.join()
