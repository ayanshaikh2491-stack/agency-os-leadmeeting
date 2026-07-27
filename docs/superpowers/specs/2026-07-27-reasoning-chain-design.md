# Reasoning Chain Architecture — Agency Content Agent

## Problem

Domain agents (Ads, Social, SEO, Website) send briefs to Content Agent. But Content Agent executes blindly — no understanding, no strategy, no quality check. Result: poor visuals, wasted GPU time, ads that don't convert.

## Solution: 5-Step Reasoning Chain

Content Agent gets a structured workflow that forces thinking before execution:

```
Brief → UNDERSTAND → RESEARCH → STRATEGIZE → EXECUTE → VALIDATE
```

### Step 1: UNDERSTAND (Parse Brief)

**Input:** Raw brief from domain agent  
**Output:** Structured understanding  

LLM call to extract:
- `content_type` — ad_creative, social_post, hero_image, etc.
- `platform` — facebook, instagram, youtube, website
- `objective` — lead_generation, brand_awareness, engagement
- `target_audience` — age, interests, pain points
- `emotional_hook` — fear, curiosity, urgency, trust
- `cta` — call to action
- `constraints` — budget, time, brand guidelines
- `missing_fields` — what's not in the brief

### Step 2: RESEARCH (Gather Intelligence)

**Input:** Parsed brief  
**Output:** Enriched context  

Gather from:
- Brand identity (colors, fonts, style from workspace data)
- Past performance (what worked before for this workspace)
- Platform specs (image sizes, video lengths, format requirements)
- Competitor data (if available)
- Agency knowledge (cross-project learnings)

### Step 3: STRATEGIZE (Plan Visual)

**Input:** Brief + Research  
**Output:** Visual strategy  

LLM call to decide:
- `format` — single image, carousel, video, story
- `style` — minimal, bold, dark, vibrant, professional
- `composition` — layout, focal point, text placement
- `color_strategy` — brand colors, contrast, mood
- `variations` — how many versions, what differs
- `platform_optimization` — specific tweaks per platform

### Step 4: EXECUTE (Generate)

**Input:** Strategy + prompt  
**Output:** Raw visuals  

- Generate prompts from strategy
- Submit to GPU queue (FLUX for images, CogVideoX for videos)
- Generate multiple variations
- Download and verify outputs

### Step 5: VALIDATE (Quality Check)

**Input:** Generated visuals  
**Output:** Quality assessment  

LLM call to check:
- Brand consistency (colors, style match)
- Platform compliance (dimensions, file size)
- Emotional alignment (does it match the hook?)
- Text readability (if any text overlay)
- Overall quality score (1-10)
- Recommendations for improvement

If score < 7: retry with adjusted prompt
If score >= 7: deliver to domain agent

## Implementation Plan

### Phase 1: Content Agent Reasoning Chain

**File: `admin/workspace/agents/content.py`**

Current graph:
```
parse_brief → analyze_brand → plan_visual → engineer_prompt → generate → validate
```

New graph with reasoning chain:
```
understand_brief → research_context → strategize_visual → execute_generation → validate_output
```

Each step:
1. Receives `ContentState` 
2. Makes LLM call to reason about the step
3. Stores reasoning in state for next step
4. Logs reasoning for debugging

### Phase 2: Domain Agent Brief Format

**Files: `admin/workspace/agents/ads.py`, `social.py`, `seo.py`, `website.py`**

Update `request_content()` in each agent to send structured briefs:

```python
brief = {
    "domain": "ads",  # or social, seo, website
    "content_type": "ad_creative",
    "platform": "facebook",
    "objective": "lead_generation",
    "target_audience": {
        "age_range": "25-45",
        "interests": ["small business", "entrepreneurship"],
        "pain_points": ["low sales", "no online presence"]
    },
    "emotional_hook": "fear_of_missing_out",
    "cta": "Start Free Trial",
    "copy_text": "Don't let your competitors get ahead...",
    "brand_guidelines": {...},
    "variations_needed": 3,
    "priority": "high",
    "deadline": "2026-07-28"
}
```

### Phase 3: Reasoning Logger

New file: `admin/tools/reasoning_logger.py`

Logs each step's reasoning:
```json
{
    "job_id": "abc123",
    "workspace_id": "xyz",
    "domain": "ads",
    "steps": {
        "understand": {
            "timestamp": "...",
            "reasoning": "This is a Facebook ad for lead generation...",
            "extracted_fields": {...},
            "tokens_used": 250
        },
        "research": {
            "brand_colors": [...],
            "past_performance": {...},
            "platform_specs": {...},
            "tokens_used": 150
        },
        "strategize": {
            "format": "carousel",
            "style": "minimal_bold",
            "variations": [...],
            "tokens_used": 300
        },
        "execute": {
            "prompts_generated": [...],
            "gpu_jobs_submitted": 3,
            "tokens_used": 0
        },
        "validate": {
            "quality_score": 8,
            "checks_passed": [...],
            "recommendations": [...],
            "tokens_used": 200
        }
    },
    "total_tokens": 900,
    "total_time_seconds": 45
}
```

### Phase 4: API Endpoints

Add to `admin/api/routes/content.py`:

```
POST /api/content/reasoning/{job_id}  — Get reasoning chain for a job
GET  /api/content/reasoning/stats     — Reasoning stats across jobs
```

### Phase 5: E2C Tests

Test file: `tests/test_reasoning_chain.py`

1. Test understand_brief extracts correct fields
2. Test research_context gathers brand data
3. Test strategize_visual creates proper plan
4. Test execute_generation produces valid output
5. Test validate_output scores correctly
6. Test full chain: Ads Agent → Content Agent → Visual output
7. Test full chain: Social Agent → Content Agent → Visual output

## Token Budget

Per job (estimated):
- Understand: ~250 tokens
- Research: ~150 tokens  
- Strategize: ~300 tokens
- Execute: 0 tokens (GPU only)
- Validate: ~200 tokens
- **Total: ~900 LLM tokens per visual**

With 3 variations: ~900 tokens (same reasoning, different generation)

## Success Metrics

1. **Quality Score** — Average validation score > 7/10
2. **First-pass Success** — > 70% pass without retry
3. **Domain Agent Satisfaction** — Brief → Output match > 85%
4. **Token Efficiency** — < 1000 tokens per visual job
5. **Time to Deliver** — < 60 seconds for images, < 120 for videos

## Files to Modify

1. `admin/workspace/agents/content.py` — Add reasoning chain steps
2. `admin/workspace/agents/content_templates.py` — Add reasoning prompts
3. `admin/workspace/agents/ads.py` — Update request_content format
4. `admin/workspace/agents/social.py` — Update request_content format
5. `admin/workspace/agents/seo.py` — Update request_content format (if exists)
6. `admin/workspace/agents/website.py` — Update request_content format (if exists)
7. `admin/tools/reasoning_logger.py` — New file for reasoning logs
8. `admin/api/routes/content.py` — Add reasoning API endpoints
9. `tests/test_reasoning_chain.py` — E2C tests

## Rollout Plan

1. Implement reasoning chain in content agent
2. Add reasoning logger
3. Update one domain agent (ads) as pilot
4. E2C test with ads agent
5. Roll out to remaining agents
6. Monitor quality metrics
