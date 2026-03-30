"""Skills system — procedural memory as markdown.

Skills capture "how to do specific task types" and are loaded on-demand
to keep token usage low (progressive disclosure pattern from Hermes Agent).
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

BUILTIN_SKILLS_DIR = Path(__file__).parent / "skills" / "builtin"


def _parse_skill_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns (metadata_dict, body_text).
    """
    content = content.strip()
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    frontmatter_str = content[3:end].strip()
    body = content[end + 3 :].strip()

    try:
        metadata = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        metadata = {}

    return metadata, body


def load_bundled_skills() -> List[dict]:
    """Load all bundled skills from the builtin directory."""
    skills = []
    if not BUILTIN_SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(BUILTIN_SKILLS_DIR.iterdir()):
        skill_file = skill_dir / "SKILL.md" if skill_dir.is_dir() else None
        if skill_file and skill_file.exists():
            content = skill_file.read_text()
            metadata, body = _parse_skill_frontmatter(content)
            skills.append(
                {
                    "id": f"bundled:{skill_dir.name}",
                    "name": metadata.get("name", skill_dir.name),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", skill_dir.parent.name),
                    "content": content,
                    "version": metadata.get("version", "1.0.0"),
                    "author": metadata.get("author", "text-generator.io"),
                    "is_bundled": True,
                    "is_public": True,
                    "metadata": metadata,
                }
            )
    return skills


def create_skill(db: Session, user_id: str, data: dict) -> dict:
    """Create a new user skill."""
    from questions.db_models_postgres import AgentSkill

    skill = AgentSkill(
        id=str(uuid.uuid4()),
        name=data["name"],
        description=data.get("description"),
        category=data.get("category"),
        content=data["content"],
        user_id=user_id,
        is_public=data.get("is_public", False),
        metadata_json=data.get("metadata"),
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill.to_dict()


def get_skill(db: Session, skill_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a skill by ID. Checks access: bundled, owned, or public."""
    # Check bundled skills first
    if skill_id.startswith("bundled:"):
        for s in load_bundled_skills():
            if s["id"] == skill_id:
                return s
        return None

    from questions.db_models_postgres import AgentSkill

    skill = db.query(AgentSkill).filter_by(id=skill_id).first()
    if not skill:
        return None

    # Access check: own skill or public
    if skill.user_id != user_id and not skill.is_public:
        return None

    return skill.to_dict()


def list_skills(
    db: Session,
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    include_content: bool = False,
) -> List[dict]:
    """List skills: bundled + user's own + public. Progressive disclosure — no content by default."""
    from questions.db_models_postgres import AgentSkill
    from sqlalchemy import or_

    results = []

    # Bundled skills
    for s in load_bundled_skills():
        if category and s.get("category") != category:
            continue
        entry = {k: v for k, v in s.items() if k != "content" or include_content}
        results.append(entry)

    # DB skills: user's own + public
    query = db.query(AgentSkill)
    filters = [AgentSkill.is_public == True]  # noqa: E712
    if user_id:
        filters.append(AgentSkill.user_id == user_id)
    query = query.filter(or_(*filters))

    if category:
        query = query.filter(AgentSkill.category == category)

    for skill in query.order_by(AgentSkill.name).all():
        d = skill.to_dict()
        if not include_content:
            d.pop("content", None)
        results.append(d)

    return results


def update_skill(db: Session, skill_id: str, user_id: str, data: dict) -> Optional[dict]:
    """Update a user-owned skill."""
    from questions.db_models_postgres import AgentSkill

    skill = db.query(AgentSkill).filter_by(id=skill_id, user_id=user_id).first()
    if not skill:
        return None

    for field in ("name", "description", "category", "content", "is_public"):
        if field in data and data[field] is not None:
            setattr(skill, field, data[field])
    if "metadata" in data:
        skill.metadata_json = data["metadata"]

    db.commit()
    db.refresh(skill)
    return skill.to_dict()


def delete_skill(db: Session, skill_id: str, user_id: str) -> bool:
    """Delete a user-owned skill."""
    from questions.db_models_postgres import AgentSkill

    skill = db.query(AgentSkill).filter_by(id=skill_id, user_id=user_id).first()
    if not skill:
        return False
    db.delete(skill)
    db.commit()
    return True


def increment_usage(db: Session, skill_id: str) -> None:
    """Increment usage count for a skill."""
    if skill_id.startswith("bundled:"):
        return  # Bundled skills don't track usage in DB

    from questions.db_models_postgres import AgentSkill

    skill = db.query(AgentSkill).filter_by(id=skill_id).first()
    if skill:
        skill.usage_count = (skill.usage_count or 0) + 1
        db.commit()


def build_skills_prompt(db: Session, user_id: Optional[str] = None) -> str:
    """Build a skills index for the system prompt (names + descriptions only)."""
    skills = list_skills(db, user_id=user_id, include_content=False)
    if not skills:
        return ""

    lines = ["## Available Skills", ""]
    by_category: Dict[str, list] = {}
    for s in skills:
        cat = s.get("category", "general")
        by_category.setdefault(cat, []).append(s)

    for cat in sorted(by_category):
        lines.append(f"### {cat}")
        for s in by_category[cat]:
            tag = " [bundled]" if s.get("is_bundled") else ""
            lines.append(f"- **{s['name']}**{tag}: {s.get('description', 'No description')}")
        lines.append("")

    return "\n".join(lines)
