# Social Media Agent — Organic Growth Engine (Design)

> Date: 2026-08-05
> Status: Approved by user (all sections)
> Scope: Full design for Social Agent upgrade from post-only to organic growth engine

---

## 1. Vision

Social Media Agent abhi sirf posts/reels banata aur post karta hai. Naya vision:
**Organic growth engine** — bina ads ke business awareness + selling, har major social platform ke real channels se.

- FB Groups me relevant posts (jahan target customers hain)
- Reddit me genuine value + soft presence
- FB Marketplace me product listings
- LinkedIn/X/Pinterest/Telegram/Google Business — API-based posting
- Jo bhi engage kare → lead banao → SBA pipeline me bhejo → auto-reply
- **24/7 operation** — EC2 pe systemd service, SBA autopilot jaisa

## 2. Confirmed Choices

| Feature | Choice |
|---|---|
| Channels (Phase 1) | FB Groups, FB Marketplace, Reddit, LinkedIn, X, Pinterest, Telegram, Google Business |
| Channels (Phase 3, deferred) | WhatsApp Status (browser), Quora (browser) |
| Posting method | **Hybrid**: API (Reddit/LinkedIn/X/Pinterest/Telegram/GBP) + Browser (FB Groups/Marketplace, ChromeTool session) |
| Workflow | Manual command + Autopilot scheduler (dono) |
| Leads | Track engagement → SBA lead + auto-reply follow-up |
| Availability | 24/7 (EC2 systemd service, SBA autopilot pattern) |
| Structure | **Modular** `admin/tools/organic/` — ek module = ek channel |

## 3. Architecture

### 3.1 Module Layout

```
admin/tools/organic/
  __init__.py
  base.py               # PostRequest, PostResult, ChannelMeta models + validation + logging
  registry.py           # channel registry: id, type (api|browser), capabilities, auth mode
  hub.py                # organic_post(channel, payload) → router to correct module
  reddit_api.py         # Reddit (PRAW) — subreddit post + comment
  linkedin_api.py       # LinkedIn API — profile/page share post
  twitter_api.py        # X API v2 — tweet + reply (media support)
  pinterest_api.py      # Pinterest API — pin (image + link)
  telegram_api.py       # Telegram Bot API — message/photo/link to channel/group
  gbp_api.py            # Google Business Profile — post/offer
  facebook_browser.py   # FB Groups + FB Marketplace — ChromeTool (browser)
```

### 3.2 Channel Registry Pattern

Har module ek `CHANNEL_META` dict expose karega:

```python
CHANNEL_META = {
    "id": "reddit",
    "type": "api",                # api | browser
    "capabilities": ["post", "comment"],  # kya kar sakta hai
    "auth": "token",              # token | browser_session
    "name": "Reddit",
}
```

- `registry.py` loads all `CHANNEL_META` → frontend ko channel list deta hai
- `hub.py` uses this to route posts
- Frontend "Organic Channels" panel isi se UI banata hai

### 3.3 Hub Contract

```python
def organic_post(channel: str, payload: dict) -> PostResult:
    """Route to correct module. Validates, posts, returns standard result."""
```

`PostResult`:
```python
@dataclass
class PostResult:
    status: str          # published | queued | error
    channel: str
    post_id: str = ""
    post_url: str = ""
    error: str = ""
    published_at: str = ""
```

## 4. Per-Platform Details

### API-based channels (token connect → real post)

| Channel | Library/API | Post types | Notes |
|---|---|---|---|
| Reddit | PRAW | text post, link post, comment | karma/cooldown respect karega |
| LinkedIn | LinkedIn API | text/share | profile + company page |
| X/Twitter | API v2 | tweet + reply | image media |
| Pinterest | Pinterest API | pin (image+link) | product boards |
| Telegram | Bot API | message/photo/link | bot channel/group |
| Google Business | GBP API | post/offer/event | local business |

### Browser-based channels (ChromeTool session — client pehle login karega)

| Channel | Action | How |
|---|---|---|
| FB Groups | group post | ChromeTool → group page → post box → type → submit |
| FB Marketplace | product listing | ChromeTool → create listing → item details form |

