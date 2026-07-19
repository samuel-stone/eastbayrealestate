import os


def send_email(message):

    print(
        "EMAIL REPORT:"
    )

    print(message)



def send_sms(message):

    print(
        "SMS REPORT:"
    )

    print(message)



def notify(message):

    send_email(message)

    send_sms(message)
