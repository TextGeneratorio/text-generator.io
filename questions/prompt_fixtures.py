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
