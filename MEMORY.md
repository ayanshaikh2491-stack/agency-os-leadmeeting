# Agency OS — Project Memory

> Persistent knowledge for the Agency OS (TAGS Agency) build. The in-tool
> `memory` backend was non-persistent in this environment, so this file is the
> source of truth. Update it as work progresses.

## ⛔ DATABASE DECISION (HARD RULE — user stated repeatedly, 2026-08-25)
- **PocketBase (self-hosted) is THE database for EVERYTHING.** Do NOT default to
  SQLite for any new system. No exceptions.
- User was frustrated I kept falling back to SQLite. Locked: every agent, every
  system (agency-os + sba-backend) MUST persist to the self-hosted PocketBase.
- Current reality (MUST be fixed): sba-backend (8000) → PocketBase ✅;
  agency-os (9002) → currently SQLite (config/settings.py default) ❌ — needs
  migration to PocketBase so there is ONE db for all.
- Only SBA agent has a real production backend. Other 6 agents (seo/social/
  content/ads/website/analytics) have graphs but no PocketBase-backed prod
  workflow yet — build them on PocketBase too.

## What this is
- Multi-agent SEO / AI-visibility ("Agency OS") system for agency TAGS.
- Repo: `C:\Users\TAUSHEF\Downloads\int`, branch `feat/sba-lead-to-meeting-pipeline`.
- AEO/GEO (AI visibility) is the product core. Wired into SBA, CEO, SEO,
  Website, Content, Social, Ads agents. 17 AEO/GEO tests pass.

## Commits (this effort)
- `39e062c` — AEO/GEO into Ads + Social agents (per-workspace angles).
- `b7cff5f` — prove Social + Ads agent CORE works (graph/tools/LLM prompt).
- `1efee96` — Social Media Agent real research via Agent-Reach (free channels).
- `9c2224b` — fix social-reach: topic-specific real data via DuckDuckGo + parse snippets.

## Agent-Reach integration (Social Media Agent only)
- Repo `https://github.com/Panniantong/Agent-Reach.git` bundled at
  `admin/tools/agent_reach/` (53 files).
- Only FREE zero-config channels used: **Web (Jina Reader `r.jina.ai`) + V2EX
  public API**. No API keys, ₹0, no Chrome.
- Wrapper `admin/tools/social_reach.py` -> `reach_trending`, `reach_competitor`,
  `reach_hashtags`, `reach_audience`.
- `admin/tools/social_tools.py` wires the 4 previously-fake research tools to
  the wrapper. **No other agent touches Agent-Reach.**

## Key technical gotchas (social_reach web search)
- Google direct -> `403 Forbidden`. Use DuckDuckGo/Bing HTML via Jina:
  `https://r.jina.ai/https://duckduckgo.com/html/?q=<urlencoded query>`.
- Query MUST be `urllib.parse.quote(...)`'d or Jina rejects with
  "only public HTTP(S) URLs are allowed".
- Parse: split text on `\n## `, heading = `^\[(title)\]\((url)\)`, snippet is a
  later markdown-link line `[text](duckduckgo-redirect-url)`.
- BUG FIXED: old code tested `duckduckgo.com` on the RAW line and dropped the
  whole snippet line. Now test the LINK TEXT, not the raw line.
- V2EX `get_node_topics(<topic>)` 404s for non-V2EX topics (it is a
  Chinese-tech community). `get_hot_topics()` returns global tech noise
  (voice input, keyboards) — off-topic for plumber/roofer. Only use V2EX for
  known nodes (tech/python/jobs/etc); otherwise rely on Web.

## User preferences
- Hinglish; simple words + real examples; **proof not jargon**; direct answers.
- Strictly ₹0, lightweight, no Chrome, no heavy EC2.
- Per-workspace/agent isolation (agents not locked).
- SEO = AI-visibility core; Website=infrastructure, Content=flesh,
  Social=light brand-entity, Ads=entity-consistent copy.
- Commit as you go. Use superpower workflow
  (using-superpowers -> brainstorming -> writing-plans -> implementation).
- Wants **topic-specific REAL data** (e.g. "plumber"), not generic global trends.

## Windows / tooling quirks
- No `head`/`tail` -> use `more` or Python scripts.
- `python -c "..."` one-liners FAIL ("unterminated string literal") -> use a
  `_script.py` file.
