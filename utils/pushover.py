import abc
import json
import os
import time

import requests
from colorama import Fore, Style


class Notification(object):
    @abc.abstractmethod
    def notify(self, message):
        pass


class NoOpNotification(Notification):
    def notify(self, message):
        print("Notifying: {}".format(message))


class Pushover(Notification):
    def __init__(self):
        self.userkey = os.environ.get('PUSHOVER_API_KEY')
        self.token = os.environ.get('PUSHOVER_API_TOKEN')
        self.retry = 3

    def notify(self, message, trying=1):
        print("Notifying: {}".format(message))
        try:
            res = requests.post("https://api.pushover.net/1/messages.json", data={
                "token": self.token,
                "user": self.userkey,
                "message": message
            })
        except ConnectionError:
            print(f"{Fore.RED}WARNING: Message not sent.{message}{Style.RESET_ALL}\n")
            return

        response = json.loads(res.text)
        if response['status'] != 1:
            if trying < self.retry:
                time.sleep(10)
                print("Retrying again ({}) in 10 seconds".format(trying))
                self.notify(message, trying=trying + 1)
            else:
                print(f"{Fore.RED}WARNING: Message not sent.{message}{Style.RESET_ALL}\n")
