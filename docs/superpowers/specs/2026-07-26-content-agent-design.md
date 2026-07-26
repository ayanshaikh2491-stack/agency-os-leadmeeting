# Content Agent — Advanced Visual Content Engine

**Date:** 2026-07-26
**Status:** Approved
**Scope:** Full rebuild of Content Agent for TAGS Agency OS

---

## 1. Overview

Content Agent = Visual content powerhouse for all workspaces. Creates images, videos, UGC content, marketing videos, trading visuals — sab. Har workspace ke agents isko use karenge.

**Key Principles:**
- VISUAL ONLY — no text, captions, copy (domain agents ka kaam)
- 3-4 variations per brief — taake agents SELECT kar sakein
- Human-like video output — AI feel nahi aani chahiye
- Error-free across all workspaces — robust retry + fallback
- Cross-project learning — purane projects ki knowledge naye mein use ho

---

## 2. Pipeline Architecture (6 Nodes)

```
Domain Agent / User
        ↓
   ┌─────────────────────────────────────────────────────┐
   │           CONTENT AGENT (LangGraph Pipeline)         │
   │                                                      │
   │  Node 1: PARSE BRIEF                                │
   │    → Free text → Structured brief                    │
   │    → visual_type, platform, mood, style, quantity    │
   │    → content_category (social/ad/ugc/trading/etc)   │
   │                                                      │
   │  Node 2: ANALYZE BRAND                              │
   │    → Workspace brand context load                    │
   │    → Agency knowledge inject                         │
   │    → Platform-specific guidelines                    │
   │    → Style memory load (past preferences)            │
   │                                                      │
   │  Node 3: PLAN VISUAL                                │
   │    → Composition, layout, elements decide            │
   │    → Image: FLUX settings                           │
   │    → Video: CogVideoX motion, frames, pacing        │
   │    → UGC: Testimonial/review style, human feel      │
   │    → Marketing: Product showcase, transitions       │
   │    → Trading: Chart animations, data viz            │
   │    → Variation plan (3-4 styles per brief)           │
   │                                                      │
   │  Node 4: ENGINEER PROMPT                            │
   │    → Expert-level prompt likho                       │
   │    → Brand colors + style automatically include     │
   │    → Platform optimize karo                         │
   │    → Negative prompt bhi banao                      │
   │    → Human-like video keywords add karo             │
   │    → Har variation ke liye alag prompt              │
   │                                                      │
   │  Node 5: GENERATE                                   │
   │    → Image? → FLUX (Kaggle GPU)                     │
   │    → Video? → CogVideoX (Kaggle GPU)                │
   │    → UGC? → UGC pipeline                            │
   │    → Marketing? → Marketing video pipeline           │
   │    → Batch mode (multiple variations)               │
   │    → Smart retry on failure                         │
   │                                                      │
   │  Node 6: VALIDATE                                   │
   │    → File exists? Size OK?                          │
   │    → Platform size match?                           │
   │    → Brand consistency check                        │
   │    → Quality score (1-10)                           │
   │    → Fail? → Back to Node 4 (retry max 2)           │
   │                                                      │
   └──────────────────────┬──────────────────────────────┘
                          ↓
   CEO Approval → Domain Agent ko deliver
```

---

## 3. Content Types

### Images
- Social Media Posts (Instagram, Facebook, LinkedIn, Twitter)
- Ad Creatives (Facebook Ad, Google Display, LinkedIn Ad)
- Website Visuals (Hero, Banner, Favicon, OG Image)
- Blog Visuals (Hero, Thumbnail, Infographic)
- Brand Assets (Logo concept, Business Card mockup)
- Marketing Materials (Poster, Flyer, Email Header)

### Videos
- Social Reels (Instagram, TikTok, YouTube Shorts)
- Ad Videos (Facebook, Instagram, YouTube pre-roll)
- Trading/Finance Videos (charts, animations, data viz)
- Product Review Videos (showcase, unboxing style)
- Project Review Videos (portfolio, case study)
- Explainer Videos (how-it-works, feature showcase)
- Testimonial/UGC Videos (human-like, real feel)
- Before/After Videos (transformation, comparison)
- Brand Story Videos (about us, mission)

### Human-Like Video Rule
- Natural, imperfect framing
- Warm, organic color grading
- Subtle camera movement (handheld feel)
- Real-world environments (not studio)
- Natural lighting (window light, golden hour)
- Genuine expressions and gestures
- Prompt keywords: "cinematic, natural lighting, handheld camera feel, warm color grading, real environment, authentic, documentary style, 24fps film look"

---

## 4. Variation System

Har brief ke liye 3-4 variations banti hain:

### Image Variations
| Platform | Size | Style Twist | Composition |
|----------|------|-------------|-------------|
| Instagram Post | 1080x1350 | Bold, vibrant | Subject center, text space right |
| Instagram Story | 1080x1920 | Full screen, immersive | Subject fills frame |
| Instagram Reel Cover | 1080x1920 | Motion implied, dynamic | Action shot |
| Facebook Post | 1200x630 | Clean, engaging | Horizontal, balanced |
| Facebook Ad | 1080x1080 | Eye-catching, CTA space | Product focused |
| LinkedIn | 1200x627 | Professional, muted | Corporate feel |
| Twitter/X | 1200x675 | Bold, contrast | Quick impact |
| YouTube Thumbnail | 1280x720 | Bold text space | High contrast |
| Blog Hero | 1200x600 | Clean, minimal | Wide, text left |

