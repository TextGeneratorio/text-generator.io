from collections import Counter
from copy import deepcopy
from typing import Any, Dict, List, Optional


BUSINESS_CATEGORIES = {
    "art-illustration": {
        "slug": "art-illustration",
        "name": "Art & Illustration prompts",
        "short_name": "Art & Illustration",
        "description": "Concept art, key art, editorial scenes, and visual storytelling prompts.",
        "icon": "palette",
    },
    "logo-icon": {
        "slug": "logo-icon",
        "name": "Logo & Icon prompts",
        "short_name": "Logo & Icon",
        "description": "Brand marks, icon systems, social avatars, and recognizable symbol work.",
        "icon": "gesture",
    },
    "graphic-design": {
        "slug": "graphic-design",
        "name": "Graphic & Design prompts",
        "short_name": "Graphic & Design",
        "description": "Layouts, packaging, design systems, and production-ready creative directions.",
        "icon": "grid_view",
    },
    "productivity-writing": {
        "slug": "productivity-writing",
        "name": "Productivity & Writing prompts",
        "short_name": "Productivity & Writing",
        "description": "Operational writing, summaries, memos, planning docs, and knowledge work prompts.",
        "icon": "edit_note",
    },
    "marketing-business": {
        "slug": "marketing-business",
        "name": "Marketing & Business prompts",
        "short_name": "Marketing & Business",
        "description": "Positioning, campaigns, ads, email, brand strategy, and growth prompts.",
        "icon": "campaign",
    },
    "photography": {
        "slug": "photography",
        "name": "Photography prompts",
        "short_name": "Photography",
        "description": "Portrait, product, editorial, cinematic, and brand photography prompts.",
        "icon": "photo_camera",
    },
    "games-3d": {
        "slug": "games-3d",
        "name": "Games & 3D prompts",
        "short_name": "Games & 3D",
        "description": "Environment concepts, assets, character turnarounds, and game-ready scenes.",
        "icon": "sports_esports",
    },
}

PROMPT_TYPES = {
    "image": {
        "slug": "image",
        "name": "Image prompts",
        "description": "Prompts for still image generation, concept art, logos, and design work.",
        "icon": "image",
    },
    "text": {
        "slug": "text",
        "name": "Text prompts",
        "description": "Prompts for copywriting, analysis, planning, summaries, and documents.",
        "icon": "description",
    },
    "video": {
        "slug": "video",
        "name": "Video prompts",
        "description": "Prompts for motion, storyboards, camera moves, and cinematic outputs.",
        "icon": "movie",
    },
    "free": {
        "slug": "free",
        "name": "Free prompts",
        "description": "Prompts marked as free-to-try starters for rapid experimentation.",
        "icon": "bolt",
    },
}

MODELS = {
    "midjourney": {
        "slug": "midjourney",
        "name": "Midjourney",
        "description": "Popular for stylized image generation and visual ideation.",
        "modality": "image",
        "icon": "brush",
    },
    "sora": {
        "slug": "sora",
        "name": "Sora",
        "description": "Text-to-video prompt workflows for cinematic motion concepts.",
        "modality": "video",
        "icon": "movie_creation",
    },
    "flux": {
        "slug": "flux",
        "name": "FLUX",
        "description": "Strong for modern image prompting with crisp detail and polish.",
        "modality": "image",
        "icon": "auto_awesome",
    },
    "dall-e": {
        "slug": "dall-e",
        "name": "DALL-E",
        "description": "Image prompts for structured visual ideation and product visuals.",
        "modality": "image",
        "icon": "photo_filter",
    },
    "chatgpt-image": {
        "slug": "chatgpt-image",
        "name": "ChatGPT Image",
        "description": "Image prompting inside ChatGPT for brand, concept, and visual workflows.",
        "modality": "image",
        "icon": "image_search",
    },
    "gemini-image": {
        "slug": "gemini-image",
        "name": "Gemini Image",
        "description": "Image prompting for scene composition, product ideas, and brand concepts.",
        "modality": "image",
        "icon": "broken_image",
    },
    "kling-ai": {
        "slug": "kling-ai",
        "name": "KLING AI",
        "description": "Video prompting for short-form motion and product storytelling.",
        "modality": "video",
        "icon": "slideshow",
    },
    "hailuo-ai": {
        "slug": "hailuo-ai",
        "name": "Hailuo AI",
        "description": "Video prompting for social clips, b-roll, and motion-heavy ideas.",
        "modality": "video",
        "icon": "ondemand_video",
    },
    "google-imagen": {
        "slug": "google-imagen",
        "name": "Google Imagen",
        "description": "Image prompting for clean composition and polished brand visuals.",
        "modality": "image",
        "icon": "filter",
    },
    "stable-diffusion": {
        "slug": "stable-diffusion",
        "name": "Stable Diffusion",
        "description": "Flexible image prompting for concept art, styles, and visual experimentation.",
        "modality": "image",
        "icon": "tune",
    },
    "deepseek": {
        "slug": "deepseek",
        "name": "DeepSeek",
        "description": "Text prompts for reasoning-heavy business writing and structured output.",
        "modality": "text",
        "icon": "psychology",
    },
    "chatgpt": {
        "slug": "chatgpt",
        "name": "ChatGPT",
        "description": "Text prompts for copy, summaries, planning, and collaborative drafting.",
        "modality": "text",
        "icon": "forum",
    },
    "leonardo-ai": {
        "slug": "leonardo-ai",
        "name": "Leonardo AI",
        "description": "Image prompts for brand, game, and production-style visual work.",
        "modality": "image",
        "icon": "draw",
    },
    "llama": {
        "slug": "llama",
        "name": "Llama",
        "description": "Text prompts for planning, summaries, and business reasoning workflows.",
        "modality": "text",
        "icon": "account_tree",
    },
    "claude": {
        "slug": "claude",
        "name": "Claude",
        "description": "Text prompts for structured writing, synthesis, and high-context tasks.",
        "modality": "text",
        "icon": "rule",
    },
    "ideogram": {
        "slug": "ideogram",
        "name": "Ideogram",
        "description": "Image prompts for logos, typography, icon systems, and brand assets.",
        "modality": "image",
        "icon": "text_fields",
    },
    "gemini": {
        "slug": "gemini",
        "name": "Gemini",
        "description": "Text prompts for synthesis, categorization, and business planning.",
        "modality": "text",
        "icon": "insights",
    },
    "grok": {
        "slug": "grok",
        "name": "Grok",
        "description": "Text prompts for fast ideation, campaign variants, and punchy angles.",
        "modality": "text",
        "icon": "bolt",
    },
    "grok-image": {
        "slug": "grok-image",
        "name": "Grok Image",
        "description": "Image prompts for stylized portraits and fast visual direction.",
        "modality": "image",
        "icon": "portrait",
    },
    "grok-video": {
        "slug": "grok-video",
        "name": "Grok Video",
        "description": "Video prompts for remixing, punchy motion ideas, and social-first outputs.",
        "modality": "video",
        "icon": "video_library",
    },
    "veo": {
        "slug": "veo",
        "name": "Veo",
        "description": "Video prompts for ad concepts, UGC structure, and cinematic scenes.",
        "modality": "video",
        "icon": "videocam",
    },
    "midjourney-video": {
        "slug": "midjourney-video",
        "name": "Midjourney Video",
        "description": "Video prompting for motion concepts and stylized scene movement.",
        "modality": "video",
        "icon": "slow_motion_video",
    },
    "seedance": {
        "slug": "seedance",
        "name": "Seedance",
        "description": "Video prompts for fashion, rhythm, and loop-friendly motion outputs.",
        "modality": "video",
        "icon": "animation",
    },
    "seedream": {
        "slug": "seedream",
        "name": "Seedream",
        "description": "Video prompts for atmospheric reels and polished product loops.",
        "modality": "video",
        "icon": "wb_twilight",
    },
    "hunyuan": {
        "slug": "hunyuan",
        "name": "Hunyuan",
        "description": "Video prompts for 3D spaces, flythroughs, and environment motion.",
        "modality": "video",
        "icon": "view_in_ar",
    },
    "recraft": {
        "slug": "recraft",
        "name": "Recraft",
        "description": "Image prompts for vector-like design, logos, layouts, and graphics.",
        "modality": "image",
        "icon": "design_services",
    },
    "wan": {
        "slug": "wan",
        "name": "Wan",
        "description": "Image prompts for game scenes, UI visuals, and stylized compositions.",
        "modality": "image",
        "icon": "layers",
    },
    "qwen-image": {
        "slug": "qwen-image",
        "name": "Qwen Image",
        "description": "Image prompts for illustrative scenes, UI concepts, and brand assets.",
        "modality": "image",
        "icon": "wallpaper",
    },
}

POPULAR_MODEL_ORDER = [
    "chatgpt",
    "midjourney",
    "claude",
    "sora",
    "flux",
    "ideogram",
    "gemini",
    "veo",
]

