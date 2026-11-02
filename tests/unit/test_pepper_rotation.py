import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("BCRYPT_ROUNDS", "4")

import bcrypt

from questions import auth


class _DB:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class _User:
    def __init__(self, password_hash):
        self.password_hash = password_hash


def _hash(password, pepper):
    return bcrypt.hashpw((password + pepper).encode(), bcrypt.gensalt(rounds=4)).decode()


def _setup(monkeypatch, user, pepper, old_pepper):
    monkeypatch.setattr(auth, "BCRYPT_ROUNDS", 4)
    monkeypatch.setattr(auth, "BCRYPT_PEPPER", pepper)
    monkeypatch.setattr(auth, "BCRYPT_PEPPER_OLD", old_pepper)
    monkeypatch.setattr(auth.User, "get_by_email", staticmethod(lambda _db, _email: user))


def test_old_pepper_hash_verifies_and_is_repeppered(monkeypatch):
    user, db = _User(_hash("pw", "old")), _DB()
    _setup(monkeypatch, user, "new", "old")
    assert auth.authenticate_user("a@b.c", "pw", db) is user
    assert db.commits == 1
    assert bcrypt.checkpw(b"pwnew", user.password_hash.encode())


def test_current_pepper_hash_is_not_rewritten(monkeypatch):
    original = _hash("pw", "new")
    user, db = _User(original), _DB()
    _setup(monkeypatch, user, "new", "old")
    assert auth.authenticate_user("a@b.c", "pw", db) is user
    assert db.commits == 0
    assert user.password_hash == original


def test_wrong_password_rejected_during_rotation(monkeypatch):
    user, db = _User(_hash("pw", "old")), _DB()
    _setup(monkeypatch, user, "new", "old")
    assert auth.authenticate_user("a@b.c", "nope", db) is None
    assert db.commits == 0


def test_old_pepper_hash_rejected_once_rotation_finished(monkeypatch):
    user, db = _User(_hash("pw", "old")), _DB()
    _setup(monkeypatch, user, "new", "")
    assert auth.authenticate_user("a@b.c", "pw", db) is None
