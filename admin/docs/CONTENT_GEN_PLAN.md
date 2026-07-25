═══ TAGS AGENCY OS — CONTENT GENERATION PLAN ═══
═══════════════════════════════════════════════════

YEH HAI PURA PLAN — KAISE KAAM KAREGA
═══════════════════════════════════════════════════

═══ PHASE 1: JO ABHI HAI (ALREADY DONE) ═══

✅ Admin Agent → Agents ko tasks allocate karta hai
✅ Domain Agents (Ads, Social, SEO, Website) → Brief create karte hain
✅ Content Agent → Brief receive karta hai
✅ ChromeTool → Connected hai real Chrome se (CDP)
✅ chrome_kaggle.py → Notebook code templates ready hain (FLUX + CogVideo)
✅ _execute_unified_tool → Async hai, Chrome tools route karta hai

═══ PHASE 2: KYA BANEGA (NEXT) ═══

Naya module: admin/tools/local_gen.py
  → Ollama API se connect hoga (text generation)
  → Har workspace ka apna model cache
  → 24/7 background me text generate karega

Fix: chrome_kaggle.py me colab code paste
  → JavaScript injection se paste karega (2 sec)
  → Abhi character-by-character type kar raha hai (10 min)

Wire: process_pending_briefs → Content Agent
  → Queue se brief uthao
  → Content LLM decide kare: text/image/video
  → Appropriate tool fire karo
  → Result wapas b PHASE 3: FINAL USER EXPERIENCE ═══

──────────────────────────────────────────
CASE 1: Text Content (Blog, Caption, Copy)
──────────────────────────────────────────

Domain Agent: "Social media post chahiye fitness brand ke liye"

↓ Brief queue me jaata hai

Content Agent uthata hai brief:
  → LLM sochta hai: "Sirf text chahiye, local Ollama se kar skta hoon"
  → Tool: generate_text(prompt, platform, tone)
  → Ollama API (localhost:11434) → phi3.5 model CPU pe run
  → 2-5 sec me caption ready
  → Result domain agent ko bhejta hai

User dekhega: Kuch nahi — background me ho gaya

──────────────────────────────────────────
CASE 2: Image Content (Poster, Ad, Social──

Domain Agent: "Fitness Instagram post ke liye image chahiye, motivational"

↓ Brief queue me jaata hai

Content Agent uthata hai brief:
  → LLM sochta hai: "Image bhi chahiye text bhi"
  → Step 1: Text → Ollama (caption likh diya, 2 sec)
  → Step 2: Image generate_image_via_colab_chrome()

      ChromeTool → Chrome opens colab.research.google.com
      │
      ├── File → New notebook (Control+N)
      ├── Wait 3 sec for load
      ├── Code cell find karo
      ├── JavaScript injection → FLUX code paste (2 sec!)
      ├── Runtime → Change runtime type → T4 GPU
     +Enter → Run cell
      │
      │   Colab ke ANDAR:
      │   ┌──────────────────────────────────┐
      │   │ pip install diffusers...         │ (30 sec)
      │   │ GPU: T4 detected                  │
      │   │ Loading FLUX.1-dev model...       │ (2-3 min)
      │   │ Generating image...               │ (30 sec)
      │   │ ✅ SUCCESS: output.png           │
      │   │ files.download(output.png) → DL  │
      │   └──────────────────────────────────┘
      │
      ├── Chrome download trigger hota hai
      ├── Download complete (5-10 sec)
      │
      ↓ Result: {"status": "completed", "file": "output.png"}

  → Step 3: Dono combine karo (image + caption)
  → Result domain agent ko bhejo

User dekhega:
  → Chrome window dikhegi (Colab open hote hue)
  → Code paste hote hue dikhega
  → Notebook run hote hue dikhega
  → Download hote hue dikhega
  → Phir Chrome tab close ho jayega

──────────────────────────────────────────
CASE 3: Video Content (Reel, Ad Video)
──────────────────────────────────────────

Domain Agent: "Product launch ke liye 6 sec video chahiye"

↓ Same flow as image

Content Agent:
  → Tool: generate_video_via_colab_chrome()
  → ChromeTool → Colab open
  → CogVideoX code paste
  → GPU run → 5-10 min wait
  → MP4 download

═══ ARCHITECTURE DIAGRAM ═══

┌─────────────────────────────────────────────────────────┐
│                     E2C WORKER (24/7)                     │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                    │
│  │  Redis Queue  │    │  File System  │                   │
│  │  (briefs in)  │    │  (outputs)    │                   │
│  └──────┬──────▲────────┘                   │
│         │                   │                            │
│         ▼───────────────────┘                            │
│  ┌──────────────────────────────────┐                    │
│  │       CONTENT AGENT (LangGraph)   │                    │
│  │                                  │                    │
│  │  Node: content_call_llm          │                    │
 LLM decides tools           │                    │
│  │                                  │                    │
│  │  Node: content_execute_tools     │                    │
│  │    → _execute_unified_tool()     │                    │
│  └────────┬────────────┬───────────┘                    │
│           │            │                                │
│           ▼            ▼                                │
│  ┌────────────┐ ┌──────────────────┐                    │
│  │  Ollama     │ │  ChromeTool      │                    │
│  │  (localhost)│ │  (CDP -> Chrome)  │                   │
│  │  phi3.5     │ │                   │                    │
│  │  text only  │ │  goto, click,     │                    │
│  │  2-5 sec    │ │  fill, eval,      │                    │
│  │            │ │  screenshot       │                    │
│  └────────────┘ └────────┬──────────┘                    │
│                          │                               │
│                          ▼                               │
│               ┌────────────────────┐                     │
│               │  Google Colab       │                     │
│               │  (free T4 GPU)      │                     │
│               │                     │                     │
│               │  FLUX -> Image      │                     │
│               │  CogVideoX -> Video  │                    │
│               └────────────────────┘                     │
└─────────────────────────────────────────────────────────┘

═══ FILES JO CHANGE HONGE ═══

1. NEW: admin/tools/local_gen.py
     → Ollama API client
     → generate_text() function
     → TEXT_TOOLS definitions
     → execute_text_tool() dispatch

2. MODIFY: admin/tools/chrome_kaggle.py
     → colab_paste_code → JavaScript injection (fast)
     → _build_flux_code → better error handling
     → COLAB_GPU_SELECTORS → updated selectors

3. MODIFY: admin/workspace/agents/content.py
     → Import local_gen tools
     → Add TEXT_TOOLS to ALL_CONTENT_TOOLS
     → _execute_unified_tool → route to Ollama text tools
     → Wire process_pending_briefs() → full pipeline
     → System prompt → updated tools list

═══ SETUP EK BAAR KARNA HOGA ═══

1. Download Ollama: https://ollama.com/download
2. CMD me run:
     ollama pull phi3.5:3.8b-mini
     (sirf 2 GB download, CPU pe chalega)
3. ChromeTool ke liye Chrome daemon already chal raha hoga
4. Colab me login: https://colab.research.google.com
     (ek baar login karo, cookies save ho jayengi)

═══ TIMELINE ═══

Day 1:
 local_gen.py banao (Ollama text)
  → chrome_kaggle.py fix karo (JS injection)
  → Sab compile verify karo

Day 2:
  → content.py wire karo
  → process_pending_briefs() complete karo
  → System prompt update karo

Day 3:
  → Test karo real Chrome + Colab
  → Test karo Ollama text
  → Test full flow domain agent → content agent → output