PROMPT_DEFINITIONS = [
    {
        "slug": "instagram-logo-prompt",
        "title": "Instagram Logo Prompt",
        "summary": "Build a modern social-first logo direction for an Instagram-native brand.",
        "prompt": """Design a distinctive Instagram-ready logo for [brand].

Requirements:
- Feel premium, modern, and memorable without copying Instagram's existing mark.
- Work as a square avatar, app icon, and profile highlight cover.
- Use a bold gradient-led palette with one dark neutral anchor.
- Show 3 variations: icon-only, wordmark, and stacked lockup.
- Keep linework simple enough to stay legible at 48px.

Return:
- primary visual direction
- color palette
- short rationale
- one alternate minimalist version""",
        "model_slug": "ideogram",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["instagram", "logo", "social media", "brand identity", "avatar"],
        "is_free": True,
        "featured": True,
        "popularity": 98,
    },
    {
        "slug": "threads-logo-prompt",
        "title": "Threads Logo Prompt",
        "summary": "Create a conversational logo concept for a Threads-style social product.",
        "prompt": """Create a clean logo system for [brand], a text-first social network inspired by fast public conversation.

Requirements:
- Simple icon that works in monochrome and high contrast.
- Typography should feel editorial, digital, and slightly opinionated.
- Avoid copying the Threads logo spiral; make the mark original.
- Include app icon, favicon, and launch badge variations.
- Present one bold direction and one ultra-minimal direction.

Output:
- hero logo concept
- icon logic
- type pairing notes
- usage guidance for dark and light backgrounds""",
        "model_slug": "recraft",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["threads", "logo", "social network", "monochrome", "editorial"],
        "is_free": True,
        "featured": True,
        "popularity": 93,
    },
    {
        "slug": "x-logo-prompt",
        "title": "X Logo Prompt",
        "summary": "Generate a sharp, minimal logo direction for a fast-moving X-style brand.",
        "prompt": """Design a logo for [brand] that feels fast, sharp, and confident in the spirit of real-time internet culture.

Requirements:
- Use geometric forms and high-contrast shapes.
- Keep the icon compact enough for favicon and app usage.
- Explore black, silver, and one electric accent color.
- Avoid cloning the existing X logo; find a distinct visual language.
- Include one aggressive direction and one cleaner corporate direction.

Deliver:
- logo concept
- icon construction notes
- palette recommendation
- one sentence describing brand personality""",
        "model_slug": "flux",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["x", "logo", "tech brand", "minimal", "bold"],
        "featured": True,
        "popularity": 95,
    },
    {
        "slug": "reddit-logo-prompt",
        "title": "Reddit Logo Prompt",
        "summary": "Design a playful community-first logo with strong mascot energy.",
        "prompt": """Create a community-driven logo for [brand], a platform built around niche fandoms and discussion.

Requirements:
- Friendly mascot energy with clean modern execution.
- Rounded shapes and approachable color balance.
- Keep the logo recognizable in tiny avatar use.
- Include one mascot-led route and one symbol-only route.
- Show how the mark can extend into stickers, badges, and subreddit-style labels.

Return:
- mascot concept
- simplified icon version
- palette
- short style notes for merch and digital use""",
        "model_slug": "leonardo-ai",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["reddit", "logo", "community", "mascot", "badge"],
        "featured": True,
        "popularity": 90,
    },
    {
        "slug": "bluesky-logo-prompt",
        "title": "Bluesky Logo Prompt",
        "summary": "Create a calm, optimistic, open-network logo concept for a Bluesky-like app.",
        "prompt": """Design a logo for [brand], a calm open-network social platform focused on thoughtful conversation.

Requirements:
- Light, airy, optimistic visual tone.
- A mark that can reference openness, sky, flow, or connection without cliché.
- Use blue-led colors with one bright secondary accent.
- Include profile avatar, splash screen icon, and simple wordmark.
- Keep shapes elegant and highly legible on mobile.

Output:
- main logo concept
- icon-only avatar
- palette notes
- one alternate icon for motion branding""",
        "model_slug": "chatgpt-image",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["bluesky", "logo", "social", "optimistic", "open network"],
        "is_free": True,
        "featured": True,
        "popularity": 88,
    },
    {
        "slug": "discord-logo-prompt",
        "title": "Discord Logo Prompt",
        "summary": "Build a gaming and community logo with strong voice-chat platform energy.",
        "prompt": """Create a logo for [brand], a live community product built around voice rooms, chat, and fandom spaces.

Requirements:
- Friendly but punchy.
- Strong silhouette that works as a circular avatar.
- Slight gaming influence without becoming noisy.
- Include mascot-inspired and symbol-only options.
- Show how the mark scales across server icons, banners, and dark mode UI.

Return:
- hero mark
- alternate mark
- palette
- two short brand adjectives""",
        "model_slug": "midjourney",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["discord", "logo", "gaming", "community", "avatar"],
        "featured": True,
        "popularity": 92,
    },
    {
        "slug": "fintech-icon-pack-prompt",
        "title": "Fintech Icon Pack Prompt",
        "summary": "Generate a clean icon set for a fintech product and dashboard UI.",
        "prompt": """Create a 12-icon visual language for [brand], a fintech dashboard.

Requirements:
- Unified stroke weight and corner radius.
- Categories should include payments, security, analytics, growth, and automation.
- Icons must stay readable at 20px and 32px.
- Use one accent color and neutral line art.
- Deliver icons as a system, not isolated one-offs.

Return:
- icon style direction
- icon descriptions for all 12 concepts
- palette and spacing notes
- one filled variant option""",
        "model_slug": "recraft",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["icon set", "fintech", "dashboard", "ui", "system design"],
        "is_free": True,
        "popularity": 84,
    },
    {
        "slug": "startup-hero-illustration-prompt",
        "title": "Startup Hero Illustration Prompt",
        "summary": "Create a landing-page hero illustration for a B2B SaaS startup.",
        "prompt": """Illustrate a hero visual for [brand], a B2B SaaS company helping teams automate repetitive work.

Requirements:
- Editorial startup style rather than childish clip-art.
- One clear focal metaphor for speed, clarity, or automation.
- Match a modern product landing page with ample whitespace.
- Include room for headline and CTA on the left.
- Use a cobalt, warm orange, and soft neutral palette.

Return:
- final hero art direction
- background treatment
- focal metaphor
- optional small supporting shapes""",
        "model_slug": "google-imagen",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["hero illustration", "saas", "landing page", "automation", "b2b"],
        "featured": True,
        "popularity": 82,
    },
    {
        "slug": "luxury-packaging-concept-prompt",
        "title": "Luxury Packaging Concept Prompt",
        "summary": "Generate a high-end packaging direction for a premium product launch.",
        "prompt": """Design a premium packaging concept for [brand], a luxury direct-to-consumer product.

Requirements:
- Sophisticated materials, premium finish, and tactile visual detail.
- Front, side, and open-box presentation.
- Avoid over-decoration; emphasize restraint and quality.
- Show one flagship colorway and one limited-edition variant.
- Include packaging photography mood and shelf impact considerations.

Output:
- packaging concept
- materials and finishes
- color direction
- mood note for product photography""",
        "model_slug": "flux",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["packaging", "luxury", "branding", "product launch", "retail"],
        "popularity": 80,
    },
    {
        "slug": "editorial-fashion-portrait-prompt",
        "title": "Editorial Fashion Portrait Prompt",
        "summary": "Create a sharp editorial portrait with premium fashion magazine energy.",
        "prompt": """Generate an editorial portrait for [brand], styled like a premium fashion campaign.

Requirements:
- Confident studio lighting and magazine-ready composition.
- Tailored wardrobe with one statement material.
- A restrained background that elevates the subject.
- Output should feel polished, expensive, and modern.
- Include one alternate setup with more cinematic shadows.

Deliver:
- primary portrait direction
- styling notes
- lighting setup
- color grade reference""",
        "model_slug": "gemini-image",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["fashion", "portrait", "editorial", "campaign", "studio"],
        "popularity": 78,
    },
    {
        "slug": "studio-product-photo-prompt",
        "title": "Studio Product Photo Prompt",
        "summary": "Produce a polished studio product shot for ecommerce and launch pages.",
        "prompt": """Create a premium studio product photo for [product].

Requirements:
- Clean background with subtle gradient or shadow plane.
- Crisp reflections or controlled highlights where appropriate.
- Show both one hero angle and one detail crop.
- Keep the product physically believable and premium.
- Make the image useful for ecommerce, press kits, and launch pages.

Return:
- hero shot setup
- lighting notes
- secondary detail shot
- color and material emphasis""",
        "model_slug": "dall-e",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["product photography", "ecommerce", "studio", "launch", "retail"],
        "is_free": True,
        "featured": True,
        "popularity": 87,
    },
    {
        "slug": "fantasy-world-key-art-prompt",
        "title": "Fantasy World Key Art Prompt",
        "summary": "Generate cinematic key art for a fantasy world or game campaign.",
        "prompt": """Create cinematic fantasy key art for [project].

Requirements:
- One strong central environment with layered depth.
- Mood should feel epic, immersive, and marketable.
- Include scale cues such as a lone figure, fortress, or towering landmark.
- Color palette should support a poster or storefront thumbnail.
- Output should feel ready for a Steam page or publishing pitch.

Deliver:
- key art direction
- environment concept
- lighting mood
- optional variant for mobile crop""",
        "model_slug": "stable-diffusion",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["fantasy", "key art", "game art", "environment", "poster"],
        "popularity": 76,
    },
    {
        "slug": "founder-portrait-prompt",
        "title": "Founder Portrait Prompt",
        "summary": "Create a founder portrait that feels sharp, modern, and credible.",
        "prompt": """Generate a founder portrait for [name], the founder of [company].

Requirements:
- Credible startup-leader energy, not generic corporate stock photo.
- Clean wardrobe styling and confident body language.
- Background should subtly reference the company's industry.
- Suitable for website about page, press coverage, and LinkedIn.
- Include one alternate setup with stronger dramatic contrast.

Return:
- portrait direction
- wardrobe suggestion
- background concept
- lighting and crop notes""",
        "model_slug": "grok-image",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["founder portrait", "startup", "about page", "press kit", "linkedin"],
        "popularity": 75,
    },
    {
        "slug": "mobile-app-ui-hero-prompt",
        "title": "Mobile App UI Hero Prompt",
        "summary": "Generate a device mockup and UI hero visual for a mobile app launch.",
        "prompt": """Create a mobile app hero visual for [brand].

Requirements:
- Show one primary phone mockup and supporting UI fragments.
- The layout should feel launch-ready for App Store pages and landing pages.
- Include depth, shadow, and subtle ambient background shapes.
- Prioritize hierarchy and visual clarity over fake complexity.
- Make the product category immediately obvious.

Deliver:
- hero composition
- mockup angle
- background treatment
- palette and CTA contrast notes""",
        "model_slug": "wan",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["app design", "mockup", "mobile", "hero section", "launch"],
        "popularity": 74,
    },
    {
        "slug": "jrpg-town-concept-prompt",
        "title": "JRPG Town Concept Prompt",
        "summary": "Create a memorable JRPG-style town concept for a game world or visual pitch.",
        "prompt": """Design a JRPG town concept for [project].

Requirements:
- Distinct identity visible in silhouette and street layout.
- Charming but production-conscious detail level.
- Mix one signature landmark with readable market, housing, and path areas.
- Daylight version plus a twilight lantern-lit variant.
- Useful for pitch decks, key art, or environment pre-production.

Return:
- town concept
- landmark note
- mood and palette
- optional top-down planning hint""",
        "model_slug": "qwen-image",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["jrpg", "town", "environment", "game pitch", "concept art"],
        "popularity": 73,
    },
    {
        "slug": "unreal-boss-arena-prompt",
        "title": "Unreal Boss Arena Prompt",
        "summary": "Generate a boss arena concept suitable for a modern fantasy action game.",
        "prompt": """Design a boss arena for [game], intended for a modern fantasy action title.

Requirements:
- Strong central arena read with traversal layers and danger zones.
- Built to feel plausible inside an Unreal-style production pipeline.
- Include environmental storytelling and one signature mechanic cue.
- Lighting should sell mood and gameplay readability.
- Show one wide establishing view and one closer combat angle.

Output:
- arena concept
- gameplay silhouette notes
- lighting and material direction
- optional VFX cue""",
        "model_slug": "leonardo-ai",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["boss arena", "unreal", "game environment", "combat", "level design"],
        "popularity": 72,
    },
    {
        "slug": "onboarding-microcopy-prompt",
        "title": "Onboarding Microcopy Prompt",
        "summary": "Write crisp onboarding copy for a product activation funnel.",
        "prompt": """You are a senior product writer.

Write onboarding microcopy for [product], a [product type] used by [audience].

Requirements:
- Tone should be clear, calm, and action-oriented.
- Cover welcome screen, first empty state, tooltip, progress step, and success message.
- Keep each line concise enough for UI.
- Avoid jargon and vague hype.
- Include one more playful variant for startup-style branding.

Return the copy as a structured list with labels.""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["onboarding", "microcopy", "product writing", "ux", "activation"],
        "is_free": True,
        "featured": True,
        "popularity": 86,
    },
    {
        "slug": "cold-email-sequence-prompt",
        "title": "Cold Email Sequence Prompt",
        "summary": "Create a concise outbound email sequence for a B2B offer.",
        "prompt": """Act like a conversion-focused B2B copywriter.

Write a 4-email cold outbound sequence for [offer] aimed at [audience].

Requirements:
- Sound specific and credible, not spammy.
- Each email should have one clear purpose and CTA.
- Use natural subject lines under 6 words.
- Include a breakup email that still protects brand perception.
- Base the messaging on the buyer's likely pains, current workflow, and objections.

Return:
- subject line
- email body
- CTA
- one optional personalization hook per email""",
        "model_slug": "claude",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["cold email", "b2b", "outbound", "sales", "sequence"],
        "featured": True,
        "popularity": 91,
    },
    {
        "slug": "sales-call-summary-prompt",
        "title": "Sales Call Summary Prompt",
        "summary": "Turn raw sales call notes into an actionable summary with next steps.",
        "prompt": """Summarize this sales conversation for an account executive.

Input:
- company: [company]
- deal stage: [stage]
- raw notes: [paste notes]

Requirements:
- Extract pains, decision criteria, blockers, stakeholders, and timing.
- Separate confirmed facts from assumptions.
- Recommend next best action.
- Keep formatting tight enough for CRM notes.
- Add one sentence the AE can send as a follow-up recap.

Output as:
1. account snapshot
2. opportunity summary
3. risks
4. next steps
5. follow-up draft""",
        "model_slug": "deepseek",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["sales", "summary", "crm", "notes", "follow-up"],
        "is_free": True,
        "popularity": 83,
    },
    {
        "slug": "executive-brief-prompt",
        "title": "Executive Brief Prompt",
        "summary": "Turn a messy topic into a concise executive brief for leadership.",
        "prompt": """Prepare an executive brief on [topic] for leadership.

Requirements:
- Focus on business impact, tradeoffs, and recommended actions.
- Use plain language and short sections.
- Include what changed, why it matters, and what decision is needed.
- Flag assumptions and unknowns explicitly.
- End with a decision-ready recommendation.

Return:
- summary
- key facts
- risks
- recommendation
- optional appendix bullets""",
        "model_slug": "llama",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["executive brief", "leadership", "decision memo", "ops", "analysis"],
        "popularity": 77,
    },
    {
        "slug": "competitor-positioning-matrix-prompt",
        "title": "Competitor Positioning Matrix Prompt",
        "summary": "Create a clean competitor matrix for a business, offer, or product category.",
        "prompt": """Build a positioning matrix for [brand] versus these competitors: [competitors].

Requirements:
- Compare audience, promise, pricing posture, proof, and messaging tone.
- Highlight where the market is crowded versus under-served.
- Recommend 3 positioning angles that are easier to own.
- Keep outputs concrete and commercially useful.
- Do not default to generic "quality" or "innovation" claims.

Return as:
- competitor table
- crowded themes
- whitespace opportunities
- recommended angle statements""",
        "model_slug": "gemini",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["competitor analysis", "positioning", "market map", "messaging", "strategy"],
        "featured": True,
        "popularity": 79,
    },
    {
        "slug": "ad-angle-sprint-prompt",
        "title": "Ad Angle Sprint Prompt",
        "summary": "Generate a large batch of ad angles for offers, hooks, and campaign ideas.",
        "prompt": """Generate 20 ad angles for [offer] targeting [audience].

Requirements:
- Include problem-aware, solution-aware, identity-based, urgency-based, and proof-led angles.
- Keep each angle punchy and distinct.
- Add one hook sentence and one visual note for each.
- Flag which 5 angles are strongest for paid social.
- Avoid recycled direct-response clichés unless they are materially adapted.

Return in a table with columns:
angle, hook, visual cue, why it may work""",
        "model_slug": "grok",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["ads", "hooks", "angles", "paid social", "creative strategy"],
        "featured": True,
        "popularity": 85,
    },
    {
        "slug": "brand-voice-guide-prompt",
        "title": "Brand Voice Guide Prompt",
        "summary": "Define a practical brand voice system for marketing and product teams.",
        "prompt": """Create a brand voice guide for [brand].

Inputs:
- company summary: [summary]
- audience: [audience]
- category: [category]
- desired tone: [tone]

Requirements:
- Define voice pillars with do and do-not examples.
- Include sample website headline, product tooltip, sales email opener, and support reply.
- Make the guide actionable for real teams, not abstract.
- Include a "how we sound under pressure" section for crisis or apology moments.

Return as a compact internal guide.""",
        "model_slug": "claude",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["brand voice", "messaging", "style guide", "copywriting", "tone"],
        "featured": True,
        "popularity": 88,
    },
    {
        "slug": "seo-content-brief-prompt",
        "title": "SEO Content Brief Prompt",
        "summary": "Turn a target topic into a structured SEO brief for content production.",
        "prompt": """Create an SEO content brief for the topic [topic].

Requirements:
- Identify likely search intent and reader stage.
- Suggest heading structure, must-cover subtopics, and proof points.
- Include internal linking ideas and a conversion CTA angle.
- Recommend title directions and meta description ideas.
- Avoid keyword stuffing; optimize for clarity and usefulness.

Return:
- target reader
- intent
- outline
- FAQ ideas
- CTA recommendation""",
        "model_slug": "deepseek",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["seo", "content brief", "outline", "search intent", "marketing"],
        "popularity": 81,
    },
    {
        "slug": "meeting-notes-to-plan-prompt",
        "title": "Meeting Notes To Plan Prompt",
        "summary": "Convert a rough meeting transcript into an execution plan.",
        "prompt": """Turn these meeting notes into an execution plan.

Requirements:
- Extract decisions, owners, deadlines, dependencies, and open questions.
- Keep tasks concrete and action-oriented.
- Group work by stream if multiple teams are involved.
- Add a short status summary a PM can paste into Slack.
- Call out contradictions or missing information.

Return:
- decisions
- action items
- risks / blockers
- Slack summary""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["meeting notes", "action plan", "project management", "summary", "slack"],
        "is_free": True,
        "popularity": 80,
    },
    {
        "slug": "customer-research-synthesis-prompt",
        "title": "Customer Research Synthesis Prompt",
        "summary": "Synthesize customer interviews into themes, quotes, and product opportunities.",
        "prompt": """Synthesize these customer research notes into product and messaging insights.

Requirements:
- Cluster findings into clear themes.
- Separate observed evidence from interpretation.
- Pull memorable quotes that illustrate the problem well.
- Highlight tensions, contradictions, and language customers naturally use.
- End with recommended product, onboarding, and marketing implications.

Return as:
- top themes
- representative quotes
- opportunity list
- open questions""",
        "model_slug": "gemini",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["research", "interviews", "voice of customer", "themes", "product discovery"],
        "popularity": 78,
    },
    {
        "slug": "pitch-deck-storyline-prompt",
        "title": "Pitch Deck Storyline Prompt",
        "summary": "Turn a startup idea into a clear investor pitch deck storyline.",
        "prompt": """Create a concise pitch deck storyline for [company].

Requirements:
- Cover problem, market shift, product, traction, moat, business model, and ask.
- Keep the story investor-readable instead of hype-heavy.
- Include the point each slide must prove.
- Call out weak slides or evidence gaps.
- Suggest one tighter narrative arc if the company feels too broad.

Return:
- slide-by-slide storyline
- proof needed
- founder note on likely investor questions""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["pitch deck", "startup", "fundraising", "storytelling", "slides"],
        "popularity": 75,
    },
    {
        "slug": "product-launch-teaser-video-prompt",
        "title": "Product Launch Teaser Video Prompt",
        "summary": "Generate a cinematic teaser for a product launch or announcement.",
        "prompt": """Create a 12-second teaser video for [product].

Requirements:
- Begin with one high-contrast reveal shot.
- Build anticipation before showing the full product.
- Use premium motion and lighting rather than generic stock energy.
- Include one product macro shot, one silhouette shot, and one payoff shot.
- End with room for a short launch date supers text.

Return:
- shot list
- motion and camera guidance
- lighting style
- pacing notes""",
        "model_slug": "sora",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["product launch", "teaser", "cinematic", "announcement", "motion"],
        "featured": True,
        "popularity": 94,
    },
    {
        "slug": "ugc-ad-variations-prompt",
        "title": "UGC Ad Variations Prompt",
        "summary": "Generate multiple short UGC ad structures for a direct-response campaign.",
        "prompt": """Create 3 UGC-style ad concepts for [product].

Requirements:
- Each concept should have a different hook structure.
- Feel like a believable creator ad, not polished TV.
- Include selfie framing, cutaway b-roll, captions, and CTA beats.
- Mention one customer objection and how the ad answers it.
- Keep each ad concept under 20 seconds.

Return:
- concept name
- beat-by-beat shot list
- caption text
- CTA ending""",
        "model_slug": "veo",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["ugc", "ads", "paid social", "creator", "conversion"],
        "featured": True,
        "popularity": 89,
    },
    {
        "slug": "app-walkthrough-video-prompt",
        "title": "App Walkthrough Video Prompt",
        "summary": "Create a short product walkthrough that shows value in under 20 seconds.",
        "prompt": """Generate a short launch video for [app].

Requirements:
- Show the product solving one core workflow clearly.
- Combine UI motion with real-world contextual framing.
- Keep transitions clean and readable for a mobile-first audience.
- Highlight one aha moment around speed or simplicity.
- Finish on product name and CTA.

Return:
- scene plan
- UI interaction beats
- voiceover or caption suggestions
- pacing notes""",
        "model_slug": "kling-ai",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["app walkthrough", "product video", "saas", "mobile", "launch"],
        "popularity": 84,
    },
    {
        "slug": "lifestyle-broll-loop-prompt",
        "title": "Lifestyle B-Roll Loop Prompt",
        "summary": "Generate a lifestyle b-roll clip for product or brand social content.",
        "prompt": """Create a 7-second lifestyle b-roll loop featuring [product] in use.

Requirements:
- Natural handheld or lightly stabilized movement.
- Premium but believable everyday setting.
- Show tactile interaction, not just static beauty shots.
- Keep the composition social-first and loop-friendly.
- Include one detail moment that highlights product quality.

Return:
- scene setup
- motion instruction
- lens / framing suggestion
- loop endpoint guidance""",
        "model_slug": "hailuo-ai",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["b-roll", "lifestyle", "product", "social video", "loop"],
        "popularity": 82,
    },
    {
        "slug": "social-remix-video-prompt",
        "title": "Social Remix Video Prompt",
        "summary": "Create a remixable social clip with punchy pacing and caption moments.",
        "prompt": """Create a 10-second remix-ready social video around [theme].

Requirements:
- Fast opening hook in the first second.
- Clear structure for text overlays and captions.
- Punchy cut rhythm with one standout transition.
- Designed for reposting across X, Reels, Shorts, and TikTok.
- End on a frame that can be reused as a thumbnail.

Return:
- sequence of shots
- caption moments
- transition note
- thumbnail frame guidance""",
        "model_slug": "grok-video",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["social video", "remix", "captions", "shorts", "reels"],
        "popularity": 76,
    },
    {
        "slug": "fashion-lookbook-loop-prompt",
        "title": "Fashion Lookbook Loop Prompt",
        "summary": "Generate a premium fashion loop for lookbooks, campaigns, or product drops.",
        "prompt": """Generate a 9-second fashion lookbook loop for [collection].

Requirements:
- Strong silhouette and movement from fabric or pose shifts.
- Minimal set, premium lighting, and editorial pacing.
- Include one close-up texture moment and one full-body moment.
- Loop seamlessly for social usage.
- Keep styling high-fashion rather than influencer casual.

Return:
- shot sequence
- styling and motion notes
- lighting direction
- loop transition idea""",
        "model_slug": "seedance",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["fashion", "lookbook", "loop", "campaign", "editorial"],
        "popularity": 74,
    },
    {
        "slug": "ambient-product-reel-prompt",
        "title": "Ambient Product Reel Prompt",
        "summary": "Create an atmospheric product reel for brand social and paid media.",
        "prompt": """Create an ambient product reel for [product].

Requirements:
- Soft cinematic movement and premium texture detail.
- Emphasize materials, glow, liquid, glass, or tactile surfaces where relevant.
- Keep the edit calm, upscale, and brand-safe.
- Include one macro detail, one medium reveal, and one final hero composition.
- Suitable for homepage backgrounds and social placements.

Return:
- scene direction
- movement and framing
- texture moments
- color grade reference""",
        "model_slug": "seedream",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["product reel", "ambient", "brand video", "macro", "homepage"],
        "popularity": 73,
    },
    {
        "slug": "drone-establishing-shot-prompt",
        "title": "Drone Establishing Shot Prompt",
        "summary": "Generate a cinematic establishing shot for a location, property, or campaign.",
        "prompt": """Create a cinematic drone establishing shot for [location or brand story].

Requirements:
- Strong sense of scale within 6 to 8 seconds.
- One graceful camera move rather than chaotic movement.
- Light haze, depth, and strong focal landmark.
- End with a composition that can carry title text.
- Suitable for real estate, hospitality, or campaign intros.

Return:
- environment setup
- camera path
- timing notes
- title-safe composition note""",
        "model_slug": "midjourney-video",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["drone", "establishing shot", "hospitality", "real estate", "cinematic"],
        "popularity": 71,
    },
    {
        "slug": "game-environment-flythrough-prompt",
        "title": "Game Environment Flythrough Prompt",
        "summary": "Create a flythrough for a game environment pitch or teaser sequence.",
        "prompt": """Generate a short flythrough for [game environment].

Requirements:
- Showcase layout, scale, and mood in one readable movement.
- Include environmental storytelling details visible from the camera path.
- Make the world feel playable, not just decorative.
- Finish on a hero frame suitable for key art or title reveal.
- Aim for pitch-deck and teaser trailer usefulness.

Return:
- flythrough path
- environment mood
- hero frame
- optional atmospheric FX""",
        "model_slug": "hunyuan",
        "category_slug": "games-3d",
        "modality": "video",
        "tags": ["flythrough", "game environment", "pitch", "teaser", "3d"],
        "popularity": 70,
    },
    {
        "slug": "mascot-turnaround-prompt",
        "title": "Mascot Turnaround Prompt",
        "summary": "Generate a short mascot turnaround useful for brand and motion design work.",
        "prompt": """Create a 360-style turnaround clip for [brand mascot].

Requirements:
- The mascot should feel production-ready for brand use.
- Keep the model readable from front, three-quarter, side, and back angles.
- Include one short personality gesture.
- Lighting should stay neutral enough for design review.
- End on a clean hero pose.

Return:
- character design summary
- turnaround beats
- lighting note
- hero pose description""",
        "model_slug": "sora",
        "category_slug": "games-3d",
        "modality": "video",
        "tags": ["mascot", "turnaround", "brand character", "3d", "motion"],
        "popularity": 69,
    },
    # ── Creative & Cross-Domain Prompts ──────────────────────────────
    {
        "slug": "vintage-album-cover-prompt",
        "title": "Vintage Album Cover Prompt",
        "summary": "Design a vinyl-era album cover with retro typography and analog texture.",
        "prompt": """Design a vintage album cover for [artist or band name] in the style of a 1970s vinyl release.

Requirements:
- Use analog-feeling textures: film grain, letterpress type, faded ink bleeds.
- The cover should tell a visual story about the music's mood without being literal.
- Include hand-drawn or hand-set typography that feels era-authentic.
- Show one front cover concept, one inner sleeve detail, and one back cover layout.
- Palette should feel sun-bleached or chemically saturated depending on genre.

Return:
- front cover art direction
- typography treatment
- inner sleeve concept
- palette and texture notes""",
        "model_slug": "midjourney",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["album cover", "vinyl", "retro", "music", "typography"],
        "featured": True,
        "popularity": 92,
    },
    {
        "slug": "childrens-book-spread-prompt",
        "title": "Children's Book Spread Prompt",
        "summary": "Illustrate a picture book spread with character, environment, and narrative beat.",
        "prompt": """Illustrate a double-page spread for a children's picture book about [story concept].

Requirements:
- One main character with a clear emotional expression and readable silhouette.
- The environment should feel immersive but not overwhelm the character.
- Leave a natural text zone for 2-3 sentences of story copy.
- Use a warm, inviting palette that works for ages 3-7.
- Include one small hidden detail that rewards re-reading.

Return:
- spread composition
- character design notes
- text placement zone
- hidden detail description""",
        "model_slug": "dall-e",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["children's book", "illustration", "picture book", "storytelling", "character"],
        "is_free": True,
        "featured": True,
        "popularity": 90,
    },
    {
        "slug": "architectural-digest-interior-prompt",
        "title": "Architectural Digest Interior Prompt",
        "summary": "Generate a magazine-worthy interior design concept for a luxury space.",
        "prompt": """Create an Architectural Digest-worthy interior for a [room type] in a [style] home.

Requirements:
- Balance statement pieces with livable comfort.
- Show one hero angle and one detail vignette of a curated shelf or surface.
- Include specific material callouts: stone, wood species, textile weave, metal finish.
- Lighting should mix natural and designed sources for editorial warmth.
- The space should feel aspirational but not sterile.

Return:
- hero room concept
- material palette with specific callouts
- furniture arrangement logic
- detail vignette description
- lighting strategy""",
        "model_slug": "flux",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["interior design", "architecture", "luxury", "editorial", "home"],
        "featured": True,
        "popularity": 89,
    },
    {
        "slug": "data-story-infographic-prompt",
        "title": "Data Story Infographic Prompt",
        "summary": "Turn a dataset or trend into a compelling visual infographic narrative.",
        "prompt": """Design an infographic that tells the story of [topic or dataset].

Requirements:
- Lead with one surprising insight that hooks the viewer.
- Use a clear visual hierarchy: headline stat, supporting data, context, and source.
- Avoid chart junk. Every visual element should carry information.
- Design for both full-size web embed and a tall social-story crop.
- Include one custom icon or illustration that makes the topic tangible.

Return:
- narrative flow and reading order
- key data visualizations with chart type recommendations
- color system and typography hierarchy
- social crop adaptation notes""",
        "model_slug": "recraft",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["infographic", "data visualization", "storytelling", "statistics", "design"],
        "is_free": True,
        "featured": True,
        "popularity": 88,
    },
    {
        "slug": "tattoo-flash-sheet-prompt",
        "title": "Tattoo Flash Sheet Prompt",
        "summary": "Create a cohesive tattoo flash sheet with multiple designs in a unified style.",
        "prompt": """Design a tattoo flash sheet around the theme of [theme] in a [style: traditional / fine-line / blackwork / neo-traditional] style.

Requirements:
- Include 6-8 individual designs that work as standalone tattoos.
- Each piece should be readable at actual tattoo scale (2-6 inches).
- Maintain consistent line weight and shading language across the sheet.
- Mix larger statement pieces with smaller filler designs.
- Include one design that works well as a forearm wrap or band.

Return:
- flash sheet layout
- individual design descriptions
- line weight and shading notes
- placement recommendations per piece""",
        "model_slug": "stable-diffusion",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["tattoo", "flash sheet", "body art", "illustration", "design"],
        "featured": True,
        "popularity": 91,
    },
    {
        "slug": "restaurant-menu-design-prompt",
        "title": "Restaurant Menu Design Prompt",
        "summary": "Design a complete restaurant menu with food photography direction and layout.",
        "prompt": """Design a menu for [restaurant name], a [cuisine type] restaurant with a [vibe: casual / fine dining / street food / farm-to-table] atmosphere.

Requirements:
- Layout should guide the eye from appetizers through dessert with natural flow.
- Typography must be readable in dim restaurant lighting.
- Include one signature dish feature with larger visual treatment.
- Balance white space with content density so it doesn't feel overwhelming.
- Show both a single-page and fold-out version.

Return:
- menu layout concept
- typography and hierarchy system
- signature dish feature treatment
- food photography art direction
- paper stock and finish recommendation""",
        "model_slug": "ideogram",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["menu design", "restaurant", "food", "typography", "layout"],
        "popularity": 82,
    },
    {
        "slug": "sci-fi-ui-hud-prompt",
        "title": "Sci-Fi UI HUD Prompt",
        "summary": "Design a futuristic heads-up display interface for a game, film, or concept project.",
        "prompt": """Design a sci-fi HUD interface for [context: spaceship cockpit / cyberpunk visor / medical scanner / mech suit].

Requirements:
- The UI should feel functional and information-dense without being unreadable.
- Use a coherent color system: one primary data color, one alert color, one ambient glow.
- Include at least one radial element, one data stream, and one status indicator.
- The design should work both as a static concept and suggest how it animates.
- Reference real UI/UX principles even in a fictional context.

Return:
- full HUD composition
- element breakdown with function labels
- color and glow system
- animation behavior notes
- one alternate state (alert or damage mode)""",
        "model_slug": "leonardo-ai",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["sci-fi", "hud", "ui design", "game art", "futuristic", "interface"],
        "featured": True,
        "popularity": 93,
    },
    {
        "slug": "botanical-illustration-prompt",
        "title": "Botanical Illustration Prompt",
        "summary": "Create a detailed scientific botanical illustration with modern design sensibility.",
        "prompt": """Create a botanical illustration of [plant species or arrangement] that blends scientific accuracy with modern art direction.

Requirements:
- Show the plant at multiple scales: full form, leaf detail, cross-section or seed structure.
- Use a style that bridges vintage botanical plates and contemporary editorial illustration.
- Include fine detail work on veins, textures, and growth patterns.
- Background should be clean enough for print reproduction on products or wall art.
- Add subtle labeling in a refined sans-serif that references field guide typography.

Return:
- primary illustration
- detail studies
- labeling system
- palette and rendering notes
- print application suggestions""",
        "model_slug": "dall-e",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["botanical", "scientific illustration", "nature", "print", "editorial"],
        "popularity": 79,
    },
    {
        "slug": "podcast-brand-kit-prompt",
        "title": "Podcast Brand Kit Prompt",
        "summary": "Build a complete podcast brand identity: cover art, episode templates, and social assets.",
        "prompt": """Create a full brand kit for [podcast name], a show about [topic] with a [tone: serious / conversational / comedic / investigative] feel.

Requirements:
- Cover art that reads clearly as a 300px square on podcast platforms.
- Episode number template system for consistent publishing.
- Audiogram / quote card template for social promotion.
- Guest photo treatment for interview episodes.
- The brand should feel distinct in a crowded podcast grid.

Return:
- cover art concept
- episode template system
- audiogram / quote card layout
- guest photo treatment
- color palette and type system""",
        "model_slug": "chatgpt-image",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["podcast", "brand kit", "cover art", "social media", "audio"],
        "is_free": True,
        "featured": True,
        "popularity": 86,
    },
    {
        "slug": "isometric-office-scene-prompt",
        "title": "Isometric Office Scene Prompt",
        "summary": "Generate a detailed isometric illustration of a workspace or office environment.",
        "prompt": """Create a detailed isometric illustration of a [workspace type: startup office / co-working space / home office / creative studio].

Requirements:
- Include recognizable human activity: people working, meeting, taking breaks.
- Fill the scene with authentic details that tell a story about the work culture.
- Use a controlled pastel or brand-aligned palette, not random rainbow colors.
- The illustration should work as a hero image, presentation slide, or print poster.
- Include at least one playful easter egg or cultural reference.

Return:
- isometric scene composition
- character and activity descriptions
- detail inventory
- easter egg description
- color system and rendering style""",
        "model_slug": "google-imagen",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["isometric", "office", "workspace", "illustration", "culture"],
        "popularity": 80,
    },
    {
        "slug": "sneaker-concept-design-prompt",
        "title": "Sneaker Concept Design Prompt",
        "summary": "Design a concept sneaker with material callouts, colorways, and brand positioning.",
        "prompt": """Design a concept sneaker for [brand or fictional label] inspired by [theme: brutalist architecture / deep ocean / vintage motorsport / solarpunk].

Requirements:
- Show three views: side profile, three-quarter, and sole detail.
- Include specific material callouts: mesh type, leather grade, foam compound, hardware.
- Design one hero colorway and one alternate limited-edition colorway.
- The silhouette should feel fresh but commercially viable.
- Include a story card that connects the design to its inspiration.

Return:
- sneaker design concept
- material specification list
- two colorway presentations
- story card copy
- retail positioning note""",
        "model_slug": "midjourney",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["sneaker", "product design", "footwear", "concept", "fashion"],
        "featured": True,
        "popularity": 87,
    },
    {
        "slug": "wedding-invitation-suite-prompt",
        "title": "Wedding Invitation Suite Prompt",
        "summary": "Design a cohesive wedding invitation suite with save-the-date and RSVP cards.",
        "prompt": """Design a wedding invitation suite for [names] getting married at [venue type] with a [aesthetic: modern minimal / garden romantic / art deco / coastal / rustic] style.

Requirements:
- Include invitation, RSVP card, details card, and save-the-date.
- Typography should feel considered and match the wedding's formality level.
- Show one design with and one without an illustrated motif or monogram.
- Paper stock and printing technique should be specified.
- The suite should photograph well for social sharing.

Return:
- invitation suite layout
- typography and monogram system
- illustrated motif concept
- paper and printing specification
- envelope treatment""",
        "model_slug": "recraft",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["wedding", "invitation", "stationery", "print design", "typography"],
        "is_free": True,
        "popularity": 78,
    },
    {
        "slug": "retro-pixel-art-game-scene-prompt",
        "title": "Retro Pixel Art Game Scene Prompt",
        "summary": "Create a pixel art game scene with character sprites, tileset, and mood.",
        "prompt": """Create a pixel art scene for a [genre: platformer / RPG / roguelike / adventure] game set in [setting].

Requirements:
- Use a restricted palette of 16-32 colors maximum.
- Include one playable character sprite (idle + one action frame), ground tileset, and background layers.
- The scene should demonstrate parallax depth with 3+ layers.
- Keep pixel density consistent (choose 16x16, 32x32, or 48x48 tile grid).
- Include one animated environmental element (water, fire, leaves, machinery).

Return:
- scene mockup
- character sprite sheet
- tileset sample
- palette with hex values
- animation frame descriptions""",
        "model_slug": "stable-diffusion",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["pixel art", "retro", "game art", "sprite", "indie game"],
        "featured": True,
        "popularity": 88,
    },
    {
        "slug": "food-photography-flat-lay-prompt",
        "title": "Food Photography Flat Lay Prompt",
        "summary": "Create a stunning overhead food photography composition for social or editorial.",
        "prompt": """Create a flat-lay food photography composition featuring [dish or cuisine type].

Requirements:
- Top-down perspective with deliberate negative space and prop placement.
- Include the hero dish, supporting ingredients, utensils, and one textile element.
- Lighting should feel natural and directional, not flat or clinical.
- Props should tell a story about the cooking process or culture.
- Color harmony between food, surfaces, and props is critical.

Return:
- composition layout
- hero dish styling notes
- prop and surface selection
- lighting setup description
- one alternate angle suggestion""",
        "model_slug": "gemini-image",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["food photography", "flat lay", "culinary", "styling", "editorial"],
        "featured": True,
        "popularity": 85,
    },
    {
        "slug": "dnd-character-sheet-art-prompt",
        "title": "D&D Character Sheet Art Prompt",
        "summary": "Generate a full character portrait and equipment spread for a tabletop RPG character.",
        "prompt": """Create character art for a D&D / tabletop RPG character: [race] [class] named [name], who is [personality and backstory brief].

Requirements:
- Full body portrait showing armor, weapons, and distinguishing features.
- One close-up face/expression study showing personality.
- Equipment spread showing 4-6 signature items laid out like a knolling photograph.
- Art style should feel painterly and warm, suitable for a character sheet or player handout.
- Include one action pose variant showing the character using their primary ability.

Return:
- full body portrait
- expression study
- equipment knolling layout
- action pose concept
- color palette and style notes""",
        "model_slug": "midjourney",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["dnd", "character art", "tabletop rpg", "fantasy", "portrait"],
        "featured": True,
        "popularity": 94,
    },
    {
        "slug": "city-map-illustration-prompt",
        "title": "City Map Illustration Prompt",
        "summary": "Design an illustrated city map for tourism, branding, or editorial use.",
        "prompt": """Create an illustrated map of [city or neighborhood] in a [style: hand-drawn / isometric / watercolor / minimalist] style.

Requirements:
- Highlight 8-12 key landmarks, venues, or cultural points of interest.
- Include illustrated icons for each point that are recognizable at small sizes.
- Roads and paths should be simplified but navigable.
- Leave space for a legend and title cartouche.
- The map should work as a poster, guidebook insert, or hotel lobby print.

Return:
- map composition and layout
- landmark icon descriptions
- legend design
- title cartouche concept
- print specification notes""",
        "model_slug": "dall-e",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["map", "illustration", "city", "tourism", "editorial"],
        "popularity": 81,
    },
    {
        "slug": "annual-report-layout-prompt",
        "title": "Annual Report Layout Prompt",
        "summary": "Design a modern annual report layout that makes data and narrative compelling.",
        "prompt": """Design a 4-page annual report spread for [company type] that balances financial data with brand storytelling.

Requirements:
- Cover page with a strong visual hook that isn't generic stock imagery.
- Data pages should make key metrics scannable with clear chart hierarchy.
- Include one full-bleed photography or illustration moment.
- Typography should feel modern and authoritative without being cold.
- The layout should work both as a digital PDF and a physical print piece.

Return:
- cover concept
- spread layout with content zones
- data visualization approach
- typography system
- print vs digital adaptation notes""",
        "model_slug": "recraft",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["annual report", "layout", "corporate", "data design", "print"],
        "popularity": 74,
    },
    {
        "slug": "movie-poster-reimagined-prompt",
        "title": "Movie Poster Reimagined Prompt",
        "summary": "Reimagine a classic or fictional movie as a striking alternative poster design.",
        "prompt": """Design an alternative movie poster for [movie title or original concept] in the style of [style: Saul Bass minimalism / Polish film poster surrealism / Japanese chirashi / Mondo collectible].

Requirements:
- Capture the film's core theme or emotion in one symbolic image.
- Typography should feel era-appropriate for the chosen style.
- The poster should work at both billboard scale and A4 print.
- Avoid literal scene recreation. Focus on mood, metaphor, or iconography.
- Include a subtle visual element that rewards a second look.

Return:
- poster concept and central metaphor
- typography treatment
- color palette
- print specification
- one sentence describing the design's interpretive angle""",
        "model_slug": "flux",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["movie poster", "alternative art", "film", "print", "graphic design"],
        "featured": True,
        "popularity": 91,
    },
    {
        "slug": "api-documentation-guide-prompt",
        "title": "API Documentation Guide Prompt",
        "summary": "Write clear, developer-friendly API documentation from endpoint specifications.",
        "prompt": """Write developer documentation for the following API endpoints: [paste endpoint list or describe the API].

Requirements:
- Write for a developer who has never seen this API before.
- Include authentication setup, base URL, and rate limit information.
- Each endpoint needs: method, path, description, parameters table, example request, example response, and error codes.
- Add a quick-start section that gets someone to their first successful call in under 2 minutes.
- Include copy-pasteable curl examples and one SDK snippet in [language].

Return:
- quick-start guide
- authentication section
- endpoint reference (per endpoint)
- error handling guide
- common patterns and tips""",
        "model_slug": "claude",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["api docs", "developer", "documentation", "technical writing", "reference"],
        "featured": True,
        "popularity": 90,
    },
    {
        "slug": "investor-update-email-prompt",
        "title": "Investor Update Email Prompt",
        "summary": "Write a concise monthly investor update that builds confidence and transparency.",
        "prompt": """Write a monthly investor update email for [company name].

Inputs:
- Key metrics this month: [metrics]
- Wins: [wins]
- Challenges: [challenges]
- Cash position / runway: [numbers]
- Key hires or departures: [if any]
- Asks from investors: [if any]

Requirements:
- Lead with the single most important thing that happened.
- Present metrics with month-over-month context, not vanity numbers.
- Be honest about challenges without being alarmist.
- Keep the total email scannable in under 90 seconds.
- End with specific, concrete asks if applicable.

Return:
- subject line
- full email body
- metrics dashboard section
- asks section""",
        "model_slug": "claude",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["investor update", "startup", "fundraising", "email", "transparency"],
        "featured": True,
        "popularity": 86,
    },
    {
        "slug": "changelog-release-notes-prompt",
        "title": "Changelog & Release Notes Prompt",
        "summary": "Turn git commits and feature notes into polished, user-facing release notes.",
        "prompt": """Transform these raw feature notes and commit messages into polished release notes for [product name].

Input: [paste raw notes, commit messages, or ticket titles]

Requirements:
- Group changes into: New Features, Improvements, Bug Fixes, and Breaking Changes.
- Write each item from the user's perspective, not the developer's.
- Lead each section with the most impactful change.
- Include migration notes for any breaking changes.
- Add a one-paragraph TL;DR at the top that highlights the 2-3 biggest changes.

Return:
- TL;DR summary
- categorized changelog
- migration guide (if needed)
- social announcement draft (1-2 sentences)""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["changelog", "release notes", "product", "developer", "communication"],
        "is_free": True,
        "featured": True,
        "popularity": 84,
    },
    {
        "slug": "debate-prep-brief-prompt",
        "title": "Debate Prep Brief Prompt",
        "summary": "Prepare both sides of an argument with evidence, counterpoints, and rebuttals.",
        "prompt": """Prepare a debate brief on the topic: [topic or proposition].

Requirements:
- Present the strongest 5 arguments FOR and 5 arguments AGAINST.
- For each argument, include supporting evidence or examples.
- Anticipate the top 3 rebuttals for each side.
- Identify the emotional vs logical dimensions of each argument.
- Highlight which arguments are most persuasive for different audiences.

Return:
- proposition statement
- arguments for (with evidence and rebuttals)
- arguments against (with evidence and rebuttals)
- audience-specific persuasion notes
- recommended framing strategy""",
        "model_slug": "deepseek",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["debate", "argumentation", "critical thinking", "research", "persuasion"],
        "is_free": True,
        "popularity": 79,
    },
    {
        "slug": "product-teardown-analysis-prompt",
        "title": "Product Teardown Analysis Prompt",
        "summary": "Perform a detailed UX and business model teardown of a product or app.",
        "prompt": """Perform a product teardown of [product or app name].

Requirements:
- Analyze the onboarding flow, core loop, monetization, and retention mechanics.
- Identify 3 things the product does exceptionally well and why.
- Identify 3 weaknesses or missed opportunities.
- Compare key design decisions against category best practices.
- Suggest 3 experiments they should run next.

Return:
- product overview and positioning
- onboarding analysis
- core loop breakdown
- monetization assessment
- strengths, weaknesses, and recommended experiments""",
        "model_slug": "gemini",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["product teardown", "ux analysis", "competitive intelligence", "strategy", "growth"],
        "featured": True,
        "popularity": 83,
    },
    {
        "slug": "world-building-bible-prompt",
        "title": "World-Building Bible Prompt",
        "summary": "Create a structured world-building document for a novel, game, or creative project.",
        "prompt": """Build a world bible for [project name], set in a [genre / setting description].

Requirements:
- Define the world's core rules: physics, magic system, technology level, or societal structure.
- Create 3 distinct factions or cultures with conflicting goals.
- Establish geography with one map-ready region description.
- Define the world's central tension or conflict engine.
- Include sensory details: what does this world sound, smell, and feel like?

Return:
- world overview and rules
- faction profiles with motivations and conflicts
- geography and key locations
- central tension description
- sensory palette and atmosphere notes
- timeline of major historical events""",
        "model_slug": "claude",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["world building", "creative writing", "fiction", "game design", "lore"],
        "featured": True,
        "popularity": 89,
    },
    {
        "slug": "email-newsletter-redesign-prompt",
        "title": "Email Newsletter Redesign Prompt",
        "summary": "Redesign an email newsletter for higher engagement and clearer hierarchy.",
        "prompt": """Redesign the email newsletter for [brand or publication].

Current issues: [describe current problems: low click rates, cluttered layout, unclear CTA, etc.]

Requirements:
- Create a modular template system that works for weekly sends with varying content volume.
- Establish clear visual hierarchy: one hero story, supporting items, and a persistent CTA.
- Design for dark mode and light mode rendering.
- Keep the template under 600px wide for email client compatibility.
- Include a system for personalizing the header based on subscriber segment.

Return:
- template wireframe
- module system (hero, list, quote, CTA, footer)
- typography and color system for email
- dark mode adaptation notes
- subject line formula recommendations""",
        "model_slug": "chatgpt-image",
        "category_slug": "marketing-business",
        "modality": "image",
        "tags": ["email", "newsletter", "design", "template", "engagement"],
        "popularity": 77,
    },
    {
        "slug": "youtube-thumbnail-system-prompt",
        "title": "YouTube Thumbnail System Prompt",
        "summary": "Create a thumbnail system for YouTube that maximizes click-through rate.",
        "prompt": """Design a YouTube thumbnail system for [channel name], a channel about [topic].

Requirements:
- Thumbnails must be instantly readable at 168x94px (mobile browse size).
- Create a consistent visual language: face crop rules, text treatment, background style.
- Maximum 3-4 words of text per thumbnail, set in a high-contrast treatment.
- Show 5 example thumbnails demonstrating variety within the system.
- Include an A/B testing framework: one emotional variant and one curiosity variant per topic.

Return:
- thumbnail system rules
- 5 example thumbnail concepts
- face and expression guidelines
- text and contrast rules
- A/B testing framework""",
        "model_slug": "flux",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["youtube", "thumbnail", "video", "ctr", "content creator"],
        "featured": True,
        "popularity": 93,
    },
    {
        "slug": "cocktail-recipe-card-prompt",
        "title": "Cocktail Recipe Card Prompt",
        "summary": "Design a beautiful recipe card for a signature cocktail with illustration and instructions.",
        "prompt": """Design a recipe card for [cocktail name], a [spirit base] cocktail with [key ingredients].

Requirements:
- Include an illustrated or photographed hero image of the finished drink.
- List ingredients with precise measurements and preparation method.
- Add a flavor profile radar chart or tasting notes.
- Include one garnish detail illustration and one glassware recommendation.
- The card should feel collectible and suitable for a bar menu insert or social post.

Return:
- recipe card layout
- drink illustration direction
- ingredient list with measurements
- flavor profile visualization
- garnish and glassware notes""",
        "model_slug": "ideogram",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["cocktail", "recipe", "food and drink", "illustration", "menu"],
        "popularity": 76,
    },
    {
        "slug": "github-readme-prompt",
        "title": "GitHub README Prompt",
        "summary": "Write a compelling open-source project README that drives stars and contributions.",
        "prompt": """Write a GitHub README for [project name], a [brief description].

Requirements:
- Open with a one-line description and a visual badge row (build status, version, license).
- Include a hero screenshot or GIF description showing the tool in action.
- Write a "Why this exists" section that explains the problem, not just the solution.
- Quick-start must get someone running in under 60 seconds with copy-paste commands.
- Include a contribution guide section that makes first-time contributors feel welcome.

Return:
- complete README structure
- badge row specifications
- quick-start section
- API or usage examples
- contribution and license sections""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["github", "readme", "open source", "developer", "documentation"],
        "is_free": True,
        "popularity": 85,
    },
    {
        "slug": "conference-talk-outline-prompt",
        "title": "Conference Talk Outline Prompt",
        "summary": "Structure a conference talk that teaches, entertains, and leaves a lasting impression.",
        "prompt": """Create an outline for a [length: 15 / 25 / 45 minute] conference talk titled "[talk title]" for an audience of [audience description].

Requirements:
- Open with a hook that creates tension or curiosity in the first 60 seconds.
- Structure around 3 key ideas maximum, not a laundry list.
- Include one live demo or interactive moment.
- Build toward a memorable closing line or call-to-action.
- Note where to place slides vs live coding vs storytelling.

Return:
- talk structure with time allocations
- opening hook script
- key idea breakdowns with transitions
- demo or interactive moment plan
- closing and Q&A preparation notes""",
        "model_slug": "claude",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["conference talk", "public speaking", "presentation", "teaching", "outline"],
        "featured": True,
        "popularity": 82,
    },
    {
        "slug": "fictional-brand-identity-prompt",
        "title": "Fictional Brand Identity Prompt",
        "summary": "Create a complete brand identity for a fictional company from scratch.",
        "prompt": """Create a full brand identity for [fictional company name], a [industry] company that [value proposition].

Requirements:
- Design a logo that works in monochrome, color, and reversed-out versions.
- Define a color system with primary, secondary, and accent colors with hex values.
- Choose a type system with heading and body fonts that reflect the brand personality.
- Create a one-page brand guidelines snapshot.
- Include mockups: business card, website header, social profile, and one physical touchpoint.

Return:
- logo concept with variations
- color system with rationale
- typography pairing
- brand guidelines snapshot
- mockup applications""",
        "model_slug": "midjourney",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["brand identity", "logo", "design system", "mockup", "fictional"],
        "featured": True,
        "popularity": 90,
    },
    {
        "slug": "product-comparison-blog-prompt",
        "title": "Product Comparison Blog Post Prompt",
        "summary": "Write a fair, detailed comparison post that ranks products for a specific audience.",
        "prompt": """Write a detailed comparison of [Product A] vs [Product B] vs [Product C] for [target audience].

Requirements:
- Open with who each product is best for, so readers can self-select fast.
- Compare on 5-7 criteria that actually matter to the buyer, not feature checklists.
- Include a summary comparison table.
- Be fair. Acknowledge genuine strengths of each option.
- End with a clear recommendation per use case, not a wishy-washy "it depends."

Return:
- quick verdict section
- detailed comparison by criteria
- comparison table
- use-case recommendations
- methodology note""",
        "model_slug": "deepseek",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["comparison", "blog post", "seo", "product review", "content marketing"],
        "is_free": True,
        "popularity": 81,
    },
    {
        "slug": "neon-sign-mockup-prompt",
        "title": "Neon Sign Mockup Prompt",
        "summary": "Create a photorealistic neon sign design for a brand, venue, or art installation.",
        "prompt": """Design a neon sign for [brand name or phrase] installed in a [setting: bar interior / storefront / studio wall / event backdrop].

Requirements:
- The neon should look physically believable with proper glass tube bending constraints.
- Include a glow and ambient light spill on surrounding surfaces.
- Show both an illuminated night version and a daylight off-state version.
- The sign should be reproducible by an actual neon fabricator.
- Include one alternate color variant.

Return:
- neon sign design
- mounting and installation context
- lit vs unlit comparison
- color variant
- fabrication feasibility notes""",
        "model_slug": "flux",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["neon sign", "signage", "branding", "interior", "mockup"],
        "popularity": 83,
    },
    {
        "slug": "stop-motion-product-video-prompt",
        "title": "Stop Motion Product Video Prompt",
        "summary": "Create a stop-motion style product video for social content or brand storytelling.",
        "prompt": """Create a stop-motion style product video for [product] in [duration: 8-15 seconds].

Requirements:
- Use the charming imperfection of stop motion: visible fingerprints of handmade movement.
- Show the product assembling, unboxing, or transforming through physical steps.
- Include tactile materials: paper, fabric, wood, or craft elements as backgrounds.
- Keep the pacing bouncy and social-friendly.
- End on a clean product hero frame with room for brand text.

Return:
- shot-by-shot storyboard
- material and set direction
- movement and pacing guide
- sound design suggestions
- hero frame composition""",
        "model_slug": "kling-ai",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["stop motion", "product video", "handmade", "social content", "craft"],
        "featured": True,
        "popularity": 85,
    },
    {
        "slug": "cinematic-food-video-prompt",
        "title": "Cinematic Food Video Prompt",
        "summary": "Generate a premium cinematic food video with slow motion and macro detail.",
        "prompt": """Create a cinematic food video featuring [dish or ingredient] in [duration: 10-20 seconds].

Requirements:
- Include at least one slow-motion pour, drizzle, or sizzle moment.
- One macro shot showing texture at extreme close-up.
- Lighting should feel warm, directional, and restaurant-quality.
- Camera movement should be smooth and intentional: one dolly, one tilt, one static beauty shot.
- The edit should feel premium enough for a food brand campaign.

Return:
- shot list with camera movements
- lighting setup description
- macro moment specification
- slow-motion beat
- color grade direction""",
        "model_slug": "sora",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["food video", "cinematic", "slow motion", "macro", "culinary"],
        "featured": True,
        "popularity": 90,
    },
    {
        "slug": "before-after-transformation-video-prompt",
        "title": "Before/After Transformation Video Prompt",
        "summary": "Create a satisfying before/after transformation video for renovations, makeovers, or results.",
        "prompt": """Create a before/after transformation video for [subject: room renovation / brand redesign / fitness journey / product upgrade] in [10-15 seconds].

Requirements:
- The "before" should feel genuinely underwhelming without being insulting.
- Use one dramatic reveal transition (swipe, match cut, or time-lapse).
- The "after" should get 2-3x more screen time than the "before."
- Include one detail comparison moment that shows quality difference.
- Optimize for the dopamine hit of transformation content on social feeds.

Return:
- before scene setup
- reveal transition technique
- after showcase shot list
- detail comparison moment
- caption and music pacing notes""",
        "model_slug": "veo",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["before after", "transformation", "reveal", "social video", "renovation"],
        "featured": True,
        "popularity": 92,
    },
    {
        "slug": "travel-destination-reel-prompt",
        "title": "Travel Destination Reel Prompt",
        "summary": "Generate a scroll-stopping travel reel that makes viewers want to book immediately.",
        "prompt": """Create a travel destination reel for [destination] in [12-18 seconds].

Requirements:
- Open with the single most jaw-dropping visual of the destination.
- Mix landscape wides, cultural close-ups, food moments, and human activity.
- Include one golden-hour or blue-hour shot for emotional pull.
- Pacing should match trending travel reel rhythms: fast cuts, one slow beat, fast finish.
- End on a frame that works as both a thumbnail and a "save for later" moment.

Return:
- shot sequence with locations
- golden hour moment
- cultural detail shots
- pacing and music sync notes
- thumbnail frame""",
        "model_slug": "hailuo-ai",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["travel", "destination", "reel", "tourism", "social video"],
        "popularity": 84,
    },
    {
        "slug": "saas-explainer-animation-prompt",
        "title": "SaaS Explainer Animation Prompt",
        "summary": "Create a clean explainer animation that communicates a SaaS product's value in seconds.",
        "prompt": """Create an explainer animation for [product name], a SaaS tool that [value proposition], in [15-30 seconds].

Requirements:
- Open with the problem: show the pain point visually in 3-4 seconds.
- Transition to the solution with one clean UI reveal.
- Show the product solving the problem in 2-3 clear steps.
- Use motion graphics, not cartoon characters, for B2B credibility.
- End with logo, tagline, and one CTA.

Return:
- storyboard with scene descriptions
- problem visualization
- UI reveal and product demo beats
- motion style guide
- voiceover script or caption text""",
        "model_slug": "sora",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["saas", "explainer", "animation", "b2b", "product marketing"],
        "featured": True,
        "popularity": 87,
    },
    {
        "slug": "music-visualizer-loop-prompt",
        "title": "Music Visualizer Loop Prompt",
        "summary": "Generate an abstract music visualizer loop for streaming, events, or social content.",
        "prompt": """Create an abstract music visualizer loop for [genre: electronic / jazz / hip-hop / ambient / orchestral] in [8-12 seconds].

Requirements:
- Motion should feel reactive to rhythm even without actual audio sync.
- Use abstract forms: particles, waveforms, liquid, geometry, or light.
- Keep the palette to 3-4 colors that feel genre-appropriate.
- The loop should be seamless for extended playback.
- Include one climax moment that suggests a drop or crescendo.

Return:
- visual concept and motion language
- color palette with mood rationale
- loop structure and climax beat
- rendering style notes
- suggested BPM range for pairing""",
        "model_slug": "midjourney-video",
        "category_slug": "art-illustration",
        "modality": "video",
        "tags": ["music visualizer", "abstract", "loop", "vj", "motion graphics"],
        "popularity": 78,
    },
    {
        "slug": "personal-swot-analysis-prompt",
        "title": "Personal SWOT Analysis Prompt",
        "summary": "Run a structured SWOT analysis on yourself or your career for strategic planning.",
        "prompt": """Conduct a personal SWOT analysis based on my background.

My context:
- Current role: [role]
- Industry: [industry]
- Years of experience: [years]
- Key skills: [skills]
- Career goal: [goal]

Requirements:
- Be genuinely critical in weaknesses and threats, not just politely encouraging.
- Identify strengths that are actually differentiating, not generic.
- Map opportunities to specific actions I can take in the next 90 days.
- Connect threats to market trends or industry shifts, not vague fears.
- End with a prioritized action plan.

Return:
- strengths (with what makes them rare)
- weaknesses (with honest assessment)
- opportunities (with 90-day actions)
- threats (with market context)
- prioritized action plan""",
        "model_slug": "claude",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["swot analysis", "career planning", "self assessment", "strategy", "personal development"],
        "is_free": True,
        "popularity": 80,
    },
    {
        "slug": "newsletter-growth-strategy-prompt",
        "title": "Newsletter Growth Strategy Prompt",
        "summary": "Build a practical newsletter growth plan from zero to 10K subscribers.",
        "prompt": """Create a newsletter growth strategy for [newsletter name] about [topic], currently at [subscriber count] subscribers.

Requirements:
- Map the growth engine: where will subscribers actually come from?
- Include 5 acquisition channels ranked by effort vs impact.
- Define the referral loop or viral mechanic.
- Specify a content calendar cadence and pillar topics.
- Set realistic milestone targets with specific tactics for each stage.

Return:
- growth engine overview
- channel-by-channel acquisition plan
- referral mechanic design
- content strategy and cadence
- milestone roadmap (1K, 5K, 10K)""",
        "model_slug": "grok",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["newsletter", "growth", "audience building", "content strategy", "email"],
        "featured": True,
        "popularity": 84,
    },
    {
        "slug": "board-game-design-prompt",
        "title": "Board Game Design Prompt",
        "summary": "Design core mechanics, components, and theme for an original board game concept.",
        "prompt": """Design a board game concept for [theme or setting] aimed at [player count] players, [age range], with a target play time of [duration].

Requirements:
- Define the core mechanic that makes the game unique and replayable.
- Describe 3-5 key components: board, cards, tokens, dice, or custom pieces.
- Explain the turn structure and win condition clearly.
- Include one catch-up mechanic so trailing players stay engaged.
- Describe the emotional arc: what feelings should players have at start, middle, and end?

Return:
- game overview and theme
- core mechanic explanation
- component list with descriptions
- turn structure and rules summary
- catch-up mechanic
- emotional arc and playtesting notes""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["board game", "game design", "tabletop", "mechanics", "creative"],
        "is_free": True,
        "popularity": 81,
    },
    {
        "slug": "brand-photography-moodboard-prompt",
        "title": "Brand Photography Moodboard Prompt",
        "summary": "Create a photography moodboard that defines the visual direction for a brand shoot.",
        "prompt": """Create a photography moodboard for [brand name], a [brand type] targeting [audience].

Requirements:
- Define 4 distinct photography moods: hero product, lifestyle in-use, detail/texture, and team/culture.
- Specify lighting direction, color temperature, and depth of field for each mood.
- Include wardrobe and prop styling notes.
- Reference real-world locations or set types.
- The moodboard should be specific enough to brief a photographer directly.

Return:
- 4 mood categories with descriptions
- lighting and camera specs per mood
- styling and prop direction
- location or set references
- shot list template""",
        "model_slug": "gemini-image",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["moodboard", "brand photography", "art direction", "shoot planning", "styling"],
        "featured": True,
        "popularity": 83,
    },
    {
        "slug": "horror-game-environment-prompt",
        "title": "Horror Game Environment Prompt",
        "summary": "Design an atmospheric horror game environment with lighting and tension cues.",
        "prompt": """Design a horror game environment for [setting: abandoned hospital / underground lab / Victorian manor / deep space station].

Requirements:
- Lighting should guide the player while creating dread: one safe zone, one danger zone, one unknown.
- Include environmental storytelling: 3 discoverable narrative details visible in the scene.
- Design sightlines that create anticipation (long corridors, blind corners, reflective surfaces).
- Specify audio design cues that pair with the visual: ambient, proximity, and jump triggers.
- Show one "before the horror" version and one "after something went wrong" version.

Return:
- environment concept
- lighting zones with gameplay function
- environmental storytelling inventory
- audio design pairing notes
- before/after comparison""",
        "model_slug": "stable-diffusion",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["horror", "game environment", "atmosphere", "level design", "narrative"],
        "featured": True,
        "popularity": 86,
    },
    {
        "slug": "typography-specimen-poster-prompt",
        "title": "Typography Specimen Poster Prompt",
        "summary": "Design a type specimen poster that showcases a font's personality and range.",
        "prompt": """Design a typography specimen poster for [font name or style description].

Requirements:
- Show the full character set: uppercase, lowercase, numerals, and key glyphs.
- Include the typeface at display, subheading, body, and caption sizes.
- Use one creative typographic composition that shows the font's personality.
- Include weight and style variations if available.
- The poster should work as both a reference tool and wall art.

Return:
- poster layout concept
- character showcase arrangement
- creative composition concept
- size and weight demonstrations
- print specification""",
        "model_slug": "recraft",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["typography", "specimen", "poster", "type design", "print"],
        "is_free": True,
        "popularity": 75,
    },
    {
        "slug": "ai-workflow-automation-prompt",
        "title": "AI Workflow Automation Prompt",
        "summary": "Design an AI-powered workflow that automates a repetitive business process.",
        "prompt": """Design an AI-powered automation workflow for [process: content review / lead qualification / support triage / invoice processing / hiring pipeline].

Requirements:
- Map the current manual workflow with time and cost estimates per step.
- Identify which steps can be fully automated, partially automated, or must stay human.
- Specify the AI models or tools needed for each automated step.
- Include error handling and human-in-the-loop escalation points.
- Calculate projected time savings and ROI.

Return:
- current workflow map with bottlenecks
- automated workflow design
- tool and model recommendations per step
- escalation and error handling rules
- ROI projection""",
        "model_slug": "gemini",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["automation", "workflow", "ai tools", "operations", "efficiency"],
        "featured": True,
        "popularity": 87,
    },
    {
        "slug": "comic-book-page-prompt",
        "title": "Comic Book Page Layout Prompt",
        "summary": "Design a dynamic comic book page with panel layout, action, and storytelling.",
        "prompt": """Design a comic book page for a [genre: superhero / noir / manga / sci-fi / slice-of-life] story.

Scene to depict: [describe the scene]

Requirements:
- Use 5-7 panels with varied sizes to control pacing and emphasis.
- Include one splash or dominant panel for the page's key moment.
- Panel compositions should guide the reader's eye through the page naturally.
- Show dynamic camera angles: at least one low angle, one close-up, and one wide.
- Leave appropriate space for speech bubbles and captions without crowding the art.

Return:
- panel layout with dimensions
- per-panel composition descriptions
- camera angle and shot type for each panel
- speech bubble placement zones
- page flow and pacing notes""",
        "model_slug": "leonardo-ai",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["comic book", "sequential art", "panel layout", "storytelling", "manga"],
        "featured": True,
        "popularity": 86,
    },
    {
        "slug": "startup-naming-brainstorm-prompt",
        "title": "Startup Naming Brainstorm Prompt",
        "summary": "Generate and evaluate startup name candidates with domain and trademark checks.",
        "prompt": """Generate 20 name candidates for a [industry] startup that [value proposition].

Target brand personality: [personality traits]
Target audience: [audience]

Requirements:
- Include a mix of: invented words, compound words, metaphors, and abbreviations.
- For each name, explain the linguistic logic and what it evokes.
- Flag likely domain availability (.com and .io).
- Rate each name on: memorability, pronunciation clarity, and trademark risk.
- Shortlist the top 5 with rationale.

Return:
- 20 name candidates with explanations
- domain availability assessment
- scoring matrix
- top 5 shortlist with rationale
- naming direction recommendations""",
        "model_slug": "grok",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["naming", "startup", "branding", "domain", "trademark"],
        "featured": True,
        "popularity": 88,
    },
    {
        "slug": "architectural-walkthrough-video-prompt",
        "title": "Architectural Walkthrough Video Prompt",
        "summary": "Generate a cinematic architectural walkthrough for a property or design concept.",
        "prompt": """Create a cinematic architectural walkthrough of [property type: modern villa / loft apartment / restaurant / boutique hotel] in [15-25 seconds].

Requirements:
- Begin outside with an establishing shot showing the building in its context.
- Transition through the entrance with a single continuous-feeling camera move.
- Reveal 3-4 key spaces with deliberate pauses on material details.
- Lighting should progress from natural exterior to designed interior.
- End on the signature space or view that sells the property.

Return:
- walkthrough path with room sequence
- camera movement and transition descriptions
- material and lighting callouts per space
- signature reveal moment
- music and ambient sound suggestions""",
        "model_slug": "hunyuan",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["architecture", "walkthrough", "real estate", "interior", "cinematic"],
        "featured": True,
        "popularity": 83,
    },
    {
        "slug": "unboxing-experience-video-prompt",
        "title": "Unboxing Experience Video Prompt",
        "summary": "Design a premium unboxing video that makes viewers feel the product quality.",
        "prompt": """Create a premium unboxing video for [product] in [12-20 seconds].

Requirements:
- ASMR-adjacent: emphasize tactile sounds, paper textures, and material reveals.
- Hands should interact with packaging deliberately, not rushed.
- Include one satisfying peel, fold, or magnetic closure moment.
- Lighting should make materials look premium: shadows, reflections, surface detail.
- Final product reveal should have a clear hero moment with breathing room.

Return:
- unboxing sequence with beats
- tactile moment highlights
- sound design notes
- lighting and camera setup
- hero reveal composition""",
        "model_slug": "seedream",
        "category_slug": "marketing-business",
        "modality": "video",
        "tags": ["unboxing", "product", "asmr", "premium", "ecommerce"],
        "popularity": 82,
    },
    {
        "slug": "character-turnaround-sheet-prompt",
        "title": "Character Turnaround Sheet Prompt",
        "summary": "Create a production-ready character turnaround for animation or game development.",
        "prompt": """Create a character turnaround sheet for [character description] in a [art style: anime / western animation / semi-realistic / chibi] style.

Requirements:
- Show front, three-quarter, side, and back views on a consistent baseline.
- Include a height reference and proportion grid.
- Add a color palette swatch with material callouts (skin, fabric, metal, etc.).
- Show 3-4 facial expression variants.
- Include one action pose that demonstrates the character's personality.

Return:
- turnaround views
- proportion and height reference
- color palette with material notes
- expression sheet
- action pose""",
        "model_slug": "wan",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["character design", "turnaround", "animation", "game dev", "model sheet"],
        "popularity": 80,
    },
    {
        "slug": "ecommerce-product-listing-prompt",
        "title": "E-commerce Product Listing Prompt",
        "summary": "Write a high-converting product listing with SEO-optimized copy and bullet points.",
        "prompt": """Write a product listing for [product name] sold on [platform: Amazon / Shopify / Etsy].

Product details: [key features, materials, dimensions, use cases]

Requirements:
- Title optimized for search with primary keyword naturally placed.
- 5 benefit-driven bullet points that address buyer objections.
- Product description that tells a story and builds desire, not just lists specs.
- Include backend search keywords and suggested A+ content sections.
- Write for the buyer who is comparing 3 tabs side by side.

Return:
- optimized title
- bullet points
- product description
- search keywords
- A+ content section suggestions""",
        "model_slug": "chatgpt",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["ecommerce", "product listing", "amazon", "seo", "copywriting"],
        "is_free": True,
        "featured": True,
        "popularity": 89,
    },
    {
        "slug": "motion-logo-reveal-prompt",
        "title": "Motion Logo Reveal Prompt",
        "summary": "Create an animated logo reveal for video intros, presentations, or brand content.",
        "prompt": """Create a motion logo reveal for [brand name] in [3-5 seconds].

Requirements:
- The animation should reflect the brand's personality: [playful / premium / technical / bold].
- Build from simple to complete, not just fade in.
- Include a subtle sound design moment (whoosh, click, tone) at the resolve.
- The logo must land on a clean, usable hold frame for at least 1 second.
- Show one alternate version: dark background and light background.

Return:
- animation sequence description
- build-up technique
- sound design beat
- hold frame composition
- dark/light variants""",
        "model_slug": "grok-video",
        "category_slug": "logo-icon",
        "modality": "video",
        "tags": ["logo animation", "motion", "brand", "intro", "reveal"],
        "featured": True,
        "popularity": 86,
    },
    {
        "slug": "vaporwave-aesthetic-prompt",
        "title": "Vaporwave Aesthetic Prompt",
        "summary": "Create a vaporwave or retrowave aesthetic piece with neon grids and surreal elements.",
        "prompt": """Create a vaporwave / retrowave artwork for [subject: album art / poster / social banner / desktop wallpaper].

Requirements:
- Classic vaporwave elements: chrome text, marble busts, neon grids, palm trees, sunset gradients.
- But push beyond cliché: add one unexpected modern element that makes it fresh.
- Color palette should center on magenta, cyan, and deep purple with chrome accents.
- Include glitch artifacts, scan lines, or VHS texture for authenticity.
- The composition should feel like a place you want to be, not just a meme.

Return:
- composition concept
- key visual elements
- unexpected fresh element
- color palette and texture treatment
- resolution and format notes""",
        "model_slug": "stable-diffusion",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["vaporwave", "retrowave", "aesthetic", "neon", "retro"],
        "popularity": 79,
    },
    {
        "slug": "ux-audit-report-prompt",
        "title": "UX Audit Report Prompt",
        "summary": "Conduct a structured UX audit of a product with prioritized recommendations.",
        "prompt": """Conduct a UX audit of [product or website URL description].

Requirements:
- Evaluate: information architecture, navigation, visual hierarchy, forms, CTAs, and mobile experience.
- Score each area on a 1-5 scale with specific evidence for each score.
- Identify the top 3 quick wins (high impact, low effort fixes).
- Identify the top 3 strategic improvements (high impact, higher effort).
- Include annotated screenshots descriptions showing exact problem areas.

Return:
- executive summary with overall score
- area-by-area assessment with scores
- quick wins with implementation notes
- strategic improvements with rationale
- prioritized recommendations matrix""",
        "model_slug": "gemini",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["ux audit", "design review", "usability", "product", "recommendations"],
        "featured": True,
        "popularity": 82,
    },
    {
        "slug": "generative-pattern-design-prompt",
        "title": "Generative Pattern Design Prompt",
        "summary": "Create a seamless repeating pattern for textiles, wallpaper, or packaging.",
        "prompt": """Design a seamless repeating pattern inspired by [theme: tropical botanicals / geometric art deco / Japanese wave motifs / microscopic organisms / circuit boards].

Requirements:
- The pattern must tile seamlessly in all directions.
- Include a hero colorway and two alternate colorways for different applications.
- Scale should work for both large format (wallpaper, fabric bolt) and small format (gift wrap, phone case).
- Balance density: not so sparse it looks empty, not so dense it overwhelms.
- Include one subtle motif variation that prevents the repeat from feeling mechanical.

Return:
- pattern tile design
- three colorways
- scale demonstration at different sizes
- repeat logic and variation notes
- application mockups (textile, packaging, digital)""",
        "model_slug": "qwen-image",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["pattern design", "textile", "seamless", "surface design", "wallpaper"],
        "popularity": 77,
    },
    {
        "slug": "crisis-communication-plan-prompt",
        "title": "Crisis Communication Plan Prompt",
        "summary": "Draft a crisis communication plan with holding statements and escalation protocols.",
        "prompt": """Create a crisis communication plan for [company] addressing a [crisis type: data breach / product recall / PR incident / executive misconduct / service outage].

Requirements:
- Write 3 holding statements for different stages: first 30 minutes, first 4 hours, next day.
- Define the approval chain and spokesperson hierarchy.
- Include templates for: press statement, customer email, social media post, and internal memo.
- Map stakeholder communication priority and channel.
- Include a "what not to say" section with common mistakes.

Return:
- holding statements (3 stages)
- approval and spokesperson protocol
- communication templates per channel
- stakeholder priority matrix
- common mistakes to avoid""",
        "model_slug": "llama",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["crisis communication", "pr", "reputation", "stakeholder", "emergency"],
        "popularity": 76,
    },
    {
        "slug": "timelapse-nature-video-prompt",
        "title": "Timelapse Nature Video Prompt",
        "summary": "Create a mesmerizing nature timelapse with dynamic sky and landscape movement.",
        "prompt": """Create a nature timelapse video of [subject: cloud formations over mountains / flower blooming / ice melting / starfield rotation / city sunrise] in [8-15 seconds].

Requirements:
- The passage of time should feel dramatic and awe-inspiring.
- Include one foreground anchor element for depth and scale.
- Lighting transition should be the emotional core: sunrise, sunset, or day-to-night.
- Camera should be locked or have one very slow pan/tilt for gentle dynamism.
- The final frame should feel like a photograph worth printing.

Return:
- scene composition
- time compression ratio
- foreground anchor element
- lighting transition arc
- final frame description""",
        "model_slug": "seedance",
        "category_slug": "photography",
        "modality": "video",
        "tags": ["timelapse", "nature", "landscape", "sky", "cinematic"],
        "popularity": 78,
    },
    {
        "slug": "lesson-plan-generator-prompt",
        "title": "Lesson Plan Generator Prompt",
        "summary": "Create a structured lesson plan with activities, assessments, and differentiation.",
        "prompt": """Create a lesson plan for teaching [topic] to [grade level / audience] in a [duration] session.

Requirements:
- Include a hook activity that sparks curiosity in the first 5 minutes.
- Structure the lesson with: warm-up, direct instruction, guided practice, independent work, and debrief.
- Provide differentiation strategies for advanced, on-level, and struggling learners.
- Include one formative assessment check and one summative assessment option.
- Add real-world connections that make the topic feel relevant to students' lives.

Return:
- lesson overview and objectives
- detailed timeline with activities
- differentiation strategies
- assessment tools
- materials list and prep notes""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["lesson plan", "education", "teaching", "curriculum", "learning"],
        "is_free": True,
        "popularity": 83,
    },
    {
        "slug": "rpg-dungeon-map-prompt",
        "title": "RPG Dungeon Map Prompt",
        "summary": "Design a tabletop RPG dungeon map with encounters, secrets, and narrative flow.",
        "prompt": """Design a dungeon map for a [theme: haunted crypt / dwarven forge / arcane library / sunken temple / dragon's lair] suitable for [party level] adventurers.

Requirements:
- 8-12 rooms with distinct visual identity and gameplay purpose.
- Include 2 combat encounter rooms, 1 puzzle room, 1 trap corridor, and 1 treasure room.
- Add 2 hidden areas that reward exploration or investigation checks.
- The map should have multiple paths so players feel agency in their route.
- Include environmental hazards that interact with the dungeon's theme.

Return:
- dungeon map layout
- room-by-room descriptions with encounters
- secret areas and discovery conditions
- environmental hazard notes
- boss room setup and narrative climax""",
        "model_slug": "grok-image",
        "category_slug": "games-3d",
        "modality": "image",
        "tags": ["dungeon map", "rpg", "tabletop", "fantasy", "encounter design"],
        "popularity": 80,
    },
    {
        "slug": "micro-saas-launch-strategy-prompt",
        "title": "Micro-SaaS Launch Strategy Prompt",
        "summary": "Plan a complete launch strategy for a micro-SaaS product from beta to first 100 customers.",
        "prompt": """Create a launch strategy for [product name], a micro-SaaS tool that [what it does] for [target customer].

Current stage: [pre-launch / beta / just launched]
Budget: [bootstrapped / small budget / funded]

Requirements:
- Define the launch in phases: pre-launch, launch week, and post-launch growth.
- Identify the 3 highest-leverage distribution channels for this specific audience.
- Include a pricing strategy with specific tier recommendations and reasoning.
- Plan the first 30 days of content and community engagement.
- Set concrete metrics for each phase: not vanity metrics, real business outcomes.

Return:
- phase-by-phase launch plan
- channel strategy with prioritization
- pricing recommendation with tiers
- 30-day content and engagement calendar
- metrics and milestones per phase""",
        "model_slug": "deepseek",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["micro saas", "launch strategy", "startup", "growth", "pricing"],
        "is_free": True,
        "featured": True,
        "popularity": 85,
    },
    {
        "slug": "surreal-dreamscape-prompt",
        "title": "Surreal Dreamscape Prompt",
        "summary": "Create a surrealist artwork that bends reality with impossible architecture and symbolism.",
        "prompt": """Create a surrealist dreamscape painting inspired by [theme: memory / time / identity / technology / nature reclaiming civilization].

Requirements:
- Blend at least two impossible spatial relationships (Escher-like gravity, recursive spaces, scale contradictions).
- Include one recognizable everyday object transformed into something uncanny.
- Lighting should feel both natural and wrong simultaneously.
- The composition should have a clear focal point despite the surreal chaos.
- Color palette should evoke a specific emotional temperature: warm nostalgia, cold alienation, or electric wonder.

Return:
- scene concept and central metaphor
- spatial impossibility descriptions
- transformed object concept
- lighting and color direction
- emotional interpretation notes""",
        "model_slug": "midjourney",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["surrealism", "dreamscape", "impossible", "art", "conceptual"],
        "popularity": 84,
    },
    {
        "slug": "landing-page-roast-prompt",
        "title": "Landing Page Roast Prompt",
        "summary": "Get a brutally honest review of a landing page with specific fix recommendations.",
        "prompt": """Roast this landing page and tell me exactly what to fix.

Page description: [describe your landing page: headline, subhead, hero image, sections, CTA, etc.]
Target audience: [who you're trying to convert]
Goal: [sign up / buy / book a demo / download]

Requirements:
- Be brutally honest. If the headline is vague, say so. If the CTA is weak, call it out.
- Grade each section: headline, subhead, hero visual, social proof, features, objection handling, CTA.
- For every criticism, give a specific rewrite or fix suggestion.
- Identify the single biggest conversion killer on the page.
- End with a prioritized fix list: what to change today, this week, and this month.

Return:
- section-by-section roast with grades
- specific rewrite suggestions
- biggest conversion killer
- prioritized fix list
- one example of a page in this category that does it well""",
        "model_slug": "grok",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["landing page", "conversion", "roast", "cro", "copywriting"],
        "featured": True,
        "popularity": 91,
    },
    {
        "slug": "vintage-travel-poster-prompt",
        "title": "Vintage Travel Poster Prompt",
        "summary": "Design a vintage-style travel poster with retro illustration and bold typography.",
        "prompt": """Design a vintage travel poster for [destination] in the style of [era: 1920s Art Deco / 1950s mid-century / 1960s airline / WPA national parks].

Requirements:
- Capture the destination's most iconic visual element in a simplified, graphic style.
- Typography should feel hand-lettered and era-authentic.
- Use a limited color palette of 4-6 flat colors with overprint effects.
- Include a tagline or slogan that captures the spirit of the destination.
- The poster should work as both a travel promotion and collectible wall art.

Return:
- poster illustration concept
- typography treatment and tagline
- color palette with printing notes
- era-specific style details
- print size and paper recommendation""",
        "model_slug": "google-imagen",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["vintage poster", "travel", "retro", "illustration", "typography"],
        "popularity": 82,
    },
    {
        "slug": "saas-onboarding-email-sequence-prompt",
        "title": "SaaS Onboarding Email Sequence Prompt",
        "summary": "Write a behavior-triggered email sequence that drives new users to activation.",
        "prompt": """Write a 7-email onboarding sequence for [product name], a [product type] where activation means [define activation event].

Requirements:
- Email 1: Welcome + single most important first action (sent immediately).
- Emails 2-4: Behavior-triggered based on whether they completed key actions or not.
- Email 5: Social proof and use case inspiration.
- Email 6: Address the #1 reason users churn early.
- Email 7: Personal check-in from founder or success team.
- Each email should have one CTA, not three.

Return:
- email sequence map with triggers
- subject lines and preview text
- full email copy for all 7 emails
- send timing and trigger logic
- metrics to track per email""",
        "model_slug": "claude",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["onboarding", "email sequence", "saas", "activation", "retention"],
        "featured": True,
        "popularity": 88,
    },
    {
        "slug": "vehicle-wrap-design-prompt",
        "title": "Vehicle Wrap Design Prompt",
        "summary": "Design a vehicle wrap for a van, truck, or fleet that turns heads and communicates.",
        "prompt": """Design a vehicle wrap for a [vehicle type: delivery van / food truck / company car / fleet vehicle] for [brand name], a [business type].

Requirements:
- The brand name and phone/URL must be readable at 40mph from 30 feet.
- Design must account for door handles, windows, wheel wells, and panel seams.
- Use one hero visual element that makes the vehicle recognizable from any angle.
- Include both side panel and rear door designs.
- The wrap should make someone pull out their phone to look up the business.

Return:
- side panel design
- rear door design
- hero visual element concept
- readability and distance notes
- color and material specification""",
        "model_slug": "flux",
        "category_slug": "graphic-design",
        "modality": "image",
        "tags": ["vehicle wrap", "fleet", "outdoor advertising", "branding", "signage"],
        "popularity": 73,
    },
    {
        "slug": "ai-art-style-mashup-prompt",
        "title": "AI Art Style Mashup Prompt",
        "summary": "Combine two unexpected art styles or movements into a single cohesive piece.",
        "prompt": """Create an artwork that fuses [Style A: e.g., Japanese ukiyo-e] with [Style B: e.g., cyberpunk neon] depicting [subject].

Requirements:
- Both styles should be recognizably present, not one overwhelming the other.
- Find a visual logic for how these two aesthetics coexist (shared geometry, complementary palettes, transitional zones).
- The subject should feel natural in this hybrid world, not pasted on.
- Include enough detail from each style that a knowledgeable viewer could identify both influences.
- The piece should look intentional, not like a glitch or accident.

Return:
- composition concept
- style fusion logic
- key elements from each style
- color harmony approach
- one sentence artist statement""",
        "model_slug": "midjourney",
        "category_slug": "art-illustration",
        "modality": "image",
        "tags": ["style mashup", "fusion", "art direction", "creative", "experimental"],
        "featured": True,
        "popularity": 89,
    },
    {
        "slug": "tiktok-content-strategy-prompt",
        "title": "TikTok Content Strategy Prompt",
        "summary": "Build a TikTok content strategy with formats, hooks, and posting cadence.",
        "prompt": """Create a TikTok content strategy for [brand or creator] in the [niche] space.

Current situation: [follower count, posting frequency, what's working or not]

Requirements:
- Define 4-5 repeatable content formats (series, templates, recurring hooks).
- For each format, include: hook formula, structure, ideal length, and example topic.
- Map content to the funnel: awareness, engagement, and conversion.
- Include a posting cadence recommendation with best times for this niche.
- Identify 3 trending formats to adapt and 3 formats to avoid.

Return:
- content format library with examples
- hook formulas per format
- posting cadence and timing
- funnel mapping
- trends to ride and avoid""",
        "model_slug": "grok",
        "category_slug": "marketing-business",
        "modality": "text",
        "tags": ["tiktok", "content strategy", "social media", "short form", "creator"],
        "featured": True,
        "popularity": 90,
    },
    {
        "slug": "minimalist-logo-one-line-prompt",
        "title": "Minimalist One-Line Logo Prompt",
        "summary": "Design a logo using a single continuous line that captures the brand essence.",
        "prompt": """Design a minimalist logo for [brand name] using a single continuous line or minimal stroke count.

Requirements:
- The entire mark should feel like it was drawn without lifting the pen (or nearly so).
- The line must form a recognizable symbol related to the brand's offering.
- Works in monochrome at any size from favicon to billboard.
- Include one version with the line forming negative space to create a second reading.
- Show the logo in three contexts: business card, app icon, and embossed on paper.

Return:
- primary line logo concept
- negative space variant
- three application mockups
- line weight specification
- construction grid""",
        "model_slug": "ideogram",
        "category_slug": "logo-icon",
        "modality": "image",
        "tags": ["minimalist", "one line", "logo", "mark", "continuous"],
        "popularity": 81,
    },
    {
        "slug": "podcast-episode-show-notes-prompt",
        "title": "Podcast Episode Show Notes Prompt",
        "summary": "Transform a podcast episode transcript into rich show notes with timestamps and takeaways.",
        "prompt": """Create comprehensive show notes for a podcast episode.

Episode title: [title]
Guest: [guest name and bio]
Transcript or summary: [paste content]

Requirements:
- Write a compelling episode description that works as both a podcast app summary and blog post intro.
- Create timestamped chapter markers for key topic shifts.
- Extract the 5 most quotable moments with exact timestamps.
- List all resources, tools, books, or links mentioned.
- Write 3 social media clips: one provocative take, one actionable tip, one surprising fact.

Return:
- episode description (150 words)
- timestamped chapters
- key quotes with timestamps
- resources and links mentioned
- 3 social media clips""",
        "model_slug": "llama",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["podcast", "show notes", "transcript", "content repurposing", "timestamps"],
        "popularity": 77,
    },
    {
        "slug": "3d-product-render-prompt",
        "title": "3D Product Render Prompt",
        "summary": "Create a photorealistic 3D product render for marketing and ecommerce.",
        "prompt": """Create a photorealistic 3D product render of [product] for [use: ecommerce listing / social ad / hero banner / packaging].

Requirements:
- Material rendering should be physically accurate: metal reflections, plastic translucency, fabric weave.
- Include one hero angle, one detail crop, and one lifestyle context placement.
- Lighting should be studio-quality with controlled highlights and shadows.
- Background should complement but not compete with the product.
- Show one exploded view or cutaway if the product has internal complexity.

Return:
- hero render angle and setup
- detail crop concept
- lifestyle placement scene
- material and lighting specifications
- optional exploded view""",
        "model_slug": "leonardo-ai",
        "category_slug": "photography",
        "modality": "image",
        "tags": ["3d render", "product visualization", "cgi", "ecommerce", "marketing"],
        "popularity": 79,
    },
    {
        "slug": "daily-standup-summary-prompt",
        "title": "Daily Standup Summary Prompt",
        "summary": "Turn messy standup notes into a clear async update for distributed teams.",
        "prompt": """Transform these daily standup notes into a clear async team update.

Team notes: [paste raw standup notes from multiple team members]

Requirements:
- Group updates by workstream, not by person.
- Highlight blockers prominently at the top.
- Flag items where two people's work might conflict or depend on each other.
- Keep each update to one line maximum.
- Add a "needs attention" section for anything that looks at risk.

Return:
- blockers (urgent, at top)
- workstream updates
- dependency alerts
- needs attention flags
- one-line team momentum summary""",
        "model_slug": "chatgpt",
        "category_slug": "productivity-writing",
        "modality": "text",
        "tags": ["standup", "async", "team update", "project management", "remote work"],
        "is_free": True,
        "popularity": 78,
    },
]


