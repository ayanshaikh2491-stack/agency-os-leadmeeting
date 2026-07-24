# Content Agent — Skill Reference

## Role
Full-spectrum content execution engine. Creates images, videos, AND text content.

## Capabilities

### Visual Content
- Social media graphics (posts, stories, reels covers)
- Ad creatives (Facebook, Instagram, Google display)
- Website visuals (hero images, banners, icons)
- Brand collateral (logos, business cards)
- Infographics and data visualizations
- Video content (short-form reels, ad videos via CogVideoX)
- AI image generation (FLUX via Kaggle GPU)

### Text Content
- Blog posts (SEO-optimized with HTML output)
- Website copy and landing pages
- Ad copy (Facebook, Instagram, Google, LinkedIn)
- Social media captions
- Meta descriptions and title tags
- Content briefs with outlines

### Content Strategy
- Content calendars (weekly/monthly planning)
- Content gap analysis (vs competitors)
- Readability analysis (Flesch-Kincaid scores)
- SEO scoring and optimization
- Content repurposing across platforms

### Brand & Research
- Auto brand discovery from website/social media
- Free stock image search (Unsplash)
- Social media image size specs (all platforms)
- Competitor content analysis

## Key Rules
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
1. Receive visual/content brief from domain agent
2. Discover client brand identity (if new client — auto-triggered)
3. Enhance brief with brand intelligence (colors, style, dimensions)
4. Submit job to GPU queue (on-demand, no waste)
5. Process queue when GPU free (auto-retry on failure)
6. Generate visuals (FLUX/CogVideoX on Kaggle GPU)
7. Generate text content (blog, copy, meta)
8. Request CEO approval before publishing
9. Report completion to briefing agent
10. Share learnings with Agency Content Agent

## Communication
- **Reports to**: The domain agent that briefed them
- **Receives briefs from**: SEO, Ads, Social, Website agents
- **Cross-reports to**: Agency Content Agent (cross-project learning)
- **Dual Reporting**: Domain agent + Agency Content Agent

## Compute
- **Kaggle API** (API-driven, no browser sessions)
- Images: FLUX.1-dev via Kaggle GPU (free 30hrs/week)
- Videos: CogVideoX-5b via Kaggle GPU
- Text: Local processing (no GPU needed)
- Future: Replicate/fal.ai when GPU budget available

## Tools (21 total)

### Visual Tools (10)
1. discover_brand_identity — Scan website for brand
2. parse_visual_brief — Parse domain agent brief
3. plan_visual_production — Plan prompts, dimensions, GPU
4. generate_image_kaggle — FLUX image generation
5. generate_ad_image — Platform-specific ad creative
6. generate_social_image — Social media post image
7. generate_hero_image — Website/blog hero banner
8. batch_generate_images — Multiple images for calendar
9. generate_video_kaggle — CogVideoX video generation
10. generate_video_ad — Video advertisement

### Content Tools (11)
11. analyze_readability — Flesch-Kincaid readability scores
12. generate_content_brief — Brief with outline + keywords
13. generate_blog_post — SEO blog post with HTML
14. optimize_meta_descriptions — Meta tag optimization
15. rewrite_content — Improve readability
16. generate_content_calendar — Weekly content plan
17. analyze_content_gaps — Competitor content analysis
18. search_images — Free stock image search
19. get_social_image_specs — Platform image sizes
20. repurpose_for_social — Cross-platform content conversion
21. generate_ad_copy — Ad copy for any platform

## API Endpoints (38 total)

### Core
- POST /api/content/chat — LangGraph chat
- GET  /api/content/tools — Tool list
- GET  /api/content/status — Agent status

### Visual Generation
- POST /api/content/discover-brand — Brand discovery
- POST /api/content/parse-brief — Brief parsing
- POST /api/content/plan — Production planning
- POST /api/content/generate-image — AI image (FLUX)
- POST /api/content/generate-video — AI video (CogVideoX)
- POST /api/content/generate-ad — Ad creative
- POST /api/content/generate-social — Social image
- POST /api/content/generate-hero — Hero banner
- POST /api/content/batch-generate — Batch images

### Text Content
- POST /api/content/analyze-readability — Readability
- POST /api/content/content-brief — Content brief
- POST /api/content/blog-post — Blog post
- POST /api/content/optimize-meta — Meta optimization
- POST /api/content/rewrite — Content rewrite
- POST /api/content/calendar — Content calendar
- POST /api/content/gap-analysis — Gap analysis
- POST /api/content/search-images — Stock images
- POST /api/content/image-specs — Image sizes
- POST /api/content/repurpose — Cross-platform
- POST /api/content/ad-copy — Ad copy

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

### Content Agent Intelligence (NEW)
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

## Interview References
- Q1: Full-spectrum content (visual + text)
- Q2: Full visual spectrum
- Q3: Kaggle API (FLUX + CogVideoX)
- Q4: Per-workspace isolation
- Q5: Brand discovery
- Q6: Domain agent approval authority
- Q7: Cross-project learning via Agency Content Agent
- Q11: Two-tier (workspace + agency)
- Q27: Cross-project knowledge sharing
