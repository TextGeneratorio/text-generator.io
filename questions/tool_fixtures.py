tools_fixtures = {
    "domain-name-generator": {
        "name": "Domain Name Generator",
        "description": "Generate creative domain names and check their availability instantly.",
        "url": "/tools/domain-generator",
        "image": "img/domain-name-generator.webp",
    },
    "text-generator-docs": {
        "name": "AI Text Editor",
        "description": "Create and edit documents with AI-powered autocomplete in a beautiful WYSIWYG editor.",
        "url": "/ai-text-editor",
        "image": "img/text-generator-docs.webp",
    },
    "prompt-optimizer": {
        "name": "Prompt Optimizer",
        "description": "Iteratively improve prompts using Claude to get better results.",
        "url": "/tools/prompt-optimizer",
        "image": "img/prompt-optimizer.webp",
    },
    "image-captioning": {
        "name": "Image Captioning AI",
        "description": "Generate captions for images using Microsoft's GIT-base model with fast and quality modes.",
        "url": "/tools/image-captioning-ai",
        "image": "img/image-captioning.webp",
        "api_endpoint": "/api/v1/image-caption",
        "examples": {
            "javascript": """const formData = new FormData();
formData.append('image_file', fileInput.files[0]);
formData.append('fast_mode', true);

fetch('https://api.text-generator.io/api/v1/image-caption', {
    method: 'POST',
    headers: {
        'secret': 'your-api-secret'
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Caption:', data.caption);
    console.log('Model:', data.model);
    console.log('Fast mode:', data.fast_mode);
});""",
            "python": """import requests

url = 'https://api.text-generator.io/api/v1/image-caption'
headers = {'secret': 'your-api-secret'}
files = {'image_file': open('image.jpg', 'rb')}
data = {'fast_mode': True}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()
print(f"Caption: {result['caption']}")""",
            "curl": """curl -X POST "https://api.text-generator.io/api/v1/image-caption" \\
  -H "secret: your-api-secret" \\
  -F "image_file=@image.jpg" \\
  -F "fast_mode=true" """,
            "response": {
                "caption": "a red car parked on the street",
                "filename": "example.jpg",
                "fast_mode": True,
                "model": "microsoft/git-base",
            },
        },
        "features": [
            "Drag & drop interface with visual feedback",
            "Real-time image preview before processing",
            "Fast mode (~200ms) and quality mode (~500ms)",
            "Live code examples in JavaScript, Python, and cURL",
            "Performance metrics and model information",
            "Supports JPEG, PNG, WebP, GIF, BMP, TIFF up to 10MB",
        ],
        "model_info": {
            "name": "microsoft/git-base",
            "optimizations": [
                "Mixed precision (FP16) for 2x speed improvement",
                "Torch compile JIT optimization",
                "Channels-last memory layout for GPU",
                "Persistent model caching",
            ],
            "generation_params": {
                "fast_mode": {"max_length": 10, "num_beams": 1},
                "quality_mode": {"max_length": 30, "num_beams": 3},
            },
        },
    },
    "competitor-teardown": {
        "name": "Competitor Teardown",
        "description": "Analyze competing pages, uncover positioning gaps, and get actionable improvements.",
        "url": "/tools/competitor-teardown",
        "image": "img/prompt-optimizer.webp",
        "keywords": "competitor analysis, positioning, conversion copy, landing page teardown",
        "template": "static/templates/tools/marketing-workflow-tool.jinja2",
        "workflow_key": "competitor-teardown",
    },
    "seo-content-gap-finder": {
        "name": "SEO Content Gap Finder",
        "description": "Compare your site with competitors and generate a prioritized content gap plan.",
        "url": "/tools/seo-content-gap-finder",
        "image": "img/prompt-optimizer.webp",
        "keywords": "seo content gap, topic clusters, content briefs, search growth",
        "template": "static/templates/tools/marketing-workflow-tool.jinja2",
        "workflow_key": "seo-content-gap-finder",
    },
    "deep-researcher": {
        "name": "Deep Researcher",
        "description": "Build structured research summaries with risks, opportunities, and next actions.",
        "url": "/tools/deep-researcher",
        "image": "img/prompt-optimizer.webp",
        "keywords": "deep research, market analysis, synthesis, strategic insights",
        "template": "static/templates/tools/marketing-workflow-tool.jinja2",
        "workflow_key": "deep-researcher",
    },
    "keyword-glossary-explorer": {
        "name": "Keyword & Glossary Explorer",
        "description": "Turn a niche into keyword clusters and plain-English glossary pages you can publish.",
        "url": "/tools/keyword-glossary-explorer",
        "image": "img/prompt-optimizer.webp",
        "keywords": "keyword research, glossary pages, long-tail seo, topical authority",
        "template": "static/templates/tools/marketing-workflow-tool.jinja2",
        "workflow_key": "keyword-glossary-explorer",
    },
}
