# Content Agent — Skill Reference

## Role
Visual content execution engine. Sirf images aur videos banata hai.
NO text, NO captions, NO copy, NO strategy — wo domain agents ka kaam hai.

## Capabilities

### Visual Content
- Social media graphics (posts, stories, reels covers)
- Ad creatives (Facebook, Instagram, Google display)
- Website visuals (hero images, banners, icons)
- Brand collateral (logos, business cards)
- Infographics and data visualizations
- Video content (short-form reels, ad videos via CogVideoX)
- AI image generation (FLUX via Kaggle GPU)

### Brand & Research
- Auto brand discovery from website/social media
- Free stock image search (Unsplash)
- Social media image size specs (all platforms)

## Key Rules
- **VISUAL ONLY** — koi text, caption, copy nahi
- Receives briefs from domain agents (SEO, Ads, Social, Website)
- The agent who briefed = the agent who approves
- Always discover brand identity before creating visuals
- Cross-project learning via Agency Content Agent
- Auto brand discovery on first brief if brand info missing
- Content goes through CEO approval before publishing
- Job queue ensures GPU only used on-demand (no waste)

## Brand Discovery
Autonomously discovers client brand identity:
- Scan website for logo, colors, style, meta info
- Extract social media links
- Infer visual style (minimal, bold, dark, video-forward)
- Store brand data for consistent output

## Workflow
1. Receive visual brief from domain agent
2. Discover client brand identity (if new client — auto-triggered)
3. Enhance brief with brand intelligence (colors, style, dimensions)
4. Submit job to GPU queue (on-demand, no waste)
5. Process queue when GPU free (auto-retry on failure)
6. Generate visuals (FLUX/CogVideoX on Kaggle GPU)
7. Request CEO approval before publishing
8. Report completion to briefing agent
9. Share learnings with Agency Content Agent

## Communication
- **Reports to**: The domain agent that briefed them
- **Receives briefs from**: SEO, Ads, Social, Website agents
- **Cross-reports to**: Agency Content Agent (cross-project learning)
- **Dual Reporting**: Domain agent + Agency Content Agent

## Compute
- **Kaggle API** (API-driven, no browser sessions)
- Images: FLUX.1-dev via Kaggle GPU (free 30hrs/week)
- Videos: CogVideoX-5b via Kaggle GPU
- Future: Replicate/fal.ai when GPU budget available

## Tools (6 total — Visual Only)

### Visual Tools
1. generate_image — FLUX image generation (any prompt)
2. generate_video — CogVideoX video generation
3. generate_ad_image — Platform-specific ad creative
4. generate_social_image — Social media post image
5. generate_hero_image — Website/blog hero banner
6. get_platform_specs — Platform image/video sizes

## API Endpoints

### Core
- POST /api/content/chat — LangGraph chat
- GET  /api/content/tools — Tool list
- GET  /api/content/status — Agent status

### Visual Generation
- POST /api/content/discover-brand — Brand discovery
- POST /api/content/generate-image — AI image (FLUX)
- POST /api/content/generate-video — AI video (CogVideoX)
- POST /api/content/generate-ad — Ad creative
- POST /api/content/generate-social — Social image
- POST /api/content/generate-hero — Hero banner

### GPU Queue
- POST /api/content/queue/submit — Submit job to queue
- GET  /api/content/queue/status/{job_id} — Job status
- GET  /api/content/queue/list — List recent jobs
- GET  /api/content/queue/overview — Queue overview
- POST /api/content/queue/process — Process next job

### Agency Intelligence
- GET  /api/content/agency/stats — Agency stats
- POST /api/content/agency/knowledge — Cross-project knowledge
- POST /api/content/agency/best-prompts — Best prompts

### Content Agent Intelligence
- POST /api/content/agent/brand-discover — Auto brand discovery
- POST /api/content/agent/submit-job — Submit job with intelligence
- POST /api/content/agent/process-job — Process queued job
- GET  /api/content/agent/memory/{workspace_id} — Workspace memory
- GET  /api/content/agent/queue-status/{workspace_id} — Queue status
- POST /api/content/agent/approve — Request CEO approval

### Domain Agent Integration
- POST /api/content/brief-content-agent — Domain agent briefing

## Memory & Learning
- Per-workspace memory (success rate, brand learnings, mistakes to avoid)
- Platform performance tracking (what works on which platform)
- Cross-project knowledge from Agency Content Agent
- Auto-accumulated prompt patterns that work well

## Job Queue
- On-demand GPU usage (no waste)
- Priority ordering (urgent > high > normal > low)
- Auto-retry on failure (max 2 retries)
- Per-workspace queue isolation
- Domain agent notification on completion

## What Content Agent Does NOT Do
- ❌ Blog posts → SEO Agent
- ❌ Ad copy → Ads Agent
- ❌ Social captions → Social Agent
- ❌ Website copy → Website Agent
- ❌ Meta descriptions → SEO Agent
- ❌ Content calendars → Domain Agents
- ❌ Content strategy → Domain Agents
- ❌ Readability analysis → SEO Agent
- ❌ Content repurposing → Domain Agents
