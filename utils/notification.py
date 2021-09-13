import json
import os

import requests
from colorama import Fore, Style


class Notification(object):
    def __init__(self):
        self.userkey = os.environ.get('PUSHOVER_API_KEY')
        self.token = os.environ.get('PUSHOVER_API_TOKEN')
        self.retry = 3

    def notify(self, message, trying=1):
        print("Notifying: {}".format(message))
        r = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": self.token,
            "user": self.userkey,
            "message": message
        })
        response = json.loads(r.text)
        if response['status'] != 1:
            if trying < self.retry:
                print("Retrying again: ", trying)
                self.notify(message, trying=trying + 1)
            else:
                print(f"{Fore.RED}WARNING: Message not sent.{message}{Style.RESET_ALL}\n")
