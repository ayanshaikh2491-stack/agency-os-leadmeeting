═══ TAGS AGENCY OS — CONTENT GENERATION PLAN ═══
═══════════════════════════════════════════════════

IMPORTANT: Content Agent = VISUAL ONLY (images + videos)
Text ka kaam domain agents khud karte hain (SEO, Social, Ads, Website)

═══ PHASE 1: JO ABHI HAI (ALREADY DONE) ═══

✅ Content Agent (LangGraph pipeline) — content.py (749 lines)
✅ Workspace Content Store — content_store.py (per-workspace memory)
✅ Agency Content Agent — content_agent.py (cross-project learning)
✅ Visual tools — generate_image, generate_video, generate_ad, generate_social, generate_hero
✅ Kaggle GPU integration — FLUX images + CogVideoX videos
✅ Brand discovery — website se brand identity scan
✅ Content API routes — /api/content/* endpoints
✅ Skill reference — SKILL.md updated (visual only)
✅ Job queue — on-demand GPU, priority ordering, auto-retry

═══ PHASE 2: KYA BAKI HAI ═══

1. chrome_kaggle.py — JavaScript injection fix
   → Abhi character-by-character paste ho raha hai (10 min)
   → JS injection se 2 sec mein hoga
   → ChromeTool se Colab notebook mein code paste

2. process_pending_briefs() — Full pipeline wire
   → Queue se brief uthao
   → Content Agent sochta hai: image/video kaunsa, kaise
   → Appropriate visual tool fire karo
   → Result domain agent ko bhejo

3. Brief system ka integration
   → Domain Agent VisualBrief bhejta hai
   → Content Agent brief parse karta hai
   → Brand context add karta hai
   → GPU pe generate karta hai

4. CEO approval flow
   → Content Agent generate karta hai
   → CEO ko approval ke liye bhejta hai
   → Approved → domain agent ko deliver

═══ FLOW: DOMAIN AGENT → CONTENT AGENT ═══

──────────────────────────────────────────
CASE 1: Image Content (Poster, Ad, Social Post)
──────────────────────────────────────────

Domain Agent: "Fitness Instagram post ke liye image chahiye, motivational"

↓ VisualBrief queue me jaata hai

Content Agent uthata hai brief:
  → LLM sochta hai: "Image chahiye, FLUX se karunga"
  → Brand context dekhta hai (client ke colors, style)
  → Expert prompt banata hai FLUX ke liye
  → Tool: generate_image(prompt, platform="instagram")
  → Kaggle GPU pe FLUX run hota hai
  → Image generate hoti hai (30 sec)
  → Result domain agent ko bhejta hai

──────────────────────────────────────────
CASE 2: Video Content (Reel, Ad Video)
──────────────────────────────────────────

Domain Agent: "Product launch ke liye 6 sec video chahiye"

↓ VisualBrief queue me jaata hai

Content Agent:
  → LLM sochta hai: "Video chahiye, CogVideoX se karunga"
  → Tool: generate_video(prompt, duration=6)
  → Kaggle GPU pe CogVideoX run hota hai
  → Video generate hoti hai (5-10 min)
  → MP4 download hota hai
  → Result domain agent ko bhejta hai

──────────────────────────────────────────
CASE 3: Ad Creative (Multi-platform)
──────────────────────────────────────────

Ads Agent: "Facebook ad ke liye 3 sizes chahiye — 1200x628, 1080x1080, 1200x1500"

↓ VisualBrief queue me jaata hai

Content Agent:
  → Tool: generate_ad_image(prompt, platform="facebook")
  → 3 alag-alag sizes generate karta hai
  → Brand consistent rakhta hai
  → Results Ads Agent ko bhejta hai

═══ ARCHITECTURE ═══

┌─────────────────────────────────────────────────────────┐
│                  CONTENT AGENT (LangGraph)                │
│                                                          │
│  ┌──────────────────────────────────┐                    │
│  │  Step 1: Brief samjhe            │                    │
│  │  Step 2: Brand context dekhe     │                    │
│  │  Step 3: Visual plan banaye      │                    │
│  │  Step 4: Expert prompt likhe     │                    │
│  │  Step 5: Generate kare           │                    │
│  │  Step 6: Report kare             │                    │
│  └────────┬────────────┬───────────┘                    │
│           │            │                                │
│           ▼            ▼                                │
│  ┌────────────┐ ┌──────────────────┐                    │
│  │  FLUX       │ │  CogVideoX       │                   │
│  │  (Images)   │ │  (Videos)        │                   │
│  └────────────┘ └──────────────────┘                    │
│                                                          │
│  ┌──────────────────────────────────┐                    │
│  │  Workspace Content Store          │                   │
│  │  (per-client memory)              │                   │
│  └──────────────────────────────────┘                    │
│                                                          │
│  ┌──────────────────────────────────┐                    │
│  │  Agency Content Agent             │                   │
│  │  (cross-project learning)         │                   │
│  └──────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘

═══ JO CHANGE KARNA HAI ═══

1. admin/tools/chrome_kaggle.py
   → JavaScript injection fix (fast paste)

2. admin/workspace/agents/content.py
   → process_pending_briefs() complete karo
   → Brief system properly wire karo

═══ SETUP ═══

1. Kaggle API token configured hona chahiye
2. Chrome running hona chahiye (ChromeTool ke liye)
3. Colab me login: https://colab.research.google.com

═══ WHAT CONTENT AGENT DOES NOT DO ═══

❌ Blog posts → SEO Agent
❌ Ad copy → Ads Agent
❌ Social captions → Social Agent
❌ Website copy → Website Agent
❌ Meta descriptions → SEO Agent
❌ Content calendars → Domain Agents
❌ Content strategy → Domain Agents
❌ Readability analysis → SEO Agent
❌ Content repurposing → Domain Agents