- `npx skills` broken -> `git clone`.
- `findstr`/`agentgrep` miss Unicode -> use Python `ast`.
- Git `index.lock` sometimes sticks -> delete manually.
- Scratch files (`_agent_reach/`, `_munder/`, `ec2_*.log`, `_audit_*.py`,
  `_test_*.py`, `_dbg_*.py`, `_social_research_demo.py`, etc.) auto-create ->
  NEVER commit; only stage relevant files.
- LF->CRLF warnings are harmless.
- Tests live in `admin/tests/`; full `pytest` is slow (network calls) -> run
  targeted files. `test_social_reach.py` = 9 tests; AEO/GEO + core = 21 more.

## Verified result (after fix)
`reach_trending("plumber")` returns plumber-specific real results
("6 Tips for New Plumbers...", "Plumbing Forums", "21 Reliable Plumbing Blogs"),
NOT global V2EX noise. Same for roofer / salon / yoga studio (topic-specific).
Snippets now populate correctly.

## Honest agent readiness (2026-08-25 structural scan)
- 7 agents each import OK + `build_*_graph(): OK -> CompiledStateGraph` +
  Agent class present: sba, seo, social, ads, website, content, analytics.
- "Graph builds" != "end-to-end works". Real run needs WORKSPACE_API_KEY/model.
  Earlier "5/6 ready" claim was shallow (only grepped function bodies for
  requests/open). User rightly corrected: structural proof is import+build, not
  grep. SBA lead-capture funcs (detect_lead_sources/save_lead_record/email
  format_template) were placeholders but now real (see code).

## User's product vision (from chat)
- Agents must be SMART (LLM-driven decisions, context-aware), NOT dumb bots.
- Run on-DEMAND under CEO command; do NOT run 24/7 (keeps server light/cheap).
  CEO says "go" -> agent works; CEO says "rest" -> agent idles. Idle = standby,
  not always-on loop.
- New agent dropping in should AUTO-integrate: its tools + skills auto-discovered
  via a registry/plugin model. External user data entering should also integrate.
- Company owner gives work + work gets done. 7 agents (or any new agent) get
  tools + skills and integrate automatically.
- This is the NEXT design goal beyond per-agent readiness.

## Reference project: Munder Difflin (THE inspiration for this Agency OS)
- **What it is**: free, open-source, local-first multi-agent harness by
  @chaitanyagiri. Each agent = a real `claude` CLI process; a 2D "office floor"
  visualizes them. Wraps Claude Code, Codex, Copilot, etc (your existing subs).
- **Repo**: `https://github.com/chaitanyagiri/munder-difflin` (MIT, ~2.5k stars).
- **Cloned locally** at `references/munder-difflin/` (shallow `--depth 1`).
  `.gitignore` excludes `/references/` so the 1785-file clone is NEVER committed
  (keeps our repo light). Read it for architecture patterns; don't copy its code.
- **Its CEO = "god agent"** (`desk-ceo`, `isGod` flag): an ordinary `claude`
  process, *always-on listener* that runs the floor — EXACTLY our user's CEO model.
- **Idle agents wake only when they hold unread inbox messages** (Stop-hook drains
  inbox) — EXACTLY "agents sleep by default, wake on CEO command, self-sleep when
  done". No 24/7 loops; event-driven.
- **Key patterns to borrow** (from its `HIVE.md`, `SPEC.md`, `DESIGN.md`):
  - Single-writer registry (`registry.json`): roster + capabilities + status.
  - Markdown-first memory per agent (`memory.md`) + shared blackboard (`board.md`).
  - Message schema (FIPA-lite speech acts): request/inform/propose/query/agree/
    refuse/done, with `hops` cap to kill ping-pong loops.
  - Mailbox/actor model: `inbox/` + `outbox/` per agent, atomic temp-file+rename,
    append-only `log.jsonl` (each consumer tracks its own cursor).
  - Native HITL: only critical (destructive / spend / scope change / unresolvable
    conflict) escalates to human; everything else the god resolves itself.
  - Git as coordination layer with SINGLE committer (main process) to avoid
    `index.lock` corruption — agents only write files, never git themselves.
  - Scheduled "missions" = cron that posts a request into an agent's queue (Hands
    off, cadence-based) — distinct from an always-on autonomous loop.
- **Local-first = no cloud server** — matches user's "server light / on-demand"
  hard requirement. The "server" is just local processes reading/writing local files.
- Important: Munder Difflin is a *generic* harness (code clones). Our Agency OS is
  the *domain product* (SEO/AEO for TAGS agency) built on top of the same pattern.
  Borrow architecture, not its code.