AUTO_PROMPT_TARGET = 1000
IMAGE_MODEL_SLUGS = [slug for slug, meta in MODELS.items() if meta["modality"] == "image"]
TEXT_MODEL_SLUGS = [slug for slug, meta in MODELS.items() if meta["modality"] == "text"]
VIDEO_MODEL_SLUGS = [slug for slug, meta in MODELS.items() if meta["modality"] == "video"]
FREE_MODEL_SLUGS = {"chatgpt", "deepseek", "stable-diffusion", "recraft", "chatgpt-image"}

IMAGE_PROMPT_VARIANTS = [
    {
        "slug": "hero",
        "title": "Hero Direction",
        "focus": "a bold hero composition that makes the concept obvious in one glance",
        "tag": "hero",
    },
    {
        "slug": "system",
        "title": "System Direction",
        "focus": "a repeatable design system that can extend into multiple touchpoints",
        "tag": "system",
    },
    {
        "slug": "premium",
        "title": "Premium Direction",
        "focus": "a more premium, high-polish execution with stronger materials, lighting, or finish",
        "tag": "premium",
    },
]

TEXT_PROMPT_VARIANTS = [
    {
        "slug": "strategic",
        "title": "Strategic",
        "focus": "show reasoning, tradeoffs, and why each recommendation matters",
        "tag": "strategy",
    },
    {
        "slug": "concise",
        "title": "Concise",
        "focus": "keep the output tight, operator-friendly, and fast to scan",
        "tag": "concise",
    },
    {
        "slug": "operator",
        "title": "Operator",
        "focus": "bias toward execution detail, owners, next steps, and implementation clarity",
        "tag": "operations",
    },
]

