# Agency OS — Project Memory

> Persistent knowledge for the Agency OS (TAGS Agency) build. The in-tool
> `memory` backend was non-persistent in this environment, so this file is the
> source of truth. Update it as work progresses.

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

## Working agreement (user, 2026-08-25)
- Keep Munder Difflin clone saved + this understanding saved (MEMORY.md = truth).
- Next build = Section 2 (CEO-gated on-demand / LifecycleState) — to be done
  TOGETHER (user + agent), not solo. Spec: docs/specs/2026-08-25-ceo-gated-
  on-demand-design.md.