## VERIFIED: our CEO is a REAL LLM (not a dumb router) + orchestrator exists
- `admin/agency/ceo.py` (2059 lines): `class AgencyCEO` -> `__init__` sets
  `self.graph = build_ceo_graph()`. `build_ceo_graph()` builds a langgraph
  `StateGraph(CEOGraphState)` and `.compile()`s it => a genuine reasoning LLM agent.
- `CEO_SYSTEM_PROMPT` (L37): "You are the Agency CEO of TAGS Agency — the
  co-founder and strategic brain." So it has its own persona/prompt (behaves like a
  real CEO, reasons, not a bot).
- CEO tools (delegate work / report / answer): `_tool_delegate` (L1037),
  `_tool_run_sales` (L957), `_tool_email_client` (L1003),
  `_tool_generate_report` (L1596), `_tool_parallel_blast` (L1167),
  `_tool_run_multiagent` (L1339), `_tool_answer`-style reasoning.
- Multi-agent handler/orchestrator EXISTS (user calls it "multi orch"):
  `admin/agency/orchestrator.py` has `register_agent` (L97),
  `run_seo_agent_for_workspace` (L310), `sba_pipeline_scan` (L584).
- Agent-to-agent comms: `admin/agency/agent_bus.py` (SQLite inbox/outbox queue,
  15 SQL hits). Route `/api/ceo/run` runs multi-agent.
- So: CEO = brain (LLM, reasons + system prompt); Orchestrator = plumbing that
  actually runs agents + registry; agent_bus = message layer. Together they give
  the multi-agent network work, manage it, answer, and report — exactly the
  user's mental model. This is the "intelligence vs mechanism" split from Munder
  Difflin's god-orchestrator.

## CRITICAL CORE requirement (user, 2026-08-25) — CEO must think like a REAL CEO
- User's words: "ceo ko hamko aise banana hai ke wo real ceo ke jaise soch skill
  ho... yehi agency ka main core hai." He knows it already uses an LLM — the gap
  is that the CEO is NOT yet given a *CEO's skill/judgment* layer.
- VERIFIED GAP: CEO has **NO skill registry** (`ceo_skills.py` does not exist).
  Other agents DO have per-agent skill registries (`sba_skills.py`, `seo_skills.py`,
  `social_skills.py`, `website_skills.py`) that auto-detect Jcode skills from the
  message. CEO only has 12 raw tool functions — no "senior-leader reasoning" skill.
- Current report is a HARD-CODED template (`=== CLIENT REPORT ===`,
  `=== TAGS AGENCY WEEKLY REPORT ===` in `_tool_generate_report`) — mechanical data
  dump, not "CEO-style thinking" + actionable next steps + boss-language (Hinglish).
- What to BUILD (the core):
  1. **CEO Skill layer** — business brain: strategy, prioritization, decision-
     making, delegation judgment (which agent, when, how). Like other agents'
     `*_skills.py` registry, but for CEO-level reasoning.
  2. **Report skill** — define HOW the CEO reports: boss-language (Hindi/English
     mix), digest vs detailed, actionable next-steps, not a raw data dump.
  3. Plumbing: CEO gets its own `ceo_skills.py` registry so it auto-reacts like
     the other agents.
- This is the agency's MAIN CORE per the user — prioritize it. Build TOGETHER.

## DONE: CEO's OWN skills wired in (2026-08-25)
- User clarified: do NOT copy from ~/.jcode/skills (external catalog). CEO needs its
  OWN brain. And `find-skills` is a DISCOVERY tool — used it to FIND relevant skills
  for the CEO, not to give find-skills itself to the CEO.
- Found via find-skills (web search of skills.sh ecosystem):
  - `ceo-skill` (AIPMAndy/CEOskill) — world-class Chief-of-Staff decision advisor:
    decision framing, risk, bias-check, war-gaming, stakeholder mapping, crisis mode.
    Cloned from https://github.com/AIPMAndy/CEOskill into
    `admin/agency/ceo_skills_repo/ceo-skill/` (SKILL.md + references + scripts + evals).
  - `status-report` — anthropic skill for leadership status updates (KPIs, risks,
    action items, green/yellow/red). Not in the cloned anthropics/skills v0.0.1, so
    wrote a CEO-specific version at `admin/agency/ceo_skills_repo/status-report/SKILL.md`
    (Hinglish digest + detailed, 🟢🟡🔴 health, actionable next-steps).