VIDEO_PROMPT_VARIANTS = [
    {
        "slug": "cinematic",
        "title": "Cinematic",
        "focus": "lean into premium motion, lighting, and camera language",
        "tag": "cinematic",
    },
    {
        "slug": "social",
        "title": "Social",
        "focus": "optimize pacing and framing for social-first performance",
        "tag": "social",
    },
    {
        "slug": "explain",
        "title": "Explainer",
        "focus": "keep the motion easy to follow with clean storytelling beats",
        "tag": "explainer",
    },
]

IMAGE_PROMPT_BLUEPRINTS = [
    {
        "slug": "brand-avatar-system",
        "title": "Brand Avatar System",
        "summary": "Create a branded avatar and profile system for a new product or community.",
        "category_slug": "logo-icon",
        "subject": "a recognizable avatar and profile-image system",
        "objective": "make the brand memorable in tiny profile placements and social thumbnails",
        "requirements": [
            "keep the silhouette legible at 48px",
            "show one icon-first option and one wordmark-supported option",
            "make it feel original rather than derivative of existing platform marks",
        ],
        "deliverables": ["primary direction", "small-size usage note", "palette recommendation"],
        "tags": ["avatar", "social brand", "identity"],
        "base_popularity": 68,
    },
    {
        "slug": "app-splash-art",
        "title": "App Splash Art",
        "summary": "Generate splash art for a mobile app launch or onboarding sequence.",
        "category_slug": "graphic-design",
        "subject": "a launch-ready splash screen visual",
        "objective": "make the app category and mood obvious before the interface loads",
        "requirements": [
            "leave enough negative space for app name and subtitle",
            "use shapes and lighting that feel native to a mobile launch screen",
            "keep the composition clean enough for both portrait and story crops",
        ],
        "deliverables": ["hero composition", "background treatment", "portrait crop note"],
        "tags": ["splash screen", "app launch", "mobile"],
        "base_popularity": 66,
    },
    {
        "slug": "founder-billboard-portrait",
        "title": "Founder Billboard Portrait",
        "summary": "Create a large-format founder portrait for press, keynotes, or campaigns.",
        "category_slug": "photography",
        "subject": "a high-confidence founder portrait",
        "objective": "make the founder feel credible, modern, and campaign-ready",
        "requirements": [
            "avoid generic stock-photo energy",
            "make the background subtly reference the company category",
            "keep the crop flexible for keynote slides and press headers",
        ],
        "deliverables": ["portrait setup", "wardrobe note", "crop guidance"],
        "tags": ["founder", "portrait", "campaign"],
        "base_popularity": 65,
    },
    {
        "slug": "product-comparison-board",
        "title": "Product Comparison Board",
        "summary": "Design a clean side-by-side product comparison visual for marketing pages.",
        "category_slug": "graphic-design",
        "subject": "a side-by-side comparison board for competing product tiers or offers",
        "objective": "help a buyer understand differences in seconds",
        "requirements": [
            "keep information hierarchy obvious from a distance",
            "use shape, contrast, and spacing to guide the eye",
            "make the board suitable for pricing pages, decks, or paid ads",
        ],
        "deliverables": ["comparison layout", "hierarchy note", "contrast guidance"],
        "tags": ["comparison", "offer design", "marketing"],
        "base_popularity": 63,
    },
    {
        "slug": "packaging-lineup",
        "title": "Packaging Lineup",
        "summary": "Create a packaging family that can support multiple SKUs or variants.",
        "category_slug": "graphic-design",
        "subject": "a multi-SKU packaging lineup",
        "objective": "make the family feel unified while each SKU stays distinct",
        "requirements": [
            "show how color and labeling separate variants",
            "keep the shelf read strong in a group shot",
            "include one hero SKU and supporting secondary packs",
        ],
        "deliverables": ["family direction", "variant logic", "shelf-impact note"],
        "tags": ["packaging", "sku system", "retail"],
        "base_popularity": 62,
    },
    {
        "slug": "landing-page-illustration",
        "title": "Landing Page Illustration",
        "summary": "Generate a polished landing-page illustration for a business or product.",
        "category_slug": "art-illustration",
        "subject": "a landing-page illustration with product storytelling value",
        "objective": "support a strong homepage headline without overwhelming the copy",
        "requirements": [
            "leave clear headline space for a left- or right-aligned layout",
            "use one central metaphor tied to the business outcome",
            "keep the rendering polished enough for a modern SaaS homepage",
        ],
        "deliverables": ["scene direction", "metaphor note", "layout guidance"],
        "tags": ["landing page", "illustration", "saas"],
        "base_popularity": 67,
    },
    {
        "slug": "mascot-sticker-sheet",
        "title": "Mascot Sticker Sheet",
        "summary": "Create a mascot-based sticker sheet for community and growth loops.",
        "category_slug": "logo-icon",
        "subject": "a mascot sticker sheet with reusable expressions and poses",
        "objective": "make the mascot flexible across community rewards, merch, and retention loops",
        "requirements": [
            "show a base mascot plus multiple emotional variants",
            "keep forms readable at chat-size and merch-size",
            "make the character original, ownable, and digitally native",
        ],
        "deliverables": ["mascot design", "expression set", "usage note"],
        "tags": ["mascot", "stickers", "community"],
        "base_popularity": 61,
    },
    {
        "slug": "webinar-cover-art",
        "title": "Webinar Cover Art",
        "summary": "Design cover art for a webinar, livestream, or educational event.",
        "category_slug": "graphic-design",
        "subject": "a webinar cover layout",
        "objective": "make the topic feel premium and worth registering for",
        "requirements": [
            "leave space for speaker name, topic, and registration callout",
            "make the layout flexible across event pages and social crops",
            "use typography and motion-friendly composition cues",
        ],
        "deliverables": ["cover concept", "type hierarchy", "cross-channel crop note"],
        "tags": ["webinar", "cover art", "events"],
        "base_popularity": 58,
    },
    {
        "slug": "icon-pack-system",
        "title": "Icon Pack System",
        "summary": "Create a clean icon pack for product, docs, or onboarding surfaces.",
        "category_slug": "logo-icon",
        "subject": "a tightly controlled icon system",
        "objective": "make the icon language feel cohesive across product and marketing surfaces",
        "requirements": [
            "keep stroke and radius decisions consistent",
            "show how icons work at 20px and 32px",
            "avoid over-detail that breaks at small sizes",
        ],
        "deliverables": ["style direction", "sample icon list", "spacing note"],
        "tags": ["icon pack", "design system", "ui"],
        "base_popularity": 64,
    },
    {
        "slug": "dashboard-hero-visual",
        "title": "Dashboard Hero Visual",
        "summary": "Generate a dashboard-led hero visual for a product launch or sales page.",
        "category_slug": "graphic-design",
        "subject": "a dashboard-led hero composition",
        "objective": "make the product outcome and data story instantly clear",
        "requirements": [
            "highlight one core insight rather than every widget",
            "mix interface detail with a clear focal path",
            "keep the scene usable on marketing pages and deck covers",
        ],
        "deliverables": ["dashboard focal point", "layout note", "supporting background detail"],
        "tags": ["dashboard", "hero", "b2b"],
        "base_popularity": 66,
    },
    {
        "slug": "event-booth-backdrop",
        "title": "Event Booth Backdrop",
        "summary": "Create a trade show or conference booth backdrop with strong brand read.",
        "category_slug": "graphic-design",
        "subject": "a booth backdrop and stage-friendly brand wall",
        "objective": "make the brand visible from distance while still photographing well",
        "requirements": [
            "optimize for both in-person read and camera framing",
            "show one focal message and one supporting visual motif",
            "make the backdrop compatible with booth furniture and lighting",
        ],
        "deliverables": ["backdrop direction", "distance-read note", "photo moment suggestion"],
        "tags": ["events", "booth", "conference"],
        "base_popularity": 57,
    },
    {
        "slug": "architecture-concept-board",
        "title": "Architecture Concept Board",
        "summary": "Generate a concept board for a commercial, retail, or hospitality space.",
        "category_slug": "art-illustration",
        "subject": "an architectural concept board",
        "objective": "communicate material mood and spatial direction quickly",
        "requirements": [
            "include scale, materiality, and atmosphere in one board",
            "balance realism with concept-level clarity",
            "make the board suitable for client review or pitch work",
        ],
        "deliverables": ["space direction", "material palette", "client-review note"],
        "tags": ["architecture", "concept board", "hospitality"],
        "base_popularity": 55,
    },
    {
        "slug": "game-key-art-system",
        "title": "Game Key Art System",
        "summary": "Generate marketable key art for a game launch, wishlist push, or pitch.",
        "category_slug": "games-3d",
        "subject": "a launch-ready game key art direction",
        "objective": "make the game world feel memorable in store thumbnails and banners",
        "requirements": [
            "include a clear focal subject and scale cue",
            "design for storefront, banner, and social promo crops",
            "keep the mood cinematic and commercially readable",
        ],
        "deliverables": ["key art direction", "thumbnail crop note", "lighting mood"],
        "tags": ["game art", "key art", "launch"],
        "base_popularity": 67,
    },
    {
        "slug": "course-thumbnail-series",
        "title": "Course Thumbnail Series",
        "summary": "Create a thumbnail system for courses, lessons, or educational products.",
        "category_slug": "graphic-design",
        "subject": "a multi-thumbnail educational cover system",
        "objective": "make episodes look consistent while topics stay easy to differentiate",
        "requirements": [
            "show clear topic hierarchy and numbering logic",
            "keep the covers legible on mobile and desktop grids",
            "balance personality with instructional clarity",
        ],
        "deliverables": ["cover system", "topic differentiation note", "grid-view guidance"],
        "tags": ["thumbnail", "course", "education"],
        "base_popularity": 56,
    },
]