### Video Variations
| Platform | Duration | Style | Notes |
|----------|----------|-------|-------|
| Instagram Reel | 15-30 sec | Fast cuts, trendy | 9:16 vertical |
| Instagram Feed | 30 sec | Cinematic | 1:1 or 4:5 |
| Facebook Ad | 10 sec | CTA focused | 16:9 or 1:1 |
| YouTube Shorts | 60 sec | Storytelling | 9:16 vertical |
| LinkedIn | 30 sec | Professional | 16:9 |
| TikTok | 15 sec | Trendy, fast | 9:16 vertical |

### Style Variations (per brief)
- Variation A: Bold & Dramatic (dark, intense, high contrast)
- Variation B: Clean & Modern (bright, minimal, professional)
- Variation C: Raw & Gritty (authentic, industrial, real)
- Variation D: Lifestyle Focus (everyday, approachable, warm)

### Selection Flow
1. Content Agent generates 3-4 variations
2. Variations stored in workspace output folder
3. Requesting agent gets all variations
4. Agent SELECTS best one
5. Selected one → CEO approval
6. Others → saved for future reference (style memory)

---

## 5. Content Category Intelligence

### Trading/Finance Videos
- Chart animations (candlestick, line, bar)
- Price movement visualization
- Technical indicators overlay
- News headline animations
- Style: Clean, professional, data-driven
- Feel: Like a real financial analyst's content

### Product Review Videos
- Product 360° showcase
- Feature highlight animations
- Comparison splitscreen
- Pros/Cons visual overlay
- Style: Clean background, product-focused
- Feel: Like a real reviewer's b-roll

### Project Review Videos
- Portfolio showcase with transitions
- Before/After transformation
- Process timeline animation
- Result metrics display
- Style: Professional, clean transitions
- Feel: Like a real agency case study

### UGC / Testimonial Videos
- Human-like talking head style
- Casual, authentic feel
- Background: office, home, outdoor (not studio)
- Movement: natural gestures, expressions
- Style: Handheld feel, warm tones
- Feel: Like a REAL person reviewing, NOT AI-generated
- Key: Natural lighting, imperfect framing, genuine emotion

---

## 6. Error Handling (7 Levels)

### Level 1: LLM Call Fails
- Fallback: Doosra LLM try karo
- Agar dono fail: Error message to caller agent

### Level 2: Prompt Engineering Fails
- LLM ne ghalat prompt banaya
- Validation node detect karta hai
- Auto-fix prompt → retry

### Level 3: GPU Submission Fails
- Kaggle CLI error / API down
- Retry with fresh notebook submission (max 2 baar)

### Level 4: GPU Generation Fails
- FLUX/CogVideoX crash on GPU
- P100 detected (FLUX nahi chalega)
- Auto-switch to SDXL fallback
- Smart retry with simplified prompt

### Level 5: Download Fails
- Output file nahi mila / corrupted
- Retry generation from scratch

### Level 6: Validation Fails
- Image too small / wrong size / brand colors nahi match
- Quality score low (<5)
- Retry with adjusted prompt (max 2 baar)

### Level 7: Timeout
- GPU 10 min mein complete nahi hua
- Kill notebook, retry with shorter prompt
- Agar 3 baar timeout: Report failure to agent

### Smart Retry Logic
```
Attempt 1: Full prompt, full settings
    ├─ SUCCESS + Score > 7 → DONE
    ├─ SUCCESS + Score 5-7 → DELIVER with note
    ├─ SUCCESS + Score < 5 → RETRY (prompt adjust)
    ├─ GPU ERROR → RETRY (simplified prompt)
    └─ TIMEOUT → RETRY (shorter prompt)

Attempt 2: Simplified prompt
    ├─ SUCCESS + Score > 5 → DONE
    ├─ SUCCESS + Score < 5 → RETRY (fallback model)
    └─ ERROR → RETRY (fallback model)

Attempt 3: Fallback model (SDXL instead of FLUX)
    ├─ SUCCESS → DONE (note: used fallback model)
    └─ ERROR → REPORT FAILURE
```

---

## 7. Workspace Isolation

### Structure
```
data/workspaces/
  workspace_fitpro_001/
    ├── brand.json
    ├── content_agent/
    │   ├── memory.json
    │   ├── style_guide.json
    │   └── outputs/
    │       ├── 2026-07-26/
    │       │   ├── fitness_post_v1.png
    │       │   ├── fitness_post_v2.png
    │       │   └── product_video_v1.mp4
    │       └── 2026-07-25/
    │           └── ...
    ├── social_agent/
    ├── ads_agent/
    ├── seo_agent/
    └── website_agent/
```

