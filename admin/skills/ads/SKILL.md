# Ads Agent — Skill Reference

## Role
Performance marketing specialist. Full ownership of paid advertising strategy, execution, and optimization.

## Interview Reference (Q1-Q5)
- Q1: Meta (Facebook + Instagram) primary, Google Ads secondary — agent decides per client
- Q2: Full ownership — ad copy, creative briefs, budget allocation, optimization
- Q3: ROAS/ROI driven + multi-metric + auto-optimization loop
- Q4: Multi-layer error recovery (auto-optimize → aggressive → pause → report CEO)
- Q5: Automated audience discovery + prospecting/retargeting hybrid

## Platforms
- **Primary**: Meta (Facebook + Instagram), Google Ads
- **Secondary (per client)**: LinkedIn, TikTok, X (decided per client profile)

## 20 Real Tools

### Strategy (5)
1. `campaign_strategy` — Full campaign strategy with 3 phases (Launch/Optimize/Scale)
2. `audience_research` — Research target audiences by industry, product, platform
3. `budget_planner` — Budget allocation across prospecting/retargeting/testing
4. `competitor_ads` — Analyze competitor Ads Library strategies
5. `platform_selection` — Recommend platforms based on client profile + budget

### Content (5)
6. `ad_copy_generator` — Generate ad copy with 4 hook formulas (curiosity/pain_point/social_proof/urgency)
7. `creative_brief` — Detailed brief for Content Agent with specs + dimensions
8. `ad_variations` — A/B test variants with testing plan
9. `landing_page_strategy` — Landing page sections, tracking, optimization
10. `ad_hashtag_tags` — Branded/niche/campaign hashtags + UTM tags

### Targeting (4)
11. `audience_builder` — Build detailed audiences (interests, behaviors, segments)
12. `lookalike_audience` — LAL from converters with percentage variations
13. `retargeting_setup` — Full funnel retargeting (cart/video/engagers)
14. `exclusion_list` — Exclude converters/employees to prevent wasted spend

### Optimization (3)
15. `performance_analyzer` — Analyze metrics, detect issues, suggest fixes
16. `auto_optimize` — Rule-based auto-optimization (budget shift, pause, scale)
17. `ab_test_setup` — Configure A/B tests with statistical significance

### Reporting (3)
18. `campaign_report` — Full campaign report with platform breakdown
19. `roas_calculator` — ROAS/ROI calculation with gap analysis
20. `creative_score` — Score ad creative (0-100) with improvement suggestions

## Installed Jcode Skills (from skills.sh)

### Core Marketing Skills
| Skill | Source | Purpose |
|-------|--------|---------|
| `ads` | coreyhaines31/marketingskills | Full paid ads playbook — Meta Andromeda era, Google, LinkedIn, retargeting frameworks |
| `copywriting` | coreyhaines31/marketingskills | Ad copy frameworks — PAS/BAB, hook formulas, conversion copy |
| `analytics` | coreyhaines31/marketingskills | Conversion tracking, GA4, pixel setup, attribution |
| `landing-page-copywriter` | onewave-ai/claude-skills | Landing page copy that converts ad traffic |
| `marketing-council` | coreyhaines31/marketingskills | Multi-expert marketing consultation |

### How to Use These Skills
When the Ads Agent needs to:
- **Write ad copy** → Use `copywriting` skill (PAS/BAB frameworks, hook formulas)
- **Optimize landing pages** → Use `landing-page-copywriter` skill
- **Set up tracking** → Use `analytics` skill (GA4, pixels, conversion events)
- **Get expert consultation** → Use `marketing-council` skill

### Key Playbooks from `ads` Skill
- **Meta Andromeda Era (2026+)**: Statics > polished video, broad targeting + specific creative, identity-trigger keywords
- **4-Component Retargeting**: Objection-handling + proof carousel + other-offers CBO + value-first audit
- **Headline Mirror Trick**: Run 20-40 headline variations on Meta → mirror winning headline on landing page → 15-20% conversion lift
- **Zombie Campaigns**: Resurrect dead variants in separate ad sets
- **Net Cash > ROAS**: Scale until break-even ROAS ceiling, not until ROAS drops

## Workflow
1. Analyze client goals, budget, and industry
2. `platform_selection` → choose platform(s)
3. `audience_research` → define target audiences
4. `budget_planner` → allocate budget
5. `campaign_strategy` → create full strategy
6. `ad_copy_generator` → write ad copy (use `copywriting` skill for frameworks)
7. `creative_brief` → brief Content Agent for visuals
8. `ad_variations` → create A/B test variants
9. `landing_page_strategy` → plan landing page (use `landing-page-copywriter` skill)
10. Launch campaigns
11. `performance_analyzer` → monitor metrics (use `analytics` skill for tracking)
12. `auto_optimize` → auto-optimize based on rules
13. `campaign_report` → report to CEO

## Error Recovery (Multi-layer)
1. Auto-optimize (budget reallocation, creative rotation)
2. Aggressive optimization (pause failing, scale winning)
3. Pause (last resort — only if CPA > 3x target consistently)
4. Report to CEO with detailed analysis + recommendations

## Metrics Tracked
ROAS, ROI, CTR, CPC, CPA, CPM, Impression Share, Frequency, Conversion Rate, Cost per Conversion

## Communication
- **Reports to**: Workspace CEO + Agency-level Ads agent
- **Receives briefs from**: CEO (campaign goals)
- **Briefs**: Content Agent (ad creatives via agent_bus)
- **Coordinates with**: Analytics Agent (performance data), Social Agent (organic insights)

## API Routes (23)
- `GET /api/ads/status` — Agent status
- `GET /api/ads/tools` — List all 20 tools
- `POST /api/ads/campaign-strategy` — Create strategy
- `POST /api/ads/audience-research` — Research audiences
- `POST /api/ads/budget-planner` — Plan budget
- `POST /api/ads/competitor-ads` — Analyze competitors
- `POST /api/ads/platform-selection` — Select platform
- `POST /api/ads/ad-copy` — Generate ad copy
- `POST /api/ads/creative-brief` — Create creative brief
- `POST /api/ads/ad-variations` — Create variations
- `POST /api/ads/landing-page` — Landing page strategy
- `POST /api/ads/hashtag-tags` — Generate hashtags
- `POST /api/ads/audience-builder` — Build audience
- `POST /api/ads/lookalike` — Create lookalike
- `POST /api/ads/retargeting` — Setup retargeting
- `POST /api/ads/exclusions` — Build exclusion list
- `POST /api/ads/performance` — Analyze performance
- `POST /api/ads/auto-optimize` — Auto-optimize
- `POST /api/ads/ab-test` — Setup A/B test
- `POST /api/ads/report` — Generate report
- `POST /api/ads/roas` — Calculate ROAS
- `POST /api/ads/creative-score` — Score creative
- `POST /api/ads/brief-content-agent` — Brief Content Agent

## LangGraph
- Nodes: call_llm → run_tools → finalize
- Agent uses real tool registry from ads_tools.py
- State: AdsAgentState with tool_round tracking

## Interview Compliance
- Q1: Platform selection tool decides per client ✓
- Q2: Full ownership via all tools ✓
- Q3: ROAS-driven via roas_calculator + performance_analyzer ✓
- Q4: Multi-layer error recovery documented ✓
- Q5: Automated audience discovery via audience_research + lookalike ✓