TEXT_PROMPT_BLUEPRINTS = [
    {
        "slug": "executive-memo",
        "title": "Executive Memo",
        "summary": "Turn a messy situation into a decision-ready executive memo.",
        "category_slug": "productivity-writing",
        "task": "an executive memo for [topic or initiative]",
        "objective": "help leadership understand what changed, why it matters, and what to decide",
        "requirements": [
            "separate confirmed facts from assumptions",
            "surface risks and tradeoffs clearly",
            "end with a recommendation and next-step decision",
        ],
        "outputs": ["summary", "key facts", "risks", "recommendation"],
        "tags": ["memo", "leadership", "decision"],
        "base_popularity": 66,
    },
    {
        "slug": "landing-page-headline-set",
        "title": "Landing Page Headline Set",
        "summary": "Generate landing-page headlines and hero copy for a new offer.",
        "category_slug": "marketing-business",
        "task": "a landing-page hero section for [offer]",
        "objective": "make the value proposition obvious fast enough to improve conversion",
        "requirements": [
            "write multiple headline angles rather than one safe line",
            "include subhead, proof cue, and CTA direction",
            "avoid vague startup clichés",
        ],
        "outputs": ["headline options", "subhead options", "proof cue", "cta suggestions"],
        "tags": ["landing page", "headline", "conversion"],
        "base_popularity": 68,
    },
    {
        "slug": "cold-outreach-sequence",
        "title": "Cold Outreach Sequence",
        "summary": "Write an outbound sequence for a service, software, or partnership offer.",
        "category_slug": "marketing-business",
        "task": "a 4-step outbound sequence for [offer]",
        "objective": "open more conversations without sounding spammy or generic",
        "requirements": [
            "give each step a clear purpose and CTA",
            "use natural subject lines and believable proof",
            "include one respectful breakup email",
        ],
        "outputs": ["subject lines", "email bodies", "cta notes", "personalization ideas"],
        "tags": ["outbound", "email", "sales"],
        "base_popularity": 67,
    },
    {
        "slug": "customer-research-synthesis",
        "title": "Customer Research Synthesis",
        "summary": "Turn raw customer interviews into themes, quotes, and actions.",
        "category_slug": "productivity-writing",
        "task": "a synthesis of customer interviews or call notes",
        "objective": "identify repeat pain points, language patterns, and product opportunities",
        "requirements": [
            "cluster findings into themes",
            "pull useful verbatim quotes",
            "end with concrete product and messaging implications",
        ],
        "outputs": ["themes", "quotes", "opportunities", "open questions"],
        "tags": ["research", "synthesis", "voice of customer"],
        "base_popularity": 65,
    },
    {
        "slug": "pricing-page-copy",
        "title": "Pricing Page Copy",
        "summary": "Write pricing-page copy that reduces friction and clarifies plan choice.",
        "category_slug": "marketing-business",
        "task": "copy for a pricing page with multiple plans",
        "objective": "help the buyer understand what each plan is for and why they should upgrade",
        "requirements": [
            "differentiate plans clearly",
            "handle objections around price and fit",
            "include faq and proof snippets",
        ],
        "outputs": ["plan positioning", "supporting copy", "faq ideas", "upgrade nudges"],
        "tags": ["pricing", "copy", "saas"],
        "base_popularity": 64,
    },
    {
        "slug": "case-study-outline",
        "title": "Case Study Outline",
        "summary": "Create a case study outline from raw project or customer notes.",
        "category_slug": "marketing-business",
        "task": "a case study outline for [customer or project]",
        "objective": "turn scattered outcomes into a persuasive before-and-after narrative",
        "requirements": [
            "focus on concrete results and proof",
            "structure the story for website and sales-team reuse",
            "identify missing evidence that still needs to be collected",
        ],
        "outputs": ["story outline", "proof checklist", "quote requests", "cta angle"],
        "tags": ["case study", "proof", "sales enablement"],
        "base_popularity": 62,
    },
    {
        "slug": "onboarding-flow-copy",
        "title": "Onboarding Flow Copy",
        "summary": "Write onboarding copy for activation, setup, and first-value flows.",
        "category_slug": "productivity-writing",
        "task": "copy for the first-run onboarding flow of [product]",
        "objective": "get the user to first value with less friction and better clarity",
        "requirements": [
            "cover welcome, setup, progress, empty state, and success moments",
            "keep the language interface-friendly",
            "offer one more playful variant if the brand allows it",
        ],
        "outputs": ["screen copy", "tooltip copy", "success states", "tone note"],
        "tags": ["onboarding", "ux writing", "activation"],
        "base_popularity": 63,
    },
    {
        "slug": "support-macro-library",
        "title": "Support Macro Library",
        "summary": "Generate support macros for common tickets and edge cases.",
        "category_slug": "productivity-writing",
        "task": "a support-macro library for [product or service]",
        "objective": "help support stay fast without losing tone or clarity",
        "requirements": [
            "cover common questions, delays, bugs, and billing issues",
            "keep each response empathetic and specific",
            "include escalation triggers where needed",
        ],
        "outputs": ["macro list", "escalation notes", "tone guardrails", "qa checklist"],
        "tags": ["support", "macros", "operations"],
        "base_popularity": 60,
    },
    {
        "slug": "prd-outline",
        "title": "PRD Outline",
        "summary": "Create a practical product requirements outline from rough feature notes.",
        "category_slug": "productivity-writing",
        "task": "a lightweight PRD for [feature or initiative]",
        "objective": "make the feature easy to discuss across product, design, and engineering",
        "requirements": [
            "define problem, audience, constraints, and success criteria",
            "note risks and unknowns explicitly",
            "keep the outline lean enough for real team usage",
        ],
        "outputs": ["problem statement", "requirements", "risks", "success metrics"],
        "tags": ["prd", "product", "planning"],
        "base_popularity": 61,
    },
    {
        "slug": "launch-plan",
        "title": "Launch Plan",
        "summary": "Turn a release idea into a compact launch plan with owners and workstreams.",
        "category_slug": "marketing-business",
        "task": "a launch plan for [release, feature, or product]",
        "objective": "coordinate product, marketing, sales, and support work around one release",
        "requirements": [
            "identify workstreams, owners, and timing",
            "flag dependencies and go-live risks",
            "include internal comms and external comms",
        ],
        "outputs": ["workstreams", "owners", "timeline", "risk register"],
        "tags": ["launch plan", "go to market", "coordination"],
        "base_popularity": 66,
    },
    {
        "slug": "webinar-script-outline",
        "title": "Webinar Script Outline",
        "summary": "Generate a webinar structure that balances education, proof, and CTA.",
        "category_slug": "marketing-business",
        "task": "a webinar or livestream outline for [topic]",
        "objective": "keep the session useful enough to hold attention while still driving a next step",
        "requirements": [
            "open with a relevant hook and clear agenda",
            "mix teaching, examples, and proof moments",
            "end with a CTA that fits the session value",
        ],
        "outputs": ["agenda", "teaching beats", "proof moments", "cta"],
        "tags": ["webinar", "script", "education"],
        "base_popularity": 58,
    },
    {
        "slug": "social-calendar",
        "title": "Social Calendar",
        "summary": "Build a social content calendar around launches, themes, and repurposing.",
        "category_slug": "marketing-business",
        "task": "a monthly social content calendar for [brand]",
        "objective": "turn one strategy into repeatable weekly publishing ideas",
        "requirements": [
            "balance education, proof, story, and conversion posts",
            "make repurposing paths obvious",
            "note where visuals, clips, or founders should appear",
        ],
        "outputs": ["weekly themes", "post ideas", "repurposing notes", "cta ideas"],
        "tags": ["social media", "calendar", "content ops"],
        "base_popularity": 59,
    },
]

