import json
from html import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.templating import Jinja2Templates

from questions import blog_fixtures, fixtures
from questions.provider_catalog import MODELS, PROVIDERS

router = APIRouter()
_templates = Jinja2Templates(directory=".")

SITE = "https://text-generator.io"
API_BASE = "https://api.text-generator.io/v1"
LASTMOD = "2026-11-10"
HTML_CACHE = "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400"
TEXT_CACHE = "public, max-age=3600, s-maxage=86400, stale-while-revalidate=86400"

PRICING = (
    "Cloud plan $19/month or $190/year; pay-as-you-go API credits at $0.01 each; "
    "self-hosting the open source stack is free. Model rates are listed per 1M tokens at "
    f"{SITE}/models."
)

CURL = f"""curl {API_BASE}/chat/completions \\
  -H "Authorization: Bearer $TEXT_GENERATOR_SECRET" \\
  -H "Content-Type: application/json" \\
  -d '{{"model":"text-generator/auto","messages":[{{"role":"user","content":"Write a haiku about routers"}}]}}'"""

PY = f"""from openai import OpenAI

client = OpenAI(api_key="YOUR_SECRET", base_url="{API_BASE}")
resp = client.chat.completions.create(
    model="text-generator/auto",
    messages=[{{"role": "user", "content": "Write a haiku about routers"}}],
)
print(resp.choices[0].message.content)"""

JS = f"""import OpenAI from "openai";

const client = new OpenAI({{ apiKey: process.env.TEXT_GENERATOR_SECRET, baseURL: "{API_BASE}" }});
const resp = await client.chat.completions.create({{
  model: "text-generator/auto",
  messages: [{{ role: "user", content: "Write a haiku about routers" }}],
}});
console.log(resp.choices[0].message.content);"""

COMMON_FAQ = [
    ("Is the API OpenAI compatible?", f"Yes. Point any OpenAI SDK at {API_BASE} and use your Text Generator secret as the API key. Chat completions, streaming and model listing use the OpenAI request and response format."),
    ("How much does it cost?", PRICING),
    ("Can I self-host it?", "Yes. The stack is open source at github.com/TextGeneratorio/text-generator.io and can be self-hosted for free."),
]

