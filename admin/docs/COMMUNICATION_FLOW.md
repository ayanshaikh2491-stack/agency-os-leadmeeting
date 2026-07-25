# TAGS Content Agent — Communication Flow
## Domain Agent → Content Agent → Execution → Result═══════════════════════════════════════════════
STEP 1: DOMAIN AGENT BRIEF (Kaun, kya, kaise)
═══════════════════════════════════════════════════════════

Domain Agent (e.g. Social Media Agent) yeh data pack bhejta hai:

┌───────────────────────────────────────────────────────────────────┐
│ SOCIAL MEDIA AGENT                                                │
│                                                                   │
│  def create_weekly_content(self):                                 │
│      brief = {                                                    │
│          "to_agent": "content",          ← Content Agent ke liye  │
│          "message_type": "brief",        ← Brief hai yeh          │
│          "subject": "Fitness Motivation Week 12",                 │
│          "content": "Need 7 Instagram posts for fitness brand,    │
│                      each post needs image + caption,             │
│                      week theme: transformation journey",         │
│          "metadata": {                                            │
│              "content_type": "image",     ← Image chahiye         │
│              "platform": "instagram_square",  ← Platform          │
│              "style": "bold",             ← Brand style           │
│              "quantity": 7,               ← Kitne chahiye?        │
│              "priority": "normal",                                │
│              "reference": "previous week's best performer was     │
│                            transformation story posts"            │
│          }                                                        │
│      }                                                            │
│      agent_bus.send(brief)                  ← Queue me daal diya  │
│                                                                   │
│      → Console: "Brief sent to Content Agent"                    │
└───────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════
STEP 2: AGENT BUS (Brief queue me store ho gaya)
═══════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────┐
│ AGENT BUS (admin/workspace/agent_bus.py)                          │
│                                                                   │
│  Queue me yeh gaya:                                               │
│  {                                                                │
│    "id": "msg_1745",                                              │
│    "from": "social",                                              │
│    "to": "content",                                               │
│    "type": "brief",                                               │
│    "subject": "Fitness Motivation Week 12",                       │
│    "body": "Need 7 Instagram posts...",                           │
│    "meta": {content_type: "image", platform: "instagram", ...},   │
│    "status": "unread",            ← Content Agent ne nahi dekha   │
│    "created": "2026-07-25T15:30:00"                               │
│  }                                                                │
└───────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════
STEP 3: CONTENT AGENT WORKER (process_pending_briefs)
═══════════════════════════════════════════════════════════

E2C background worker har kuch der poll karta hai:

┌───────────────────────────────────────────────────────────────────┐
│ CONTENT AGENT (content.py)                                        │
│                                                                   │
│  async def process_pending_briefs(self):                          │
│      briefs = agent_bus.get_messages(to="content", unread=True)   │
│                                                                   │
│      for brief in briefs:  ← Har unread brief uthao              │
│                                                                   │
│          Step 3A: Brand auto-discovery                            │
│          ─────────────────────────────────────                    │
│          if not brand_discovered:                                 │
│              result = chrome.goto(client_website_url)             │
│              result = chrome.extract_colors()                     │
│              result = chrome.get_logo()                           │
│              → Brand colors: ["#FF6600", "#0066FF"]              │
│              → Brand style: "Bold, energetic"                    │
│                                                                   │
│          Step 3B: Content Agent LLM decide karega                 │
│          ─────────────────────────────────────                    │
│          LLM input: brief + brand_colors + platform_sizes         │
│                                                                   │
│          LLM sochta hai:                                          │
│          ```think                                                  │
│          Brief: 7 Instagram posts, fitness transformation         │
│          Platform: instagram_square → 1080x1080                   │
│          Brand colors: orange #FF6600, blue #0066FF               │
│          Style: bold → "bold typography, high contrast"          │
│                                                                   │
│          Plan:                                                    │
│          Day 1: "Starting point" → image + caption               │
│          Day 2: "First workout" → image + Day 3: "Nutrition change" → image + caption             │
│          Day 4: "Progress pic" → image + caption                  │
│          Day 5: "Milestone" → image + caption                     │
│          Day 6: "Transformation" → image + caption                │
│          Day 7: "New lifestyle" → image + caption                 │
│                                                                   │
│          Tools needed: generate_text (7 captions)                 │
│                       generate_image_via_colab_chrome (7 images)  │
│          ```                                                      │
│                                                                   │
│          Step 3C: TOOLS EXECUTE                                    │
│          ─────────────────────                                    │
│                                                                   │
│          # Day 1                                                 │
│          tool_call_1 = generate_text(brief="Starting caption      │
│                           for fitness transformation...",         │
│                           platform="instagram")                   │
│              → Ollama CPU → 3 sec → "Every journey starts       │
│                 with a single step... #Fitness"                   │
│                                                                   │
│          tool_call_2 = generate_image_via_colab_chrome(           │
│              prompt="Professional Instagram post, fitness,        │
│                      bold style, brand colors orange blue,        │
│                      text overlay 'Day 1: Start',                 │
│                      1080x1080, professional quality",              │
│              platform="instagram_square"                          │
│          )                                                        │
│              → Chrome opens Colab → FLUX T4 GPU                   │
│              → 5 min waiting...                                   │
│              → SUCCESS: output.png (1080x1080, 512KB)            │
│                                                                   │
│          # Day 2 (same pattern)                                  │
│          ...                                                      │
│                                                                   │
│          # Day 3 (same pattern)                                  │
│          ...                                                      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════
STEP 4: COLAB GENERATION (EXACT VISUAL)
═══════════════════════════════════════════════════════════