VIDEO_PROMPT_BLUEPRINTS = [
    {
        "slug": "product-teaser",
        "title": "Product Teaser",
        "summary": "Create a short teaser that builds anticipation before a launch or reveal.",
        "category_slug": "marketing-business",
        "subject": "a short product teaser for [product or launch]",
        "objective": "build anticipation before the full reveal",
        "requirements": [
            "use one reveal shot, one detail moment, and one payoff shot",
            "leave space for a title card or launch date",
            "make the motion feel premium rather than generic",
        ],
        "deliverables": ["shot list", "camera guidance", "timing note"],
        "tags": ["teaser", "launch", "motion"],
        "base_popularity": 68,
    },
    {
        "slug": "ugc-ad",
        "title": "UGC Ad",
        "summary": "Generate a short UGC ad concept with creator-style pacing and proof.",
        "category_slug": "marketing-business",
        "subject": "a short UGC-style ad for [product or offer]",
        "objective": "help a paid-social viewer understand the hook before they scroll away",
        "requirements": [
            "start with a strong first-second hook",
            "mix selfie framing with cutaway b-roll",
            "end on a clear CTA beat",
        ],
        "deliverables": ["beat-by-beat structure", "caption cue", "cta ending"],
        "tags": ["ugc", "ads", "paid social"],
        "base_popularity": 67,
    },
    {
        "slug": "app-walkthrough",
        "title": "App Walkthrough",
        "summary": "Create a product walkthrough that shows a core workflow clearly.",
        "category_slug": "marketing-business",
        "subject": "a fast app walkthrough for [product]",
        "objective": "show the product's main value without over-explaining",
        "requirements": [
            "highlight one core workflow rather than every feature",
            "make the UI motion readable on mobile",
            "finish on a product name or CTA frame",
        ],
        "deliverables": ["scene order", "ui moments", "ending frame"],
        "tags": ["walkthrough", "app", "saas"],
        "base_popularity": 66,
    },
    {
        "slug": "founder-intro",
        "title": "Founder Intro",
        "summary": "Generate a founder-introduction clip for websites, about pages, or paid media.",
        "category_slug": "marketing-business",
        "subject": "a short founder-introduction clip for [brand]",
        "objective": "make the founder feel clear, credible, and human quickly",
        "requirements": [
            "mix speaking-to-camera with contextual cutaways",
            "keep the tone warm but specific",
            "end with a simple line or CTA frame",
        ],
        "deliverables": ["opening hook", "cutaway ideas", "closing line"],
        "tags": ["founder", "brand video", "intro"],
        "base_popularity": 60,
    },
    {
        "slug": "event-recap",
        "title": "Event Recap",
        "summary": "Create a quick recap reel for a conference, meetup, or launch event.",
        "category_slug": "marketing-business",
        "subject": "a fast event recap reel",
        "objective": "make the event feel energetic, credible, and worth attending next time",
        "requirements": [
            "mix wide crowd moments with tighter reaction shots",
            "include one clear brand or venue anchor shot",
            "keep edits punchy but readable",
        ],
        "deliverables": ["reel structure", "anchor shot", "music / pacing note"],
        "tags": ["event", "recap", "community"],
        "base_popularity": 58,
    },
    {
        "slug": "real-estate-flythrough",
        "title": "Real Estate Flythrough",
        "summary": "Generate a premium property or space flythrough.",
        "category_slug": "photography",
        "subject": "a property or interior flythrough",
        "objective": "show layout, atmosphere, and premium detail in one short sequence",
        "requirements": [
            "use one smooth camera path instead of chaotic movement",
            "include scale cues and material detail",
            "end on a frame that can carry text",
        ],
        "deliverables": ["camera path", "hero frame", "space note"],
        "tags": ["real estate", "flythrough", "hospitality"],
        "base_popularity": 57,
    },
    {
        "slug": "fashion-lookbook",
        "title": "Fashion Lookbook",
        "summary": "Create a lookbook-style reel for fashion drops or editorial campaigns.",
        "category_slug": "photography",
        "subject": "a fashion lookbook clip for [collection]",
        "objective": "show silhouette, material, and attitude in a short social-friendly loop",
        "requirements": [
            "mix one full-body moment with one texture close-up",
            "keep styling editorial rather than generic influencer",
            "make the clip loop cleanly",
        ],
        "deliverables": ["shot sequence", "styling note", "loop moment"],
        "tags": ["fashion", "lookbook", "editorial"],
        "base_popularity": 56,
    },
    {
        "slug": "hospitality-reel",
        "title": "Hospitality Reel",
        "summary": "Generate a hospitality reel for hotels, venues, or destination brands.",
        "category_slug": "photography",
        "subject": "a hospitality promo reel for [property or venue]",
        "objective": "make the space feel premium and bookable in a few seconds",
        "requirements": [
            "show arrival, atmosphere, and one standout amenity",
            "use movement that feels calm and upscale",
            "keep the edit suitable for homepage hero or social use",
        ],
        "deliverables": ["arrival shot", "amenity moment", "closing frame"],
        "tags": ["hospitality", "venue", "travel"],
        "base_popularity": 55,
    },
    {
        "slug": "explainer-storyboard",
        "title": "Explainer Storyboard",
        "summary": "Create an explainer storyboard for a product, service, or workflow.",
        "category_slug": "marketing-business",
        "subject": "an explainer storyboard for [topic or product]",
        "objective": "turn a complex idea into a sequence that feels easy to follow",
        "requirements": [
            "break the story into simple beats",
            "pair each beat with one visual metaphor or motion cue",
            "end with a clean CTA or next-step frame",
        ],
        "deliverables": ["story beats", "visual cues", "cta frame"],
        "tags": ["explainer", "storyboard", "education"],
        "base_popularity": 64,
    },
    {
        "slug": "gameplay-flythrough",
        "title": "Gameplay Flythrough",
        "summary": "Generate a gameplay or environment flythrough for a game pitch or reveal.",
        "category_slug": "games-3d",
        "subject": "a game environment or gameplay reveal flythrough",
        "objective": "show scale, mood, and playability in a short reveal sequence",
        "requirements": [
            "include a focal landmark and traversal read",
            "keep the world feeling playable, not just scenic",
            "finish on a hero frame for title or logo",
        ],
        "deliverables": ["path direction", "hero reveal", "playability cue"],
        "tags": ["gameplay", "reveal", "environment"],
        "base_popularity": 65,
    },
]


