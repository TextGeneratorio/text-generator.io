"""Tests for the skills system."""

import pytest

from questions.agent.skill_manager import (
    _parse_skill_frontmatter,
    build_skills_prompt,
    create_skill,
    delete_skill,
    get_skill,
    list_skills,
    load_bundled_skills,
    update_skill,
)
from questions.db_models_postgres import AgentSkill, Base, User


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
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        id="skills_test_user",
        email="skills@test.com",
        name="Skills Tester",
        secret="skills_test_secret",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestFrontmatterParsing:
    def test_parse_with_frontmatter(self):
        content = """---
name: test-skill
description: A test skill
category: testing
version: 1.0.0
---

# Test Skill

This is the body."""
        meta, body = _parse_skill_frontmatter(content)
        assert meta["name"] == "test-skill"
        assert meta["description"] == "A test skill"
        assert meta["category"] == "testing"
        assert "# Test Skill" in body

    def test_parse_without_frontmatter(self):
        content = "# Just a markdown file\n\nNo frontmatter here."
        meta, body = _parse_skill_frontmatter(content)
        assert meta == {}
        assert "Just a markdown file" in body

    def test_parse_invalid_yaml(self):
        content = """---
invalid: yaml: [broken
---

Body text."""
        meta, body = _parse_skill_frontmatter(content)
        assert meta == {}
        assert "Body text." in body


class TestBundledSkills:
    def test_load_bundled_skills(self):
        skills = load_bundled_skills()
        assert len(skills) >= 4  # We created 4 bundled skills

        names = {s["name"] for s in skills}
        assert "seo-writer" in names
        assert "blog-post" in names
        assert "code-review" in names
        assert "competitor-analysis" in names

    def test_bundled_skills_have_required_fields(self):
        skills = load_bundled_skills()
        for skill in skills:
            assert skill["id"].startswith("bundled:")
            assert skill["name"]
            assert skill["content"]
            assert skill["is_bundled"] is True
            assert skill["is_public"] is True


class TestSkillCRUD:
    def test_create_skill(self, db_session, test_user):
        result = create_skill(
            db_session,
            test_user.id,
            {
                "name": "my-skill",
                "description": "Custom skill",
                "category": "custom",
                "content": "# My Skill\n\nDo the thing.",
            },
        )
        assert result["name"] == "my-skill"
        assert result["user_id"] == test_user.id
        assert result["is_bundled"] is False

    def test_get_own_skill(self, db_session, test_user):
        created = create_skill(
            db_session,
            test_user.id,
            {"name": "get-test", "content": "content here"},
        )
        retrieved = get_skill(db_session, created["id"], user_id=test_user.id)
        assert retrieved is not None
        assert retrieved["name"] == "get-test"

    def test_get_bundled_skill(self, db_session):
        skills = load_bundled_skills()
        if skills:
            result = get_skill(db_session, skills[0]["id"])
            assert result is not None
            assert result["is_bundled"] is True

    def test_get_other_users_private_skill(self, db_session, test_user):
        created = create_skill(
            db_session,
            test_user.id,
            {"name": "private-skill", "content": "secret", "is_public": False},
        )
        # Different user can't see it
        result = get_skill(db_session, created["id"], user_id="other_user")
        assert result is None

    def test_get_public_skill(self, db_session, test_user):
        created = create_skill(
            db_session,
            test_user.id,
            {"name": "public-skill", "content": "public content", "is_public": True},
        )
        result = get_skill(db_session, created["id"], user_id="other_user")
        assert result is not None

    def test_list_skills_includes_bundled(self, db_session, test_user):
        skills = list_skills(db_session, user_id=test_user.id)
        bundled = [s for s in skills if s.get("is_bundled")]
        assert len(bundled) >= 4

    def test_list_skills_no_content_by_default(self, db_session, test_user):
        create_skill(db_session, test_user.id, {"name": "list-test", "content": "body"})
        skills = list_skills(db_session, user_id=test_user.id, include_content=False)
        for s in skills:
            if not s.get("is_bundled"):
                assert "content" not in s or s.get("content") is None

    def test_list_skills_filter_by_category(self, db_session, test_user):
        create_skill(
            db_session,
            test_user.id,
            {"name": "cat-a", "content": "a", "category": "alpha"},
        )
        create_skill(
            db_session,
            test_user.id,
            {"name": "cat-b", "content": "b", "category": "beta"},
        )
        skills = list_skills(db_session, user_id=test_user.id, category="alpha")
        user_skills = [s for s in skills if not s.get("is_bundled")]
        assert all(s.get("category") == "alpha" for s in user_skills)

    def test_update_skill(self, db_session, test_user):
        created = create_skill(
            db_session,
            test_user.id,
            {"name": "update-me", "content": "old content"},
        )
        updated = update_skill(
            db_session,
            created["id"],
            test_user.id,
            {"content": "new content", "description": "updated"},
        )
        assert updated["content"] == "new content"
        assert updated["description"] == "updated"

    def test_update_nonexistent_skill(self, db_session, test_user):
        result = update_skill(db_session, "fake-id", test_user.id, {"name": "x"})
        assert result is None

    def test_delete_skill(self, db_session, test_user):
        created = create_skill(
            db_session,
            test_user.id,
            {"name": "delete-me", "content": "doomed"},
        )
        assert delete_skill(db_session, created["id"], test_user.id) is True
        assert get_skill(db_session, created["id"], user_id=test_user.id) is None

    def test_delete_nonexistent_skill(self, db_session, test_user):
        assert delete_skill(db_session, "fake-id", test_user.id) is False


class TestSkillsPrompt:
    def test_build_skills_prompt(self, db_session, test_user):
        prompt = build_skills_prompt(db_session, user_id=test_user.id)
        assert "## Available Skills" in prompt
        assert "seo-writer" in prompt
        assert "blog-post" in prompt

    def test_build_skills_prompt_empty_db(self, db_session):
        # Even with empty DB, bundled skills should show
        prompt = build_skills_prompt(db_session)
        assert "seo-writer" in prompt
