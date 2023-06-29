#!/usr/bin/env python
import os
import json

from google.appengine.api import users
import webapp2
from webapp2_extras import sessions
import jinja2

import facebook
from paypal import IPNHandler
from models.models import *
from gameon_utils import GameOnUtils
import utils
import jwt


# application-specific imports
from sellerinfo import SELLER_ID, session_secret
from sellerinfo import SELLER_SECRET
from sellerinfo import FACEBOOK_APP_ID
from sellerinfo import FACEBOOK_APP_SECRET


config = {'webapp2_extras.sessions': session_secret}

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


class BaseHandler(webapp2.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """

    @property
    def current_user(self):
        #===== Google Auth
        user = users.get_current_user()
        if user:
            dbUser = User.byId(user.user_id())
            if dbUser:
                return dbUser
            else:

                dbUser = User()
                dbUser.id = user.user_id()
                dbUser.name = user.nickname()
                dbUser.email = user.email().lower()
                dbUser.put()
                return dbUser

        #===== FACEBOOK Auth
        if self.session.get("user"):
            # User is logged in
            return User.byId(self.session.get("user")["id"])
        else:
            # Either used just logged in or just saw the first page
            # We'll see here
            fbcookie = facebook.get_user_from_cookie(self.request.cookies,
                                                     FACEBOOK_APP_ID,
                                                     FACEBOOK_APP_SECRET)
            if fbcookie:
                # Okay so user logged in.
                # Now, check to see if existing user
                user = User.byId(fbcookie["uid"])
                if not user:
                    # Not an existing user so get user info
                    graph = facebook.GraphAPI(fbcookie["access_token"])
                    profile = graph.get_object("me")
                    user = User(
                        key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profile_url=profile["link"],
                        access_token=fbcookie["access_token"]
                    )
                    user.put()
                elif user.access_token != fbcookie["access_token"]:
                    user.access_token = fbcookie["access_token"]
                    user.put()
                    # User is now logged in
                self.session["user"] = dict(
                    name=user.name,
                    profile_url=user.profile_url,
                    id=user.id,
                    access_token=user.access_token
                )
                return user
                #======== use session cookie user
        anonymous_cookie = self.request.cookies.get('wsuser', None)
        if anonymous_cookie is None:
            cookie_value = utils.random_string()
            self.response.set_cookie('wsuser', cookie_value, max_age=15724800)
            anon_user = User()
            anon_user.cookie_user = 1
            anon_user.id = cookie_value
            anon_user.put()
            return anon_user
        else:
            anon_user = User.byId(anonymous_cookie)
            if anon_user:
                return anon_user
            anon_user = User()
            anon_user.cookie_user = 1
            anon_user.id = anonymous_cookie
            anon_user.put()
            return anon_user

    def render(self, view_name, extraParams={}):

        template_values = {
            # 'ws': ws,
            # 'facebook_app_id': FACEBOOK_APP_ID,
            # 'MEDIUM':MEDIUM,
            # 'EASY':EASY,
            # 'HARD':HARD,
            # 'glogin_url': users.create_login_url(self.request.uri),
            # 'glogout_url': users.create_logout_url(self.request.uri),
            # 'url':self.request.uri,
            # 'num_levels': len(LEVELS)
        }
        template_values.update(extraParams)

        template = JINJA_ENVIRONMENT.get_template(view_name)
        self.response.write(template.render(template_values))

    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        except:
            pass
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        return self.session_store.get_session()


class GetUserHandler(BaseHandler):
    def get(self):
        currentUser = self.current_user
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(currentUser.to_dict(), cls=GameOnUtils.MyEncoder))


class ScoresHandler(BaseHandler):
    # TODO should be ndb.transactional but we would need ancestor queries
    def get(self):
        userscore = Score()
        userscore.score = int(self.request.get('score'))
        userscore.game_mode = int(self.request.get('game_mode'))

        currentUser = self.current_user
        currentUser.scores.append(userscore)
        currentUser.put()

        self.response.out.write('success')


class DeleteAllScoresHandler(BaseHandler):
    def get(self):
        currentUser = self.current_user
        currentUser.scores = []
        currentUser.put()

        self.response.out.write('success')


class AchievementsHandler(BaseHandler):
    def get(self):
        achieve = Achievement()
        achieve.type = int(self.request.get('type'))
        currentUser = self.current_user
        currentUser.achievements.append(achieve)
        currentUser.put()
        self.response.out.write('success')


class IsGoldHandler(BaseHandler):
    def get(self):
        currentUser = self.current_user
        if currentUser.gold:
            self.response.out.write('success')




class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user is not None:
            self.session['user'] = None

        self.redirect('/')


class makeGoldHandler(BaseHandler):
    def get(self):
        if self.request.get('reverse', None):
            user = self.current_user
            user.gold = 0
            user.put()
            self.response.out.write('success')
        else:
            User.buyFor(self.current_user.id)
            ##TODOFIX
            self.redirect("/play")


class SaveVolumeHandler(BaseHandler):
    def get(self):
        user = self.current_user
        user.volume = float(self.request.get('volume', None))
        user.put()
        self.response.out.write('success')


class SaveMuteHandler(BaseHandler):
    def get(self):
        user = self.current_user
        user.mute = int(self.request.get('mute', None))
        user.put()
        self.response.out.write('success')


class SaveLevelsUnlockedHandler(BaseHandler):
    def get(self):
        user = self.current_user
        user.levels_unlocked = int(self.request.get('levels_unlocked', None))
        user.put()
        self.response.out.write('success')


class SaveDifficultiesUnlockedHandler(BaseHandler):
    def get(self):
        user = self.current_user
        user.difficulties_unlocked = int(self.request.get('difficulties_unlocked', None))
        user.put()
        self.response.out.write('success')


class TestsHandler(BaseHandler):
    def get(self):
        try:
            self.render('templates/tests.jinja2')
        except Exception as e:
            import logging
            logging.error(e)


class PostbackHandler(BaseHandler):
    """Handles server postback - received at /postback"""

    def post(self):
        """Handles post request."""
        encoded_jwt = self.request.get('jwt', None)
        if encoded_jwt is not None:
            # jwt.decode won't accept unicode, cast to str
            # http://github.com/progrium/pyjwt/issues/4
            decoded_jwt = jwt.decode(str(encoded_jwt), SELLER_SECRET)

            # validate the payment request and respond back to Google
            if decoded_jwt['iss'] == 'Google' and decoded_jwt['aud'] == SELLER_ID:
                if ('response' in decoded_jwt and
                            'orderId' in decoded_jwt['response'] and
                            'request' in decoded_jwt):
                    order_id = decoded_jwt['response']['orderId']
                    request_info = decoded_jwt['request']
                    if ('currencyCode' in request_info and 'sellerData' in request_info
                        and 'name' in request_info and 'price' in request_info):
                        # optional - update local database
                        # orderId = decoded_jwt['response']['orderId']

                        pb = Postback()
                        pb.jwtPostback = encoded_jwt
                        pb.orderId = order_id
                        # pb.itemName = request_info.get('name')
                        # pb.saleType = decoded_jwt['typ']

                        if (decoded_jwt['typ'] == 'google/payments/inapp/item/v1/postback/buy'):
                            pb.price = request_info['price']
                            pb.currencyCode = request_info['currencyCode']
                        elif (decoded_jwt['typ'] == 'google/payments/inapp/subscription/v1/postback/buy'):
                            pb.price = request_info['initialPayment']['price']
                            pb.currencyCode = request_info['initialPayment']['currencyCode']
                            # pb.recurrencePrice = request_info['recurrence']['price']
                            # pb.recurrenceFrequency = request_info['recurrence']['frequency']

                        pb.put()
                        sellerData = request_info.get('sellerData')
                        User.buyFor(sellerData)
                        # respond back to complete payment
                        self.response.out.write(order_id)


routes = [
    ('/gameon/getuser', GetUserHandler),
    ('/gameon/savescore', ScoresHandler),
    ('/gameon/deleteallscores', DeleteAllScoresHandler),
    ('/gameon/saveachievement', AchievementsHandler),
    ('/gameon/logout', LogoutHandler),
    ('/gameon/postback', PostbackHandler),
    ('/gameon/makegold', makeGoldHandler),
    ('/gameon/isgold', IsGoldHandler),
    ('/gameon/savevolume', SaveVolumeHandler),
    ('/gameon/savemute', SaveMuteHandler),
    ('/gameon/savelevelsunlocked', SaveLevelsUnlockedHandler),
    ('/gameon/savedifficultiesunlocked', SaveDifficultiesUnlockedHandler),
    ('/gameon/tests', TestsHandler),
    (r'/ipn/(.*)', IPNHandler),


]
