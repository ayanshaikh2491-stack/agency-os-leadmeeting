# Content Agent — Skill Reference

## Role
Visual content execution engine with REASONING CHAIN.
Har brief ko samajhta hai, sochta hai, strategize karta hai, phir execute karta hai.
Sirf images aur videos nahi — PERFORMANCE-FIRST visuals banata hai.

## Reasoning Chain (5 Steps)

```
Brief → UNDERSTAND → RESEARCH → STRATEGIZE → EXECUTE → VALIDATE
```

### Step 1: UNDERSTAND
- Brief deeply parse karta hai
- Content type, platform, objective, audience, emotional hook extract karta hai
- Missing fields identify karta hai
- Domain agent ka intent samajhta hai (ads=conversion, social=engagement)

### Step 2: RESEARCH
- Brand identity gather karta hai (colors, style, tone)
- Platform specs check karta hai (dimensions, format)
- Past performance data dekhta hai
- Competitor visual patterns analyze karta hai

### Step 3: STRATEGIZE
- Format decide karta hai (single image, carousel, video)
- Style decide karta hai (minimal, bold, cinematic)
- Composition plan banata hai (layout, focal point, text space)
- Color strategy banata hai (brand colors, contrast, mood)
- Variations plan karta hai (kitne versions, kya different hoga)

### Step 4: EXECUTE
- Expert prompts generate karta hai for FLUX/CogVideoX
- Platform-specific optimizations add karta hai
- GPU queue mein submit karta hai
- Multiple variations generate karta hai

### Step 5: VALIDATE
- Brand consistency check karta hai
- Platform compliance verify karta hai
- Emotional alignment check karta hai
- Quality score assign karta hai (1-10)
- Score < 7 = retry with adjusted prompt

## Capabilities

### Visual Content
- Social media graphics (posts, stories, reels covers)
- Instagram carousels (multi-slide, 5-10 images)
- Ad creatives (Facebook Ads, Google Display, Instagram)
- YouTube thumbnails (1280x720, high contrast)
- Website visuals (hero images, banners, icons)
- Brand collateral (logos, business cards)
- Infographics and data visualizations
- UGC videos (testimonial, review, unboxing, reaction)
- Marketing videos (explainer, product showcase, brand story)
- Trading/finance videos (charts, data visualization)
- AI image generation (FLUX via Kaggle GPU)
- AI video generation (CogVideoX via Kaggle GPU)

### Content Types (14 total)
1. **Instagram Post** — Single image (1080x1080/1080x1350)
2. **Carousel** — Multi-slide images (5-10 slides)
3. **Story** — Vertical image (1080x1920)
4. **Ad Creative** — Platform-specific ad image
5. **Thumbnail** — YouTube/blog thumbnail (1280x720)
6. **UGC Video** — Authentic user-generated content style
7. **Marketing Video** — Polished commercial video
8. **Explainer Video** — Step-by-step educational video
9. **Product Showcase** — 360-degree product video
10. **Testimonial** — Real person testimonial video
11. **Unboxing** — Product unboxing video
12. **Trading Video** — Financial visualization video
13. **Regular Video** — General motion content
14. **Hero Image** — Website/blog banner

## Key Rules
- **REASON FIRST** — Har brief pehle samjho, phir execute karo
- **PERFORMANCE-FIRST** — Aesthetics nahi, CONVERSION chahiye
- Receives structured briefs from domain agents (SEO, Ads, Social, Website)
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
1. Receive structured brief from domain agent
2. **UNDERSTAND** — Parse brief deeply (objective, audience, emotion, CTA)
3. **RESEARCH** — Gather brand data, platform specs, past performance
4. **STRATEGIZE** — Plan visual approach (format, style, composition, colors)
5. **EXECUTE** — Generate expert prompts, submit to GPU queue
6. **VALIDATE** — Quality check (score 1-10), retry if needed
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
- Images: FLUX.1-schnell via Kaggle GPU (free 30hrs/week)
- Videos: CogVideoX-2b via Kaggle GPU
- On-demand GPU usage (no waste)

## Tools (14 total — Visual Only)

### Image Generation
1. generate_image — FLUX image generation (any prompt)
2. generate_carousel — Multi-slide carousel images
3. generate_ad_image — Platform-specific ad creative
4. generate_social_image — Social media post image
5. generate_hero_image — Website/blog hero banner
6. generate_story — Instagram/Facebook story (1080x1920)
7. generate_thumbnail — YouTube/blog thumbnail (1280x720)

### Video Generation
8. generate_video — CogVideoX video generation
9. generate_ugc — UGC style video (testimonial, review, unboxing)
10. generate_testimonial — Real person testimonial video
11. generate_unboxing — Product unboxing video
12. generate_explainer — Step-by-step explainer video
13. generate_product_showcase — 360-degree product showcase video

### Utilities
14. get_platform_specs — Platform image/video sizes

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

### Reasoning Chain
- POST /api/content/reasoning/run — Run 5-step reasoning chain
- GET  /api/content/reasoning/{job_id} — Get reasoning log
- GET  /api/content/reasoning/stats/recent — Recent stats

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
- **Reasoning logs** — Every step's reasoning stored for debugging

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
