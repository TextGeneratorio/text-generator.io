"""Tests for BYOK (Bring Your Own Key) system."""

import pytest

from questions.agent.byok import (
    SUPPORTED_PROVIDERS,
    _get_fernet,
    _make_prefix,
    add_key,
    get_key,
    get_user_providers,
    list_keys,
    revoke_key,
)
from questions.db_models_postgres import Base, User, UserAPIKey


@pytest.fixture(scope="module")
def db_engine():
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    session = Session()
    # Clean tables
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        id="byok_test_user",
        email="byok@test.com",
        name="BYOK Tester",
        secret="byok_test_secret",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestEncryption:
    def test_fernet_roundtrip(self):
        fernet = _get_fernet()
        original = "sk-test-1234567890abcdef"
        encrypted = fernet.encrypt(original.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        assert decrypted == original

    def test_make_prefix_long_key(self):
        prefix = _make_prefix("sk-1234567890abcdef1234567890")
        assert prefix.startswith("sk-123")
        assert prefix.endswith("7890")
        assert "..." in prefix

    def test_make_prefix_short_key(self):
        prefix = _make_prefix("short")
        assert prefix == "sho..."


class TestKeyManagement:
    def test_add_and_get_key(self, db_session, test_user):
        api_key = "sk-test-openai-key-12345678"
        result = add_key(db_session, test_user.id, "openai", api_key)

        assert result["provider"] == "openai"
        assert result["is_active"] is True
        assert "sk-tes" in result["key_prefix"]

        # Retrieve the key
        retrieved = get_key(db_session, test_user.id, "openai")
        assert retrieved == api_key

    def test_add_key_replaces_existing(self, db_session, test_user):
        add_key(db_session, test_user.id, "anthropic", "sk-ant-old-key-12345")
        add_key(db_session, test_user.id, "anthropic", "sk-ant-new-key-67890")

        # Should get the new key
        retrieved = get_key(db_session, test_user.id, "anthropic")
        assert retrieved == "sk-ant-new-key-67890"

        # Old key should be inactive
        keys = list_keys(db_session, test_user.id)
        anthropic_keys = [k for k in keys if k["provider"] == "anthropic"]
        assert len(anthropic_keys) == 1  # Only active ones

    def test_add_key_unsupported_provider(self, db_session, test_user):
        with pytest.raises(ValueError, match="Unsupported provider"):
            add_key(db_session, test_user.id, "fakeprovider", "key123456")

    def test_get_key_nonexistent(self, db_session, test_user):
        result = get_key(db_session, test_user.id, "google")
        assert result is None

    def test_list_keys(self, db_session, test_user):
        add_key(db_session, test_user.id, "openai", "sk-openai-key-12345")
        add_key(db_session, test_user.id, "google", "goog-key-67890abc")

        keys = list_keys(db_session, test_user.id)
        assert len(keys) == 2
        providers = {k["provider"] for k in keys}
        assert providers == {"openai", "google"}

        # No encrypted key exposed
        for k in keys:
            assert "encrypted_key" not in k

    def test_revoke_key(self, db_session, test_user):
        result = add_key(db_session, test_user.id, "openai", "sk-to-revoke-123")
        key_id = result["id"]

        assert revoke_key(db_session, test_user.id, key_id) is True
        assert get_key(db_session, test_user.id, "openai") is None

    def test_revoke_nonexistent_key(self, db_session, test_user):
        assert revoke_key(db_session, test_user.id, "nonexistent-id") is False

    def test_revoke_wrong_user(self, db_session, test_user):
        result = add_key(db_session, test_user.id, "openai", "sk-user-key-123")
        assert revoke_key(db_session, "different_user", result["id"]) is False

    def test_get_user_providers(self, db_session, test_user):
        add_key(db_session, test_user.id, "openai", "sk-openai-123456")
        add_key(db_session, test_user.id, "anthropic", "sk-ant-123456789")

        providers = get_user_providers(db_session, test_user.id)
        assert providers == {"openai", "anthropic"}

    def test_get_user_providers_empty(self, db_session, test_user):
        providers = get_user_providers(db_session, test_user.id)
        assert providers == set()


class TestSupportedProviders:
    def test_known_providers(self):
        assert "openai" in SUPPORTED_PROVIDERS
        assert "anthropic" in SUPPORTED_PROVIDERS
        assert "google" in SUPPORTED_PROVIDERS
        assert "groq" in SUPPORTED_PROVIDERS
        assert "deepseek" in SUPPORTED_PROVIDERS