GUIDES = {
    "openai-compatible-api": {
        "title": "OpenAI-Compatible API for Any Model | Text Generator",
        "h1": "An OpenAI-compatible API for every major model",
        "description": "Change one base URL and use GPT, Claude, Gemini, Grok, Kimi, DeepSeek and more through one OpenAI-compatible chat completions API with streaming.",
        "intro": "Keep your existing OpenAI SDK code. Change the base URL and API key, then pick any model in the catalogue or let the auto router choose.",
        "points": [
            "Drop-in /v1/chat/completions with server-sent-event streaming",
            "GET /v1/models lists every model id you can request",
            "One secret and one bill across providers instead of a key per vendor",
            "Automatic fallbacks if a provider is down",
            "Works with the OpenAI Python and JavaScript SDKs, LangChain, LlamaIndex and curl",
        ],
        "faq": [],
    },
    "openai-alternative-api": {
        "title": "OpenAI API Alternative with Multi-Provider Routing | Text Generator",
        "h1": "An OpenAI API alternative that is a one-line change",
        "description": "Switch from the OpenAI API with one base URL change and gain access to Claude, Gemini, Grok, Kimi and DeepSeek models plus an auto router.",
        "intro": "If you already call the OpenAI API, Text Generator accepts the same requests. You keep your code and gain a wider model choice and failover.",
        "points": [
            "Same chat.completions.create call and response shape",
            "Use GPT models or switch to Claude, Gemini, Grok, Kimi K3 or DeepSeek by changing the model string",
            "text-generator/auto picks a model per request for quality, speed and cost",
            "Pay-as-you-go credits with no mandatory subscription",
        ],
        "faq": [("How do I migrate from OpenAI?", f"Set base_url to {API_BASE}, set the API key to your Text Generator secret and keep the rest of your code. Change model to any id from {SITE}/models.")],
    },
    "cheap-llm-api": {
        "title": "Cheap LLM API: Low-Cost Models and Auto Routing | Text Generator",
        "h1": "A low-cost LLM API with cheapest-suitable routing",
        "description": "Cut LLM spend with low-cost models and the text-generator/auto-cheap route. Pay-as-you-go credits, per-model token rates published openly.",
        "intro": "Use text-generator/auto-cheap for formatting, classification and extraction, or pick a small model directly. Rates for every model are published on the catalogue page.",
        "points": [
            "text-generator/auto-cheap routes simple jobs to the lowest-cost suitable model",
            "Small models such as Claude Haiku 5.5 and GPT-4o Mini for high-volume work",
            "Published per-1M-token input and output rates for every model",
            "Credits cost $0.01 each; no seat licences",
        ],
        "faq": [],
    },
    "llm-api-for-coding": {
        "title": "LLM API for Coding and Agents | Text Generator",
        "h1": "A coding LLM API for editors, CLIs and agents",
        "description": "Route code generation, review and agent loops to GPT, Claude, Kimi and DeepSeek models through one OpenAI-compatible endpoint with tool calling.",
        "intro": "Point your editor, CLI or agent framework at one endpoint. text-generator/auto-code routes by task complexity; or select a model explicitly.",
        "points": [
            "text-generator/auto-code for small diffs through architecture work",
            "Tool and function calling on supporting models",
            "Long context windows up to 1M tokens on selected models",
            "Works with any tool that accepts an OpenAI base URL",
        ],
        "faq": [],
    },
    "kimi-k3-api": {
        "title": "Kimi K3 API Access | Text Generator",
        "h1": "Kimi K3 through an OpenAI-compatible API",
        "description": "Call Moonshot's Kimi K3 with the OpenAI SDK. Use model id kimi-k3 on one endpoint alongside GPT, Claude and Gemini.",
        "intro": "Request model kimi-k3 on the same endpoint as every other model. No separate account or SDK is needed.",
        "points": [
            "Model id kimi-k3 on /v1/chat/completions",
            "Fallback route via OpenRouter keeps requests flowing",
            "Switch to another model by changing one string",
        ],
        "model": "kimi-k3",
        "faq": [],
    },
    "llm-router-api": {
        "title": "LLM Router API: Semantic Model Routing | Text Generator",
        "h1": "An LLM router API that picks the model for you",
        "description": "Send one request and let the auto router choose between providers by task, cost and latency. Profiles for fast, cheap, code, reasoning and vision.",
        "intro": "Instead of hard-coding one model, call an auto profile. Profiles: text-generator/auto, auto-fast, auto-cheap, auto-code, auto-reasoning, auto-vision.",
        "points": [
            "Six routing profiles for common workloads",
            "Fallback models if a provider errors",
            "One OpenAI-compatible interface for every route",
        ],
        "faq": [],
    },
    "text-generation-api": {
        "title": "Text Generation API: Generate, Summarize, Classify | Text Generator",
        "h1": "A text generation API for apps and pipelines",
        "description": "Generate text, summarize, classify, translate and extract with a REST API. Controls for max length, stopping sequences, temperature and number of results.",
        "intro": "The native /api/v1/generate endpoint offers fine-grained controls, and the OpenAI-compatible endpoint covers chat. See the full OpenAPI spec for every parameter.",
        "points": [
            "max_length, max_sentences and stopping_sequences control cost and output size",
            "top_p, top_k and temperature control variety",
            "Summarization, embeddings, image captioning and speech endpoints",
            "OpenAPI 3 spec at /openapi.json",
        ],
        "faq": [],
    },
}

