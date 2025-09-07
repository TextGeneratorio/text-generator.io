"""Migrate users from Google Cloud NDB to Postgres/SQLite.

Existing users do not have passwords set.  This script copies all user
information except for passwords into the SQL database.  Users will be prompted
to set a password on first login.
"""

from google.cloud import ndb

from questions.sql_models import Base, SessionLocal, User, engine


class NDBUser(ndb.Model):
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
    charges_monthly = ndb.IntegerProperty(default=0)


client = ndb.Client()


def migrate():
    Base.metadata.create_all(bind=engine)
    with client.context():
        for ndb_user in NDBUser.query().fetch():
            with SessionLocal() as session:
                if session.query(User).filter_by(id=ndb_user.id).first():
                    continue
                user = User(
                    id=ndb_user.id,
                    email=ndb_user.email,
                    name=ndb_user.name,
                    stripe_id=ndb_user.stripe_id,
                    secret=ndb_user.secret,
                    free_credits=ndb_user.free_credits,
                    charges_monthly=ndb_user.charges_monthly,
                )
                session.add(user)
                session.commit()
                print(f"Migrated user {user.email}")


if __name__ == "__main__":
    migrate()
