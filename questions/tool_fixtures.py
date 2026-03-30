tools_fixtures = {
    "competitor-teardown": {
        "name": "Competitor Teardown",
        "description": "Turn competitor URLs and notes into positioning gaps, messaging angles, and copy ideas.",
        "keywords": "competitor analysis, positioning, marketing strategy, landing page copy, AI marketing tool",
        "url": "/tools/competitor-teardown",
        "image": "img/text-generator-brain.png",
    },
    "seo-content-gap": {
        "name": "SEO Content Gap Finder",
        "description": "Build an SEO brief from your site, competitors, and target topics.",
        "keywords": "seo content gap, topic clusters, keyword strategy, content brief, AI SEO tool",
        "url": "/tools/seo-content-gap",
        "image": "img/text-generator-brain.png",
    },
    "offer-generator": {
        "name": "Offer Generator",
        "description": "Package a service or product into clearer tiers, bonuses, guarantees, and CTAs.",
        "keywords": "offer generator, pricing tiers, service packages, business offer, sales copy",
        "url": "/tools/offer-generator",
        "image": "img/text-generator-brain.png",
    },
    "deep-researcher": {
        "name": "Deep Researcher",
        "description": "Run a web-grounded research agent that plans, gathers evidence, and writes a cited report in chat form.",
        "keywords": "deep research agent, ai research assistant, web research, cited report, subscriber tool",
        "url": "/tools/deep-researcher",
        "image": "img/text-generator-brain.png",
        "premium": True,
    },
    "domain-generator": {
        "name": "Domain Name Generator",
        "description": "Generate creative domain names and check their availability instantly.",
        "keywords": "domain name generator, brand naming, startup domains, website ideas",
        "url": "/tools/domain-generator",
        "image": "img/domain-name-generator.webp",
        "premium": True,
    },
    "text-generator-docs": {
        "name": "AI Text Editor",
        "description": "Create and edit documents with AI-powered autocomplete in a beautiful WYSIWYG editor.",
        "keywords": "ai text editor, document editor, writing assistant, autocomplete",
        "url": "/ai-text-editor",
        "image": "img/text-generator-docs.webp",
    },
    "prompt-optimizer": {
        "name": "Prompt Optimizer",
        "description": "Iteratively improve prompts using Claude to get better results.",
        "keywords": "prompt optimizer, prompt engineering, ai prompt improvement, claude prompts",
        "url": "/tools/prompt-optimizer",
        "image": "img/prompt-optimizer.webp",
    },
    "image-captioning-ai": {
        "name": "Image Captioning AI",
        "description": "Generate captions for images using Microsoft's GIT-base model with fast and quality modes.",
        "keywords": "image captioning, image to text, computer vision, caption generator",
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
}