COMPARISONS = {
    "openai-api": {
        "title": "Text Generator vs OpenAI API | Comparison",
        "h1": "Text Generator vs the OpenAI API",
        "description": "Factual comparison of Text Generator and the OpenAI API: model choice, compatibility, routing, pricing model and self-hosting.",
        "intro": "The OpenAI API gives direct access to OpenAI's own models. Text Generator exposes an OpenAI-compatible API that also reaches models from several other providers.",
        "rows": [
            ("Models", "OpenAI models", "OpenAI plus Anthropic, Google, xAI, Moonshot, DeepSeek, Mistral and others"),
            ("API format", "OpenAI chat completions and responses", "OpenAI-compatible chat completions with streaming"),
            ("Model selection", "You choose the model", "You choose, or use auto routing profiles"),
            ("Pricing model", "Per-token, set by OpenAI", "Pay-as-you-go credits or a $19/month plan; per-model rates published"),
            ("Self-hosting", "Not available", "Open source stack can be self-hosted"),
        ],
        "note": "Check the OpenAI pricing page for current OpenAI rates; this page does not restate them.",
    },
    "openrouter": {
        "title": "Text Generator vs OpenRouter | Comparison",
        "h1": "Text Generator vs OpenRouter",
        "description": "Compare Text Generator and OpenRouter as unified LLM APIs: routing, catalogue, first-party tools and open source options.",
        "intro": "Both services give one OpenAI-compatible endpoint for many models. Text Generator also provides a semantic auto router and first-party speech, vision and embedding endpoints, and OpenRouter is one of its fallback providers.",
        "rows": [
            ("Unified endpoint", "Yes", "Yes"),
            ("Auto routing profiles", "Provider-side routing options", "Task-based profiles: fast, cheap, code, reasoning, vision"),
            ("Speech, captioning, embeddings", "Not the focus", "Native endpoints included"),
            ("Open source stack", "No", "Yes, self-hostable"),
        ],
        "note": "Feature sets change; verify details on each provider's own documentation.",
    },
    "litellm": {
        "title": "Text Generator vs LiteLLM | Comparison",
        "h1": "Text Generator vs LiteLLM",
        "description": "Hosted unified LLM API versus a self-run proxy: compare operations effort, keys, billing and routing.",
        "intro": "LiteLLM is an open-source library and proxy you run yourself with your own provider keys. Text Generator is a hosted API with provider keys, billing and failover handled for you, and is also self-hostable.",
        "rows": [
            ("Hosting", "You run the proxy", "Hosted, or self-host the open source stack"),
            ("Provider keys", "You bring a key per provider", "One Text Generator secret"),
            ("Billing", "Separate bill per provider", "One credit balance"),
            ("Routing", "Configurable by you", "Built-in auto profiles"),
        ],
        "note": "If you need to keep all traffic inside your own network, a self-run proxy or self-hosting is the better fit.",
    },
}

SITEMAP_STATIC = [
    ("/", "1.0"), ("/models", "0.9"), ("/providers", "0.8"), ("/docs", "0.9"), ("/subscribe", "0.8"),
    ("/playground", "0.7"), ("/use-cases", "0.7"), ("/blog", "0.7"), ("/guides", "0.8"),
    ("/agents", "0.8"), ("/how-it-works", "0.5"), ("/about", "0.4"), ("/contact", "0.3"),
    ("/prompts", "0.5"), ("/tools", "0.6"), ("/selfhosting", "0.5"),
    ("/voice-chat", "0.5"), ("/text-to-speech", "0.5"), ("/speech-to-text", "0.5"),
    ("/privacy", "0.1"), ("/terms", "0.1"),
]


def _ld(obj):
    return json.dumps(obj, separators=(",", ":")).replace("</", "<\\/")


def _breadcrumbs(items):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + path}
            for i, (name, path) in enumerate(items)
        ],
    }


def _software():
    return {
        "@type": "SoftwareApplication",
        "@id": SITE + "/#software",
        "name": "Text Generator",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Web",
        "url": SITE + "/",
        "description": "OpenAI-compatible API and playground for GPT, Claude, Gemini, Grok, Kimi and open models with auto routing.",
        "offers": [
            {"@type": "Offer", "name": "Cloud plan monthly", "price": "19", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "Cloud plan annual", "price": "190", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "API credit", "price": "0.01", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "Self-hosted open source", "price": "0", "priceCurrency": "USD"},
        ],
    }


def _faq(faq):
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq
        ],
    }


def _howto():
    return {
        "@type": "HowTo",
        "name": "Call any model with the OpenAI SDK through Text Generator",
        "step": [
            {"@type": "HowToStep", "position": 1, "name": "Get a secret", "text": f"Create an account at {SITE}/subscribe and copy your secret from the account page."},
            {"@type": "HowToStep", "position": 2, "name": "Set the base URL", "text": f"Set the OpenAI client base_url to {API_BASE}."},
            {"@type": "HowToStep", "position": 3, "name": "Choose a model", "text": "Set model to text-generator/auto or any id from /models, then call chat.completions.create."},
        ],
    }


def _render(request, template, ctx):
    from main import get_base_template_vars

    base = get_base_template_vars(request)
    base.update(ctx)
    resp = _templates.TemplateResponse(template, base)
    resp.headers["Cache-Control"] = HTML_CACHE
    return resp


