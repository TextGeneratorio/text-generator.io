from google.cloud import ndb

client = ndb.Client()


class BaseModel(ndb.Model):
    def default(self, o): return o.to_dict()


class User(BaseModel):
    id = ndb.StringProperty(required=True)

    cookie_user = ndb.IntegerProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    is_subscribed = ndb.BooleanProperty(default=False)
    num_self_hosted_instances = ndb.IntegerProperty(default=0)

    name = ndb.StringProperty()
    email = ndb.StringProperty()

    profile_url = ndb.StringProperty()
    access_token = ndb.StringProperty()
    photo_url = ndb.StringProperty()

    stripe_id = ndb.StringProperty()
    secret = ndb.StringProperty()
    free_credits = ndb.IntegerProperty(default=0)
    charges_monthly = ndb.IntegerProperty(default=0) # send at end of month if over 100 cleared every month

    #     game_urltitles_played = ndb.IntegerProperty()
    @classmethod
    def byId(cls, id):
        with client.context():
            return cls.query(cls.id == id).get()

    @classmethod
    def byEmail(cls, email):
        with client.context():
            return cls.query(cls.email == email).get()

    @classmethod
    def bySecret(cls, secret):
        with client.context():
            return cls.query(cls.secret == secret).get()

    @classmethod
    def save(cls, user):
        with client.context():
            return user.put()


class Document(BaseModel):
    user_id = ndb.StringProperty(required=True)
    title = ndb.StringProperty(default="Untitled Document")
    content = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    
    @classmethod
    def byId(cls, id):
        with client.context():
            return ndb.Key(cls, id).get()
    
    @classmethod
    def byUserId(cls, user_id):
        with client.context():
            return cls.query(cls.user_id == user_id).order(-cls.updated).fetch()
    
    @classmethod
    def save(cls, document):
        with client.context():
            return document.put()