Jab generate_image_via_colab_chrome call hota hai:

┌───────────────────────────────────────────────────────────────────┐
│ CHROME_TOOL → REAL CHROME                                         │
│                                                                   │
│  1. goto("https://colab.research.google.com")                     │
│     → User ka Chrome window dikhega: Colab open hota hai          │
│                                                                   │
│  2. press("Control+n")                                            │
│     → Naya notebook bana                                          │
│                                                                   │
│  3. eval(JAVASCRIPT_CODE) ← 2 sec me code paste                  │
│     → FLUX code cell me aa gaya                                   │
│                                                                   │
│  4. press("Control+F9")  ← Run all                                │
│     → Colab GPU chalu                                             │
│                                                                   │
│  5. Poll... wait...                                                │
│     "Installing dependencies..."                                   │
│     "GPU: Tesla T4"                                               │
│     "Loading FLUX.1-dev..."                                       │
│     "Generating: Day 1: Start..."                                 │
│     "✅ SUCCESS: output.png (512KB)"                               │
│                                                                   │
│  6. files.download() → Browser download trigger                   │
│                                                                   │
│  TOTAL TIME: ~5-8 minutes                                        ───────────────────┘═══════════════
STEP 5: RESULT WAPAS DOMAIN AGENT KO
═══════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────┐
│ CONTENT AGENT ne sab khatam kiya                                  │
│                                                                   │
│  Final output:                                                    │
│  {                                                                │
│    "workspace": "fitlife",                                        │
│    "brief_from": "social",                                        │
│    "brief_subject": "Fitness Motivation Week 12",                 │
│    "results": [                                                   │
│      {                                                            │
│        "day": 1,                                                  │
│        "image": "outputs/fitlife/week12/day1_start.png",          │
│        "caption": "Every journey starts with a single step...     │
│                    #FitnessMotivation #Transformation",           │
│        "size": "1080x1080",                                       │
│        "format": "image/png"                                      │
│      },                                                           │
│      {                                                            │
│        "day": 2,                                                  │
│        "image": "outputs/fitlife/week12/day2_workout.png",        │
│        "caption": "Sweat is just your fat crying...               │
│                    #WorkoutMotivation",                            │
│        "size": "1080x1080",                                       │
│        "format": "image/png"                                      │
│      },                                                           │
│      ... 5 more days                                              │
│    ],                                                             │
│    "stats": {                                                     │
│      "total_images": 7,                                           │
│      "total_captions": 7,                                         │
│      "total_time_minutes": 42,                                    │
│      "brand_colors_used": ["#FF6600", "#0066FF"],                │
│      "models_used": ["FLUX.1-dev", "phi3.5:3.8b-mini"]          │
│    }                                                              │
│  }                                                                │
│                                                                   │
│  agent_bus.send({                                                 │
│      "from": "content",                                           │
│      "to": "social",                                              │
│      "type": "response",                                          │
│      "subject": "Week 12 content ready!",                         │
│      "body": "7 posts completed. Images in outputs/week12/"       │
│  })                                                               │
└───────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════
STEP 6: SOCIAL MEDIA AGENT RESULTS DEKHTA HAI
═══════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────┐
│ SOCIAL MEDIA AGENT                                                │
│                                                                   │
│  Response mila Content Agent se:                                  │
│  "7 posts ready!"                                                 │
│                                                                   │
│  Agent check karta hai:                                           │
│  ├── output_fitlife_week12_day1.png ← Image ready                │
│  ├── Caption: "Every journey starts..."                          │
│  ├── Output_fitlife_week12_day2.png ← Image ready                │
│  ├── Caption: "Sweat is just..."                                  │
│  ├── ...                                                         ── Output_fitlife_week12_day7.png ← Image ready                │
│                                                                   │
│  Agent: "Post karne ke liye schedule set karo!"                 ───────────────────────────────────┘

═══════════════════════════════════════════════════════════
SUMMARY: EXACT DATA FLOW (JSON ke saath)
═══════════════════════════════════════════════════════════

┌────────────┐         ┌──────────────┐         ┌───┐
│   ──①──►  AGENT BUS    │  ──②── CONTENT       │
│  AGENT      │  brief   (queue)      │  unread   AGENT WORKER  │
│             │         │              │         │               │
│  brief = {  │         │  {           │         │  ③ LLM decide │
│   to:"content"│       │   from:social│         │  "image+text" │
│   type:"image"│       │   to:content │         │               │
│   platform:"ig"│      │   status:    │         │  ④ TOOLS:     │
│   topic:"fit"│        │    "unread"  │         │  Ollama text  │
│   quantity:7 │        │  }           │         │  Colab image  │
│  }           │         │              │         │               │
└──────┬───────┘         └──────────────┘         └───────
       │                                                  │
       │  ⑥ Result wapas                                  │ ⑤ Output
       │                                                  │
       │    ┌────────────────────────────┐               │
       └────│  "7 posts ready!"          │◄──────────────┘
            │  images + captions         │
            │  brand colors applied      │
            └────────────────────────────┘