def _page(request, slug, data, section, section_path):
    faq = list(data.get("faq", [])) + COMMON_FAQ
    path = f"{section_path}/{slug}" if slug else section_path
    graph = [_breadcrumbs([("Home", "/"), (section, section_path), (data["h1"], path)]), _faq(faq), _howto()]
    if section_path == "/guides":
        graph.append(_software())
    model = None
    if data.get("model"):
        from questions.provider_catalog import MODELS_BY_ID

        model = MODELS_BY_ID.get(data["model"])
    related_guides = [(s, g["h1"]) for s, g in GUIDES.items() if s != slug][:5]
    related_compare = [(s, c["h1"]) for s, c in COMPARISONS.items() if s != slug][:3]
    return _render(
        request,
        "templates/seo-page.jinja2",
        {
            "page_title": data["title"],
            "page_description": data["description"],
            "page_path": path,
            "page": data,
            "section": section,
            "section_path": section_path,
            "faq": faq,
            "jsonld": _ld({"@context": "https://schema.org", "@graph": graph}),
            "curl": CURL, "py": PY, "js": JS,
            "pricing": PRICING,
            "model": model,
            "related_guides": related_guides,
            "related_compare": related_compare,
            "skip_canonical": False,
        },
    )


@router.get("/guides")
async def guides_index(request: Request):
    return _render(
        request,
        "templates/seo-index.jinja2",
        {
            "page_title": "Guides and Comparisons | Text Generator API",
            "page_description": "Use-case guides and factual comparisons for the Text Generator OpenAI-compatible LLM API.",
            "guides": [(s, g["h1"], g["description"]) for s, g in GUIDES.items()],
            "comparisons": [(s, c["h1"], c["description"]) for s, c in COMPARISONS.items()],
            "jsonld": _ld({"@context": "https://schema.org", "@graph": [_breadcrumbs([("Home", "/"), ("Guides", "/guides")])]}),
        },
    )