def _slugify(value: str) -> str:
    lowered = value.lower()
    chars = [char if char.isalnum() else "-" for char in lowered]
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _model_prompt_hint(model_slug: str) -> str:
    model = MODELS[model_slug]
    return f"Shape the output to play to {model['name']}'s strengths: {model['description'].rstrip('.')}."


def _generate_image_prompts(existing_slugs: set[str]) -> List[Dict[str, Any]]:
    generated = []
    for blueprint_index, blueprint in enumerate(IMAGE_PROMPT_BLUEPRINTS):
        for model_index, model_slug in enumerate(IMAGE_MODEL_SLUGS):
            model = MODELS[model_slug]
            for variant_index, variant in enumerate(IMAGE_PROMPT_VARIANTS):
                slug = f"{blueprint['slug']}-{model_slug}-{variant['slug']}-prompt"
                if slug in existing_slugs:
                    continue
                prompt_text = "\n".join(
                    [
                        f"Create {blueprint['subject']} for [brand, project, or campaign] using {model['name']}.",
                        "",
                        "Objective:",
                        f"- {blueprint['objective']}.",
                        f"- Push toward {variant['focus']}.",
                        f"- { _model_prompt_hint(model_slug) }",
                        "",
                        "Requirements:",
                        *[f"- {requirement}." for requirement in blueprint["requirements"]],
                        f"- Keep the work appropriate for the {BUSINESS_CATEGORIES[blueprint['category_slug']]['short_name']} use case.",
                        "",
                        "Return:",
                        *[f"- {item}" for item in blueprint["deliverables"]],
                    ]
                )
                generated.append(
                    {
                        "slug": slug,
                        "title": f"{blueprint['title']} for {model['name']} - {variant['title']} Prompt",
                        "summary": f"{blueprint['summary']} Tailored for {model['name']} with a {variant['title'].lower()} angle.",
                        "prompt": prompt_text,
                        "model_slug": model_slug,
                        "category_slug": blueprint["category_slug"],
                        "modality": "image",
                        "tags": blueprint["tags"] + [variant["tag"], model["name"].lower(), "image prompt"],
                        "is_free": model_slug in FREE_MODEL_SLUGS and variant_index == 0 and blueprint_index % 2 == 0,
                        "featured": False,
                        "popularity": max(36, blueprint["base_popularity"] - variant_index * 3 - (model_index % 5)),
                    }
                )
                existing_slugs.add(slug)
    return generated


