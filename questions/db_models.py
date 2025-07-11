"""Database models used by the application.

The project originally stored all data in Google Cloud NDB.  As part of the
migration away from Firebase authentication, users are now persisted using
SQLAlchemy so that either Postgres or SQLite can be utilised.  Documents remain
in NDB for now as the migration is focused on the authentication flow.
"""

import os

from .sql_models import (
    BaseModel,  # SQLAlchemy BaseModel
    User,  # SQLAlchemy User model
)

# Only import NDB when needed for migration
try:
    from google.cloud import ndb
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "local")
    client = ndb.Client(project=project, credentials=None)
    NDB_AVAILABLE = True
except ImportError:
    NDB_AVAILABLE = False
    ndb = None
    client = None

if NDB_AVAILABLE:
    class NDBBaseModel(ndb.Model):
        """Base model for NDB entities with helper serialisation."""

        def to_dict(self):
            result = super().to_dict()
            for key, val in result.items():
                if hasattr(val, "isoformat"):
                    result[key] = val.isoformat()
            return result

        def default(self, o):
            return self.to_dict()

    class Document(NDBBaseModel):
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

else:
    # Provide stub classes when NDB is not available
    class NDBBaseModel:
        """Stub class when NDB is not available."""
        pass
    
    class Document(NDBBaseModel):
        """Stub class when NDB is not available."""
        pass

# The :class:`User` model is now provided by ``questions.sql_models`` and
# re-exported here for backwards compatibility with existing imports.

