# System Prompt for 20-Questions Development

## Overview

text-generator.io is a vision language and speech API

## Development Guidelines

### Package Management

- Use `uv` for dependency management
- Edit `requirements.in` files and run `uv pip compile requirements.in -o requirements.txt`
- Install dependencies with:

  ```bash
  uv pip install -r requirements.txt
  uv pip install -r dev-requirements.txt
  uv pip install -r questions/inference_server/requirements.txt
  ```

### Server Operations

- Use `curl` for API testing

### Testing

- Run tests with proper PYTHONPATH: `PYTHONPATH=. pytest tests/test_chat_openai.py`
- All tests should pass before committing changes

### Project Structure

- Main application: `main.py`
- inference server: `questions/` directory
- Routes: `routes/` directory
- AI models: `models/` directory
- Static assets: `static/` directory
- Templates: `templates/` directory

### Key Components

- **API Endpoints**: RESTful API for game interactions

### Development Best Practices

2. Use the existing test suite for validation one test at a time
3. Follow the established directory structure
4. Document any new AI model integrations

### AI Models & Features

- Text generation and inference
- Question summarization
- vision language models
- embeddings
- OCR capabilities
- Audio processing

## Important Notes

- This is an active development environment
- Use the logging system for debugging rather than print statements