- Built `admin/agency/ceo_skills.py` — mirrors the other agents' `*_skills.py`
  mechanism (detect by keyword, build context block) BUT sources from the local
  `ceo_skills_repo/` folder (CEO's own role skills, not the Jcode domain catalog).
- Wired into `ceo.py::call_llm` — CEO skill context injected into the system prompt
  alongside tools/functions. Boss message triggers the right skill (decision vs
  report); neutral message falls back to a default so CEO stays skill-aware.
- Verified (no model call): ceo-skill detects on "strategic decision/risk",
  status-report on "status/update", context block builds correctly (6321 chars).
- NOT gitignored — these are our files (not a reference clone), should be committed.

## Working agreement (user, 2026-08-25)
- Keep Munder Difflin clone saved + this understanding saved (MEMORY.md = truth).
- Next build = Section 2 (CEO-gated on-demand / LifecycleState) — to be done
  TOGETHER (user + agent), not solo. Spec: docs/specs/2026-08-25-ceo-gated-
  on-demand-design.md.
- ALSO build the CEO-as-real-CEO skill core (above) — this is the bigger priority.

## CEO SELF-HEALING (built 2026 session, §2.5)

- **User requirement (verbatim intent):** "CEO khud heal karega — agent ka tool nahi
  chala ya agent fail ho gaya toh CEO usko sahi karega. CEO agent backend mai khud
  jayega, error + tool sahi karega, kaam rukna nahi chahiye, user ke wait mein nahi
  baithna." Agents sleep by default; CEO is the 24/7 supervisor that also HEALS.
- **Implemented:** `admin/agency/self_heal.py` — `heal_agent()` + `heal_and_report()`.
  Flow: failure detected (custom agent `ok=False` / delegation exception / multi-agent
  FAIL) → CEO classifies error (transient / config / tool) → re-dispatches the
  ORIGINAL task (not just "analyze") → retries with backoff (transient) → escalates to
  boss ONLY after 3 failed attempts (config/credential + tool-exhausted).
- Wired into `ceo.py`:
  - New tool `heal_agent` registered in `CEO_TOOLS` + `_tool_heal_agent` + dispatch case.
  - `_tool_delegate`: custom-agent `ok=False` → heal; any delegation exception → heal
    (covers built-in agents like ads/seo that raise).
  - `_tool_run_multiagent`: each FAILED result → CEO heal (status shows HEALED/FAIL).
- Extends the earlier `route_error_fix` concept (ceo.py `_tool_route_error`) but adds
  automatic detection + re-dispatch of the original brief + retry/escalate. The old
  `_tool_route_error` only routed an error to an agent for "analysis", it did not
  re-run the work or retry.
- **Known limitation (v1):** built-in agents (route_to_agent) return a plain string,
  not an `ok` flag, so non-exception failures (agent returns an error string without
  raising) are NOT auto-healed yet — only exception-level failures trigger heal for
  built-ins. Custom agents (run_worker) DO report `ok`, so they are fully covered.
  Future: make route_to_agent return structured {ok, error} for full coverage.
- Design note: CEO is the ONLY thing that triggers agent wake/sleep (Lifecycle), and
  now the ONLY thing that heals them — consistent with the "CEO = 24/7 supervisor"
  model. No 24/7 polling loop added; healing happens inline within the CEO's own
  delegation context (CEO is already 24/7 on as the FastAPI server).

## DUAL PERSISTENCE: PocketBase + JSON FILES (2026 session)

Boss rule: "memory aur FILE dono jagah sab save ho."
- **PocketBase** = networked source of truth. **Files** (`data/store/<collection>/<id>.json`,
  `admin/file_store.py`) = always-written, boss-readable backup - works even with
  `POCKETBASE_URL` unset. Lifecycle already had its own `lifecycle_state.json`.
- Boot restore order: local SQLite -> PB pull -> file-store gap fill
  (`manager.seed_from_pocketbase`, `agent_registry.sync_from_pocketbase`).
- Custom agents create/delete sync to BOTH; workspaces + agent_outputs mirror to
  BOTH via `_mirror_to_pb` (keyed upserts, never fatal).
- PB server: EC2-local `pocketbase.service` @ `127.0.0.1:8090` (v0.39.10). Auth is
  the NEW `_superusers` endpoint (old `/api/admins` 404s); creds wired in EC2
  `/opt/tags-agency-os/.env`. Client self-heals missing key fields on legacy shared
  collections (`ensure_key_field`) - e.g. `workspaces` is SHARED with sba-gateway,
  never drop it.
- E2E proven live: API create -> row in PB + JSON file; API delete -> gone from both.