@router.get("/guides/{slug}")
async def guide_page(request: Request, slug: str):
    data = GUIDES.get(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Guide not found")
    return _page(request, slug, data, "Guides", "/guides")


@router.get("/compare/{slug}")
async def compare_page(request: Request, slug: str):
    data = COMPARISONS.get(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return _page(request, slug, data, "Compare", "/compare")


@router.get("/agents")
async def agents_page(request: Request):
    data = {
        "title": "Text Generator for AI Agents and Coding Tools",
        "h1": "Use Text Generator from AI agents and coding tools",
        "description": "Machine-readable docs for agents: llms.txt, OpenAPI spec, OpenAI-compatible endpoint and model list.",
        "intro": f"Agents and tools can discover everything from machine-readable files: {SITE}/llms.txt, {SITE}/llms-full.txt, {SITE}/openapi.json and {API_BASE}/models.",
        "points": [
            f"Base URL {API_BASE} with a Bearer secret",
            "GET /v1/models returns valid model ids",
            "POST /v1/chat/completions supports streaming and tool calling on supporting models",
            "Native REST endpoints for generation, summarization, embeddings, captioning and speech are in the OpenAPI spec",
            "Use any MCP or agent framework that accepts an OpenAI-compatible base URL",
        ],
        "faq": [],
    }
    return _page(request, "", data, "Agents", "/agents")


@router.get("/llms.txt", include_in_schema=False)
async def llms_txt():
    lines = [
        "# Text Generator",
        "",
        "> OpenAI-compatible LLM API and playground. One endpoint and one secret for GPT, Claude, Gemini, Grok, Kimi, DeepSeek and open models, with auto routing, speech, vision and embeddings. Open source and self-hostable.",
        "",
        f"API base URL: {API_BASE}",
        "Auth: Authorization: Bearer YOUR_SECRET",
        f"Pricing: {PRICING}",
        "",
        "## API",
        f"- [OpenAPI spec]({SITE}/openapi.json): machine-readable REST API description",
        f"- [API docs]({SITE}/docs): endpoint reference and examples",
        f"- [Full LLM context]({SITE}/llms-full.txt): models, pricing and examples in one file",
        f"- [Model catalogue]({SITE}/models): every model id with context window and token rates",
        f"- [Providers]({SITE}/providers): upstream providers",
        f"- [Agents guide]({SITE}/agents): using the API from agents and coding tools",
        "",
        "## Guides",
    ]
    lines += [f"- [{g['h1']}]({SITE}/guides/{s}): {g['description']}" for s, g in GUIDES.items()]
    lines += ["", "## Comparisons"]
    lines += [f"- [{c['h1']}]({SITE}/compare/{s}): {c['description']}" for s, c in COMPARISONS.items()]
    lines += ["", "## Optional", f"- [Blog]({SITE}/blog)", f"- [Use cases]({SITE}/use-cases)", f"- [Source code](https://github.com/TextGeneratorio/text-generator.io)", ""]
    return Response("\n".join(lines), media_type="text/plain; charset=utf-8", headers={"Cache-Control": TEXT_CACHE})


@router.get("/llms-full.txt", include_in_schema=False)
async def llms_full_txt():
    out = [
        "# Text Generator: full API context",
        "",
        "Text Generator is an OpenAI-compatible LLM API with auto routing across providers, plus native endpoints for generation, summarization, embeddings, image captioning and speech.",
        "",
        "## Quick start",
        f"Base URL: {API_BASE}",
        "Auth header: Authorization: Bearer YOUR_SECRET (secret from the account page)",
        "",
        "curl:",
        CURL,
        "",
        "Python:",
        PY,
        "",
        "JavaScript:",
        JS,
        "",
        "Streaming: pass stream=true to receive server-sent events in the OpenAI format.",
        f"List models: GET {API_BASE}/models",
        f"Native REST generate endpoint: POST https://api.text-generator.io/api/v1/generate (see {SITE}/openapi.json)",
        "",
        "## Pricing",
        PRICING,
        "",
        "## Routing profiles",
    ]
    for m in MODELS:
        if m.id.startswith("text-generator/"):
            out.append(f"- {m.id}: {m.description}")
    out += ["", "## Providers"]
    out += [f"- {p.name} ({p.slug}): {p.description}" for p in PROVIDERS]
    out += ["", "## Models (id | provider | context | input USD per 1M tokens | output USD per 1M tokens)"]
    out += [f"- {m.id} | {m.provider} | {m.context_window} | {m.input_price:g} | {m.output_price:g}" for m in MODELS]
    out += ["", "## FAQ"]
    for q, a in COMMON_FAQ:
        out += [f"Q: {q}", f"A: {a}", ""]
    out += ["## Pages"]
    out += [f"- {SITE}/guides/{s}: {g['h1']}" for s, g in GUIDES.items()]
    out += [f"- {SITE}/compare/{s}: {c['h1']}" for s, c in COMPARISONS.items()]
    out.append("")
    return Response("\n".join(out), media_type="text/plain; charset=utf-8", headers={"Cache-Control": TEXT_CACHE})


@router.get("/.well-known/llms.txt", include_in_schema=False)
async def well_known_llms():
    return await llms_txt()


@router.get("/.well-known/openapi.json", include_in_schema=False)
async def well_known_openapi():
    from main import load_openapi_spec

    return JSONResponse(load_openapi_spec(), headers={"Cache-Control": TEXT_CACHE})


@router.get("/.well-known/api-catalog", include_in_schema=False)
async def api_catalog():
    body = {
        "linkset": [
            {
                "anchor": API_BASE,
                "service-desc": [{"href": f"{SITE}/openapi.json", "type": "application/json"}],
                "service-doc": [{"href": f"{SITE}/docs", "type": "text/html"}],
                "status": [{"href": f"{API_BASE}/models", "type": "application/json"}],
            }
        ]
    }
    return Response(json.dumps(body), media_type="application/linkset+json", headers={"Cache-Control": TEXT_CACHE})


def build_sitemap_xml() -> str:
    urls = [(p, pr, LASTMOD) for p, pr in SITEMAP_STATIC]
    urls += [(f"/guides/{s}", "0.8", LASTMOD) for s in GUIDES]
    urls += [(f"/compare/{s}", "0.8", LASTMOD) for s in COMPARISONS]
    urls += [(f"/blog/{s}", "0.6", LASTMOD) for s in blog_fixtures.blogs]
    urls += [(f"/use-cases/{s}", "0.5", LASTMOD) for s in fixtures.use_cases]
    urls += [(f"/providers/{p.slug}", "0.6", LASTMOD) for p in PROVIDERS]
    from questions.provider_catalog import MODELS_BY_ID

    urls += [(f"/models/{mid}", "0.6", LASTMOD) for mid in MODELS_BY_ID]
    seen, rows = set(), []
    for p, pr, lm in urls:
        if p in seen:
            continue
        seen.add(p)
        loc = escape(SITE + (p if p != "/" else "/"))
        rows.append(f"<url><loc>{loc}</loc><lastmod>{lm}</lastmod><priority>{pr}</priority></url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n"