### Common module pattern
1. **Validate** — auth present, required fields (subreddit, group URL, etc.)
2. **Post** — API call / browser action
3. **Result** — standard `PostResult`
4. **Log** — reasoning_logger / SBA log style (frontend pe visible)

### Rate limiting (account ban se bachao)
- Har channel ka safe daily limit (FB groups 3-5/day, Reddit 5-10/day, Twitter 15-20/day)
- Per-channel cooldown min interval
- Browser posting me existing `chrome_tool.py` delays (1-3.5s typing, random clicks) reuse karo

## 5. Lead Capture + Auto-Reply (Phase 2)

### Flow
```
Post published (any channel)
  ↓
Monitor loop (har 30-60 min, scheduler me)
  ↓
1. Reddit: PRAW → post ke naye comments fetch
2. FB Groups: ChromeTool → post comments scrape
3. LinkedIn/X/Pinterest: API → post insights/mentions
4. Telegram: bot → message replies
  ↓
Filter genuine engagement (spam/bot nahi)
  ↓
Lead banao:
  - username, platform, post, message → SBA lead
  - status: "social_lead", source: "reddit/facebook/..."
  - contact info DM me mili → enrich
  ↓
Auto-reply (15-30 min ke andar):
  - platform-specific template, natural lage, spammy nahi
  - genuine interest → DM/comment follow-up + CTA
  - interested lead → SBA pipeline (meeting scheduling)
```

### Key decisions
- **Spam detection**: "price?", "interested", "how to buy" → hot lead. "nice post" → thank-you only.
- **Auto-reply tone**: Reddit value-first, FB group direct offer OK, Telegram strong CTA.
- **Privacy**: Personal DMs sirf tab jab interest dikhaya. High-risk actions manual approval queue.

## 6. Autopilot + Strategy (Phase 3)

### Flow
```
Content Bank:
  - Content Agent briefs (request_content already hai)
  - Manual input
  - Superpower skills (ad-creative, social) — Phase 3
  ↓
Autopilot Scheduler (har hour):
  - kaunsa content kis channel pe kab post
  - best time per channel (platform intelligence already social_tools me)
  - purana content repurpose (rotating, spammy nahi)
  ↓
Post → monitor (Phase 2) → leads → SBA pipeline
  ↓
Weekly report: posts, engagement, leads, meetings, channel breakdown
```

### 24/7 Operation
- **EC2 systemd service** `social-autopilot.service` — SBA autopilot pattern
- `scheduler.py` me social job add karo (hourly check)
- Har autopilot post ke liye manual approval toggle (default ON)
- Logs → journald / SBA log file, frontend status endpoint

### Integration
- `scheduler.py` (SBA autopilot) me social job add
- `sba_pipeline.py` se leads link (social lead → pipeline)
- `analytics.py` me social metrics (posts, engagement, social leads)
- Frontend social page pe "Autopilot" toggle + status + Organic Channels panel

## 7. Testing Strategy

- **Unit tests per module**: registry, hub routing, validation, rate limiting
- **Mock API tests**: har API module fake response ke saath
- **Browser tests**: ChromeTool daemon integration (login session required — manual test first, then automate)
- **E2E**: post → lead capture → auto-reply → SBA lead, sab mocked environment me
- **Existing test suite**: `pytest` — ensure koi bhi existing test break na ho

## 8. Phases

| Phase | Scope | Deliverable |
|---|---|---|
| 1 | Posting Engine | `organic/` modules + hub + registry, API channels live, FB browser base, social_tools integration, frontend panel |
| 2 | Lead Capture + Auto-reply | monitor loop, SBA lead integration, auto-reply |
| 3 | Autopilot + Strategy | scheduler, 24/7 service, weekly report, superpower content integration |

## 9. Out of Scope (abhi)

- Paid ads
- Email/SMS outreach (SBA already handles)
- Client-facing social dashboard (internal admin only)
- WhatsApp API (requires Business API approval — WhatsApp Status via browser later)
- Quora (requires browser automation — Phase 3 consideration)
