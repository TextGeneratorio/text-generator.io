"""Tests for chat and batch endpoints."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from questions.agent.batch import MAX_BATCH_SIZE, process_batch
from questions.agent.chat import MAX_TOOL_ITERATIONS, chat_with_tools
from questions.agent.registry import ToolRegistry, registry
from questions.db_models_postgres import Base, BatchJob, User


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
        id="chat_test_user",
        email="chat@test.com",
        name="Chat Tester",
        secret="chat_test_secret",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(autouse=True)
def clean_registry():
    ToolRegistry.reset()
    yield
    ToolRegistry.reset()


def _mock_llm_response(content="Hello!", tool_calls=None, finish_reason="stop"):
    """Build a mock LLM response."""
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
        finish_reason = "tool_calls"
    return {
        "choices": [{"message": message, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "model": "test-model",
    }


class TestChatWithTools:
    @pytest.mark.asyncio
    async def test_simple_chat_no_tools(self):
        with patch("questions.agent.chat.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _mock_llm_response("Hi there!")

            result = await chat_with_tools(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result["message"]["content"] == "Hi there!"
            assert result["tool_calls_made"] == []
            assert result["iterations"] == 1

    @pytest.mark.asyncio
    async def test_chat_with_tool_call(self):
        # Register a tool
        def calc_handler(args, **kwargs):
            return json.dumps({"result": eval(args.get("expression", "0"))})  # noqa: S307

        registry.register(
            name="calculator",
            toolset="utility",
            schema={
                "name": "calculator",
                "description": "Calculate",
                "parameters": {
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
            },
            handler=calc_handler,
        )

        call_count = 0

        async def mock_llm(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: model wants to use calculator
                return _mock_llm_response(
                    content=None,
                    tool_calls=[
                        {
                            "id": "call_1",
                            "function": {
                                "name": "calculator",
                                "arguments": '{"expression": "2 + 2"}',
                            },
                        }
                    ],
                )
            else:
                # Second call: model returns final answer
                return _mock_llm_response("The answer is 4")

        with patch("questions.agent.chat.call_llm", side_effect=mock_llm):
            result = await chat_with_tools(
                messages=[{"role": "user", "content": "What is 2+2?"}],
                tools_enabled=["utility"],
            )

            assert result["message"]["content"] == "The answer is 4"
            assert len(result["tool_calls_made"]) == 1
            assert result["tool_calls_made"][0]["name"] == "calculator"
            assert result["iterations"] == 2

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self):
        with patch("questions.agent.chat.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _mock_llm_response("I'm a pirate!")

            result = await chat_with_tools(
                messages=[{"role": "user", "content": "Who are you?"}],
                system_prompt="You are a pirate.",
            )

            # Check that system prompt was passed in messages
            call_args = mock_llm.call_args
            messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
            assert any("pirate" in m.get("content", "") for m in messages if m["role"] == "system")

    @pytest.mark.asyncio
    async def test_chat_max_iterations(self):
        """Model keeps calling tools until max iterations."""
        call_count = 0

        async def always_tool_call(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return _mock_llm_response(
                content="still working" if call_count >= MAX_TOOL_ITERATIONS else None,
                tool_calls=[
                    {
                        "id": f"call_{call_count}",
                        "function": {
                            "name": "noop",
                            "arguments": "{}",
                        },
                    }
                ],
            )

        registry.register(
            name="noop",
            toolset="test",
            schema={"name": "noop", "description": "No-op", "parameters": {"type": "object", "properties": {}}},
            handler=lambda args, **kw: json.dumps({"ok": True}),
        )

        with patch("questions.agent.chat.call_llm", side_effect=always_tool_call):
            result = await chat_with_tools(
                messages=[{"role": "user", "content": "Loop forever"}],
                tools_enabled=["test"],
            )

            assert result["iterations"] == MAX_TOOL_ITERATIONS


class TestBatchProcessing:
    @pytest.mark.asyncio
    async def test_batch_simple(self, db_session, test_user):
        with patch("questions.agent.batch.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _mock_llm_response("Generated text")

            result = await process_batch(
                db=db_session,
                user_id=test_user.id,
                prompts=[
                    {"prompt": "Write about cats"},
                    {"prompt": "Write about dogs"},
                ],
                model="test-model",
            )

            assert result["status"] == "completed"
            assert result["total_prompts"] == 2
            assert result["completed_prompts"] == 2
            assert result["failed_prompts"] == 0
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_batch_with_errors(self, db_session, test_user):
        call_count = 0

        async def sometimes_fail(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("API error")
            return _mock_llm_response("Generated text")

        with patch("questions.agent.batch.call_llm", side_effect=sometimes_fail):
            result = await process_batch(
                db=db_session,
                user_id=test_user.id,
                prompts=[
                    {"prompt": "Prompt 1"},
                    {"prompt": "Prompt 2 (will fail)"},
                    {"prompt": "Prompt 3"},
                ],
            )

            assert result["completed_prompts"] == 2
            assert result["failed_prompts"] == 1

    @pytest.mark.asyncio
    async def test_batch_too_large(self, db_session, test_user):
        prompts = [{"prompt": f"Prompt {i}"} for i in range(MAX_BATCH_SIZE + 1)]
        with pytest.raises(ValueError, match="exceeds maximum"):
            await process_batch(db=db_session, user_id=test_user.id, prompts=prompts)

    @pytest.mark.asyncio
    async def test_batch_persisted_to_db(self, db_session, test_user):
        with patch("questions.agent.batch.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = _mock_llm_response("Done")

            result = await process_batch(
                db=db_session,
                user_id=test_user.id,
                prompts=[{"prompt": "Test"}],
            )

            # Check it was saved to DB
            job = db_session.query(BatchJob).filter_by(id=result["batch_id"]).first()
            assert job is not None
            assert job.status == "completed"
            assert job.completed_prompts == 1
