#!/usr/bin/python
'''
This module processes PayPal Instant Payment Notification messages (IPNs).
'''
from __future__ import print_function

import sys
import os
import cgi
import smtplib
import logging
import json

try:  # Python2
    import urlparse
    from urllib2 import Request, urlopen
    from urllib import urlencode
except ImportError:  # Python3
    import urllib.parse as urlparse
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode

VERIFY_URL_PROD = 'https://www.paypal.com/cgi-bin/webscr'
VERIFY_URL_TEST = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
# non-sandbox useragent should be "PayPal IPN ( https://www.paypal.com/ipn )"
NON_SANDBOX = 'https://www.paypal.com/ipn'
USERAGENT = os.getenv('HTTP_USER_AGENT', '')
VERIFY_URL = VERIFY_URL_PROD if NON_SANDBOX in USERAGENT else VERIFY_URL_TEST
SERVER_NAME = os.getenv('SERVER_NAME', 'localhost')
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
logging.debug('logging at DEBUG level')

def paypal_ipn():
    '''
    verify PayPal transaction
    '''
    print('content-type: text/plain', end='\r\n\r\n')
    parameters = urlparse.parse_qsl(sys.stdin.read())
    # Add '_notify-validate' parameter
    parameters.append(('cmd', '_notify-validate'))
    postdata = urlencode(dict(parameters)).encode('utf8')
    logging.info('postdata: %s', postdata)
    request = Request(VERIFY_URL)
    # Post back to PayPal for validation
    logging.info('posting to %s', VERIFY_URL)
    response = urlopen(request, postdata).read().decode('utf8')
    logging.info('response: %s', response)
    if response == 'VERIFIED':
        logging.info('valid transaction')
        sendmail('successful PayPal transaction', postdata)
    elif response == 'INVALID':
        logging.warning('invalid transaction')
        if dict(parameters).get('txn_type') == 'invoice_payment':
            sendmail('invoice payment cannot be verified', postdata)
        else:
            sendmail('failed PayPal transaction', postdata)
    else:
        logging.error('unexpected response: %s', response)
        sendmail('unknown PayPal transaction', postdata)
    print('IPN session complete.')

def sendmail(subject, contents):
    '''
    send a mail to PayPal recipient or server administrator
    '''
    try:
        ipn_dict = dict(urlparse.parse_qsl(contents))
    except (TypeError, ValueError):
        ipn_dict = {}
    if 'success' in subject:
        to_addr = [ipn_dict.get('receiver_email', 'root@%s' % SERVER_NAME)]
    else:  # don't let people use this for spamming
        to_addr = ['root@%s' % SERVER_NAME]
    from_addr = 'paypal_ipn@%s' % to_addr[0].split('@')[1]
    server = smtplib.SMTP('localhost')
    message = [
        'From: %s\n' % from_addr,
        'To: %s\n' % to_addr[0],
        'Subject: %s\n' % subject,
        '\n',
        'Received order: %s\n' % contents,
    ]
    server.sendmail(from_addr, to_addr, ''.join(message))

if __name__ == '__main__':
    paypal_ipn()