def _generate_text_prompts(existing_slugs: set[str]) -> List[Dict[str, Any]]:
    generated = []
    for blueprint_index, blueprint in enumerate(TEXT_PROMPT_BLUEPRINTS):
        for model_index, model_slug in enumerate(TEXT_MODEL_SLUGS):
            model = MODELS[model_slug]
            for variant_index, variant in enumerate(TEXT_PROMPT_VARIANTS):
                slug = f"{blueprint['slug']}-{model_slug}-{variant['slug']}-prompt"
                if slug in existing_slugs:
                    continue
                prompt_text = "\n".join(
                    [
                        f"You are using {model['name']} to produce {blueprint['task']}.",
                        "",
                        "Objective:",
                        f"- {blueprint['objective']}.",
                        f"- {variant['focus']}.",
                        f"- { _model_prompt_hint(model_slug) }",
                        "",
                        "Requirements:",
                        *[f"- {requirement}." for requirement in blueprint["requirements"]],
                        f"- Keep the output tuned for the {BUSINESS_CATEGORIES[blueprint['category_slug']]['short_name']} workflow.",
                        "",
                        "Return:",
                        *[f"- {item}" for item in blueprint["outputs"]],
                    ]
                )
                generated.append(
                    {
                        "slug": slug,
                        "title": f"{blueprint['title']} for {model['name']} - {variant['title']} Prompt",
                        "summary": f"{blueprint['summary']} Adapted for {model['name']} with a {variant['title'].lower()} output style.",
                        "prompt": prompt_text,
                        "model_slug": model_slug,
                        "category_slug": blueprint["category_slug"],
                        "modality": "text",
                        "tags": blueprint["tags"] + [variant["tag"], model["name"].lower(), "text prompt"],
                        "is_free": model_slug in FREE_MODEL_SLUGS and variant_index == 1 and blueprint_index % 2 == 1,
                        "featured": False,
                        "popularity": max(35, blueprint["base_popularity"] - variant_index * 3 - (model_index % 4)),
                    }
                )
                existing_slugs.add(slug)
    return generated


def _generate_video_prompts(existing_slugs: set[str]) -> List[Dict[str, Any]]:
    generated = []
    for blueprint_index, blueprint in enumerate(VIDEO_PROMPT_BLUEPRINTS):
        for model_index, model_slug in enumerate(VIDEO_MODEL_SLUGS):
            model = MODELS[model_slug]
            for variant_index, variant in enumerate(VIDEO_PROMPT_VARIANTS):
                slug = f"{blueprint['slug']}-{model_slug}-{variant['slug']}-prompt"
                if slug in existing_slugs:
                    continue
                prompt_text = "\n".join(
                    [
                        f"Create {blueprint['subject']} using {model['name']}.",
                        "",
                        "Objective:",
                        f"- {blueprint['objective']}.",
                        f"- {variant['focus']}.",
                        f"- { _model_prompt_hint(model_slug) }",
                        "",
                        "Requirements:",
                        *[f"- {requirement}." for requirement in blueprint["requirements"]],
                        f"- Keep the sequence usable for the {BUSINESS_CATEGORIES[blueprint['category_slug']]['short_name']} context.",
                        "",
                        "Return:",
                        *[f"- {item}" for item in blueprint["deliverables"]],
                    ]
                )
                generated.append(
                    {
                        "slug": slug,
                        "title": f"{blueprint['title']} for {model['name']} - {variant['title']} Prompt",
                        "summary": f"{blueprint['summary']} Built for {model['name']} with a {variant['title'].lower()} motion style.",
                        "prompt": prompt_text,
                        "model_slug": model_slug,
                        "category_slug": blueprint["category_slug"],
                        "modality": "video",
                        "tags": blueprint["tags"] + [variant["tag"], model["name"].lower(), "video prompt"],
                        "is_free": False,
                        "featured": False,
                        "popularity": max(34, blueprint["base_popularity"] - variant_index * 3 - (model_index % 4)),
                    }
                )
                existing_slugs.add(slug)
    return generated


def _generate_auto_prompt_definitions(target_total: int) -> List[Dict[str, Any]]:
    if len(PROMPT_DEFINITIONS) >= target_total:
        return []

    existing_slugs = {definition["slug"] for definition in PROMPT_DEFINITIONS}
    auto_definitions = []
    auto_definitions.extend(_generate_image_prompts(existing_slugs))
    auto_definitions.extend(_generate_text_prompts(existing_slugs))
    auto_definitions.extend(_generate_video_prompts(existing_slugs))

    needed = target_total - len(PROMPT_DEFINITIONS)
    if len(auto_definitions) < needed:
        raise ValueError(f"Not enough generated prompts to reach target: need {needed}, have {len(auto_definitions)}")

    return auto_definitions[:needed]


PROMPT_DEFINITIONS.extend(_generate_auto_prompt_definitions(AUTO_PROMPT_TARGET))


def _build_prompt(definition: Dict[str, Any]) -> Dict[str, Any]:
    model = MODELS[definition["model_slug"]]
    category = BUSINESS_CATEGORIES[definition["category_slug"]]
    modality = PROMPT_TYPES[definition["modality"]]
    tags = sorted(set(definition["tags"]))

    search_parts = [
        definition["title"],
        definition["summary"],
        definition["prompt"],
        model["name"],
        category["name"],
        modality["name"],
        " ".join(tags),
    ]
    if definition.get("is_free"):
        search_parts.append("free prompts")

    return {
        "slug": definition["slug"],
        "title": definition["title"],
        "summary": definition["summary"],
        "prompt": definition["prompt"],
        "model_slug": model["slug"],
        "model_name": model["name"],
        "model_description": model["description"],
        "model_icon": model["icon"],
        "category_slug": category["slug"],
        "category_name": category["name"],
        "category_short_name": category["short_name"],
        "category_icon": category["icon"],
        "modality": definition["modality"],
        "modality_name": modality["name"],
        "modality_icon": modality["icon"],
        "tags": tags,
        "is_free": bool(definition.get("is_free")),
        "featured": bool(definition.get("featured")),
        "popularity": int(definition["popularity"]),
        "url": f"/prompts/{definition['slug']}",
        "model_url": f"/prompts/model/{model['slug']}",
        "category_url": f"/prompts/category/{category['slug']}",
        "modality_url": f"/prompts/type/{definition['modality']}",
        "free_url": "/prompts/type/free" if definition.get("is_free") else None,
        "search_text": " ".join(search_parts).lower(),
    }


PROMPTS = tuple(_build_prompt(definition) for definition in PROMPT_DEFINITIONS)
PROMPTS_BY_SLUG = {prompt["slug"]: prompt for prompt in PROMPTS}
PROMPT_COUNT = len(PROMPTS)

_category_counts = Counter(prompt["category_slug"] for prompt in PROMPTS)
_model_counts = Counter(prompt["model_slug"] for prompt in PROMPTS)
_modality_counts = Counter(prompt["modality"] for prompt in PROMPTS)
_free_count = sum(1 for prompt in PROMPTS if prompt["is_free"])

_CATEGORY_LIST = tuple(
    {
        **meta,
        "count": _category_counts[slug],
        "url": f"/prompts/category/{slug}",
    }
    for slug, meta in BUSINESS_CATEGORIES.items()
)

_MODEL_LIST = tuple(
    {
        **meta,
        "count": _model_counts[slug],
        "url": f"/prompts/model/{slug}",
    }
    for slug, meta in MODELS.items()
)

_TYPE_LIST = tuple(
    {
        **meta,
        "count": _free_count if slug == "free" else _modality_counts[slug],
        "url": f"/prompts/type/{slug}",
    }
    for slug, meta in PROMPT_TYPES.items()
)


def _clone_list(items: List[Dict[str, Any]] | tuple) -> List[Dict[str, Any]]:
    return [deepcopy(item) for item in items]


def _sorted_prompts(prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(prompts, key=lambda prompt: (prompt["featured"], prompt["popularity"]), reverse=True)


def get_all_prompts() -> List[Dict[str, Any]]:
    return _clone_list(list(PROMPTS))


def get_prompt_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    prompt = PROMPTS_BY_SLUG.get(slug)
    return deepcopy(prompt) if prompt else None


def get_featured_prompts(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    prompts = [prompt for prompt in PROMPTS if prompt["featured"]]
    prompts = _sorted_prompts(prompts)
    if limit is not None:
        prompts = prompts[:limit]
    return _clone_list(prompts)


def get_prompts(
    *,
    category_slug: Optional[str] = None,
    model_slug: Optional[str] = None,
    prompt_type_slug: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    prompts = list(PROMPTS)

    if category_slug:
        prompts = [prompt for prompt in prompts if prompt["category_slug"] == category_slug]
    if model_slug:
        prompts = [prompt for prompt in prompts if prompt["model_slug"] == model_slug]
    if prompt_type_slug:
        if prompt_type_slug == "free":
            prompts = [prompt for prompt in prompts if prompt["is_free"]]
        else:
            prompts = [prompt for prompt in prompts if prompt["modality"] == prompt_type_slug]

    prompts = _sorted_prompts(prompts)
    if limit is not None:
        prompts = prompts[:limit]
    return _clone_list(prompts)


def get_related_prompts(prompt_slug: str, limit: int = 4) -> List[Dict[str, Any]]:
    prompt = PROMPTS_BY_SLUG.get(prompt_slug)
    if not prompt:
        return []

    related = [
        candidate
        for candidate in PROMPTS
        if candidate["slug"] != prompt_slug
        and (
            candidate["category_slug"] == prompt["category_slug"]
            or candidate["model_slug"] == prompt["model_slug"]
        )
    ]
    related = sorted(
        related,
        key=lambda candidate: (
            candidate["category_slug"] == prompt["category_slug"],
            candidate["model_slug"] == prompt["model_slug"],
            candidate["featured"],
            candidate["popularity"],
        ),
        reverse=True,
    )
    return _clone_list(related[:limit])


def get_categories() -> List[Dict[str, Any]]:
    return _clone_list(list(_CATEGORY_LIST))


def get_models() -> List[Dict[str, Any]]:
    return _clone_list(list(_MODEL_LIST))


def get_popular_models(limit: int = 8) -> List[Dict[str, Any]]:
    by_slug = {model["slug"]: model for model in _MODEL_LIST}
    models = [by_slug[slug] for slug in POPULAR_MODEL_ORDER if slug in by_slug]
    if limit is not None:
        models = models[:limit]
    return _clone_list(models)


def get_prompt_types() -> List[Dict[str, Any]]:
    return _clone_list(list(_TYPE_LIST))


def get_category_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    category = next((item for item in _CATEGORY_LIST if item["slug"] == slug), None)
    return deepcopy(category) if category else None


def get_model_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    model = next((item for item in _MODEL_LIST if item["slug"] == slug), None)
    return deepcopy(model) if model else None


def get_prompt_type_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    prompt_type = next((item for item in _TYPE_LIST if item["slug"] == slug), None)
    return deepcopy(prompt_type) if prompt_type else None


def get_sitemap_sections() -> List[Dict[str, Any]]:
    return [
        {
            "title": "Categories",
            "items": get_categories(),
        },
        {
            "title": "Most Popular Models",
            "items": get_popular_models(limit=8),
        },
        {
            "title": "Models",
            "items": get_models(),
        },
        {
            "title": "Prompt Types",
            "items": get_prompt_types(),
        },
        {
            "title": "Best AI prompts",
            "items": get_featured_prompts(limit=8),
        },
    ]


def get_prompt_stats() -> Dict[str, int]:
    return {
        "prompt_count": PROMPT_COUNT,
        "category_count": len(BUSINESS_CATEGORIES),
        "model_count": len(MODELS),
        "free_count": _free_count,
    }
