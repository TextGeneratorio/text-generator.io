import logging
import os.path
import urllib
import urllib2
import wsgiref.handlers

import webapp2
from ws import ws
from models.models import User


RECEIVER_ID = 'xxxxxxxx'
RECEIVER_EMAIL = 'name@example.com'



class IPNHandler(webapp2.RequestHandler):
    def verify_ipn(self, data):
        # prepares provided data set to inform PayPal we wish to validate the response
        data["cmd"] = "_notify-validate"
        params = urllib.urlencode(data)

        if ws.debug:
            # sends the data and request to the PayPal Sandbox
            paypal_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
        else:
            paypal_url = 'https://www.paypal.com/cgi-bin/webscr'



        req = urllib2.Request(paypal_url, params)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        # reads the response back from PayPal
        response = urllib2.urlopen(req)
        status = response.read()



        # If not verified
        if not status == "Verified":
            return False



        # # if not the correct receiver ID
        # if not ws.debug and data['txn_type'] == 'subscr_payment': #and not data["receiver_id"] == RECEIVER_ID:
        #     logging.info('Incorrect receiver_id')
        #     logging.info(data['receiver_id'])
        #     return False



        # # if not the correct receiver email
        # if not ws.debug and data['txn_type'] != 'subscr_payment':# and not data["receiver_email"] == RECEIVER_EMAIL:
        #     logging.info('Incorrect receiver_email')
        #     logging.info(data['receiver_email'])
        #     return False



        # if not the correct currency
        if not ws.debug and not data.get("mc_currency") == "USD":
            logging.info('Incorrect mc_currency')
            return False



        # otherwise...
        return True



    def subscr_signup(self, data):
        # handle a 'Signup' IPN message
        # you can create a User object, for example,
        # or set a user's plan
        pass



    def subscr_payment(self, data):
        # handle a 'Payment' IPN message
        # this message gets sent when you receive a recurring payment
        # you can re-set your user's plan here
        pass



    def subscr_modify(self, data):
        # handle a 'Modify' IPN message
        # the Subscribe button has an option to allow users to modify
        # their subscription plan
        # you can upgrade your user's plan here
        pass



    def subscr_eot(self, data):
        # handle a 'End of Transaction' IPN message
        # at the end of the subscription period, this message gets sent
        # you can disable a user here
        pass



    def subscr_cancel(self, data):
        # handle a 'Cancel' IPN message
        # when a user cancels his subscription (either in his PayPal page or
        # in your website), this message gets sent
        # you can disable a user here
        pass



    def subscr_failed(self, data):
        # handle a 'Failed' IPN message
        # sometimes something goes wrong while the IPN is being sent
        # you can log the error here
        pass



    def post(self, user_id):
        data = {}

        # the values in request.arguments are stored as single value lists
        # we need to extract their string values
        for arg in self.request.arguments():
            data[arg] = self.request.get(arg)

        # If there is no txn_id in the received arguments don't proceed
        if data['txn_type'] == 'subscr_payment' and not 'txn_id' in data:
            logging.info('IPN: No Parameters')
            return

        User.buyFor(user_id)
        # Verify the data received with Paypal
        if not self.request.host.split(':')[0] == 'localhost' and not self.verify_ipn(data):
            logging.info('IPN: Unable to verify')
            return

        logging.info('IPN: Verified!')
        logging.info(data)


        # Now do something with the IPN data
        # if data['txn_type'] == 'express_checkout' or data['txn_type'] == 'web_accept':
        #     #======== BUY  ===== !!!!

        if data['txn_type'] == 'subscr_signup':
            # initial subscription
            self.subscr_signup(data)
        elif data['txn_type'] == 'subscr_payment':
            # subscription renewed
            self.subscr_payment(data)
        elif data['txn_type'] == 'subscr_modify':
            # subscription plan modified
            self.subscr_modify(data)
        elif data['txn_type'] == 'subscr_eot':
            # subscription expired
            self.subscr_eot(data)
        elif data['txn_type'] == 'subscr_cancel':
            # subscription canceled
            self.subscr_cancel(data)
        elif data['txn_type'] == 'subscr_failed':
            # subscription failed
            self.subscr_failed(data)

        return