### Isolation Rules
- Har workspace ka apna brand.json
- Har workspace ka apna content_agent/memory.json
- Har workspace ka apna outputs folder
- Kal ke outputs aaj ke saath mix NAHI honge
- Ek workspace ka data doosre workspace mein NAHI jayega
- Agency knowledge shared hai, but workspace-specific data isolated

### Error Handling Per Workspace
- Content Agent crash → Automatic restart, memory load from disk
- GPU quota exhausted → Queue pending jobs, retry Monday
- Brand discovery fail → Fallback to last known brand data
- Kaggle down → Queue all pending jobs, alert CEO
- Concurrent requests → Queue system with priority (Ads > Social > SEO > Website)

---

## 8. Quality Scoring (1-10)

### Factors
- Brand Match (0-3): colors used (+1), style followed (+1), name/logo visible (+1)
- Platform Fit (0-2): correct dimensions (+1), platform-appropriate style (+1)
- Prompt Accuracy (0-2): subject matches (+1), mood/style matches (+1)
- Technical Quality (0-2): resolution acceptable (+1), file size reasonable (+1)
- Overall Appeal (0-1): visual quality assessment (+1)

### Score Actions
- 8-10: Excellent → Auto-approve, deliver
- 6-7: Good → Deliver with note
- 4-5: Average → Retry with adjusted prompt
- 1-3: Poor → Retry from scratch
- 0: Failed → Report error to agent

### Score Usage
- Workspace memory mein save hota hai
- "Best prompts" list maintain hoti hai
- Agency knowledge mein aggregate hota hai
- Future requests mein reference hota hai

---

## 9. Agency Knowledge System

### Knowledge Types
1. Prompt Patterns — kya kaam karta hai (success rate, sample prompts)
2. Brand Insights — industry trends (e.g., "real estate: exterior shots > interior")
3. Failure Patterns — kya NAHI kaam karta (avoid these approaches)
4. Platform Performance — kis platform pe kya chalta hai
5. GPU Optimization — efficiency tips (steps, model selection, frame counts)

### Knowledge Flow
```
Project A completes → Report to Agency → Knowledge stored
Project B starts → Agency sends relevant knowledge → Content Agent uses it
```

### Knowledge Injection (Node 2)
1. Workspace brand load karo
2. Agency knowledge load karo (same industry, platform, failures)
3. Combine → System prompt mein inject karo

### Knowledge Updates
- Success → Prompt pattern saved, brand insight updated
- Failure → Failure pattern recorded, "avoid this" added
- 3 same failures → Alert CEO
- Monthly → Agency aggregates learnings
- Quarterly → Review and clean old patterns

---

## 10. API Endpoints

### Core
- POST /api/content/chat — LangGraph chat
- GET /api/content/status — Agent status + GPU info
- GET /api/content/tools — Available tools

### Visual Generation
- POST /api/content/generate-image — Single image
- POST /api/content/generate-video — Single video
- POST /api/content/generate-ad — Ad creative
- POST /api/content/generate-social — Social media image
- POST /api/content/generate-hero — Hero/banner
- POST /api/content/generate-ugc — UGC style video
- POST /api/content/generate-marketing — Marketing video

### Variations
- POST /api/content/generate-variations — 3-4 variations per brief
- POST /api/content/batch-generate — Multiple images batch (content calendar: up to 7 images, consistent style, single GPU submission)

### Briefing
- POST /api/content/brief — Domain agent brief
- POST /api/content/select-variation — Select best variation

### Approval
- POST /api/content/approve — CEO approval
- POST /api/content/reject — CEO rejection

### Intelligence
- GET /api/content/agency/stats — Agency stats
- GET /api/content/agency/knowledge — Cross-project knowledge
- GET /api/content/workspace/:id/memory — Workspace memory
- GET /api/content/workspace/:id/outputs — Workspace outputs

---

## 11. Files to Modify

| File | Change |
|------|--------|
| `admin/workspace/agents/content.py` | Full rebuild — 6 nodes, variations, intelligence |
| `admin/tools/visual_tools.py` | Add UGC, marketing, video intelligence tools |
| `admin/tools/kaggle_gpu.py` | Add fallback models, smart retry |
| `admin/workspace/content_store.py` | Enhanced memory, variations tracking |
| `admin/agency/content_agent.py` | Knowledge injection, pattern learning |
| `admin/api/routes/content.py` | New endpoints |
| `admin/skills/content/SKILL.md` | Updated skill reference |

---

## 12. Migration Plan

- Phase 1 (Abhi): Single Pipeline — images + videos + UGC + marketing sab ek mein
- Phase 2 (Baad mein): Router node add karo jab pipeline bohot badi ho jaye
- Phase 3 (Future): Split into specialized pipelines if needed

---

## 13. Interview References

- Q1: Full visual spectrum
- Q3: Kaggle API (FLUX + CogVideoX)
- Q4: Per-workspace isolation
- Q5: Brand discovery
- Q6: Domain agent approval authority
- Q7: Cross-project learning via Agency Content Agent
- Q11: Two-tier (workspace + agency)
- Q27: Cross-project knowledge sharing
