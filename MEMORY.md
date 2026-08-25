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
