# Content Agent Remaining Work — Design Spec

Date: 2026-07-26
Author: Jcode + User
Status: Approved

## Goal

Close 3 remaining gaps in the Content Agent system simultaneously:
1. Unified tool registry (21 tools in one place)
2. Missing API routes (11 endpoints)
3. Test file rewrite (match current 6-node pipeline code)

## Current State

- 6-node LangGraph pipeline: DONE (parse_brief -> analyze_brand -> plan_visual -> engineer_prompt -> generate -> validate)
- Visual tools (10): exist in `admin/tools/visual_tools.py`
- Content tools (11): exist in `admin/tools/content_tools.py`
- API routes (16): exist in `admin/api/routes/content.py`
- Agency Content Agent: DONE (`admin/agency/content_agent.py`)
- Workspace Content Store: DONE (`admin/workspace/content_store.py`)
- Content Job Queue: DONE (`admin/tools/content_queue.py`)
- Test file: OUTDATED — references old imports that no longer exist

## Design

### 1. Unified Tool Registry

**File:** `admin/tools/registry.py`

Create a single entry point that combines all 21 tools from visual_tools and content_tools:

- `CONTENT_AGENT_TOOLS`: Combined list of all 21 tool schemas
- `execute_agent_tool(tool_name, params)`: Single dispatcher that routes to the correct tool function
- `get_tool_by_name(name)`: Lookup a tool schema by name
- `list_tools_by_category(category)`: Filter tools by category (visual/content/kaggle)

The registry imports from existing files — no duplication. Just aggregation and dispatch.

### 2. Missing API Routes (11 endpoints)

Add to existing `admin/api/routes/content.py`:

| Endpoint | Method | Description | Calls |
|---|---|---|---|
| `/api/content/tools/all` | GET | Full tool list (21 tools) | `registry.list_all_tools()` |
| `/api/content/analyze-readability` | POST | URL readability analysis | `execute_content_tool("analyze_readability", ...)` |
| `/api/content/blog-post` | POST | Blog post generation | `execute_content_tool("generate_blog_post", ...)` |
| `/api/content/calendar` | POST | Content calendar | `execute_content_tool("generate_content_calendar", ...)` |
| `/api/content/rewrite` | POST | Content rewriting | `execute_content_tool("rewrite_content", ...)` |
| `/api/content/meta-optimize` | POST | Meta description optimization | `execute_content_tool("optimize_meta_descriptions", ...)` |
| `/api/content/content-gaps` | POST | Content gap analysis | `execute_content_tool("analyze_content_gaps", ...)` |
| `/api/content/agency/stats` | GET | Agency-level stats | `get_agency_content_agent().get_stats()` |
| `/api/content/agency/knowledge` | POST | Cross-project knowledge | `get_agency_content_agent().get_knowledge_for_workspace()` |
| `/api/content/agency/best-prompts` | GET | Best prompts | `get_agency_content_agent().get_best_prompts()` |
| `/api/content/queue/status` | GET | Queue overview | `get_queue(ws_id).get_queue_status()` |

All routes call existing functions — no new business logic, just wiring.

### 3. Test File Rewrite

**File:** `admin/tests/test_content_agent.py`

Complete rewrite matching current code. Test sections:

1. **Imports** (7 modules): visual_tools, content_tools, registry, content agent, content_queue, content_store, agency content agent
2. **Unified Tool Registry** (21 tools): verify count, execute dispatch, category filtering
3. **Visual Tools** (10 tools): direct import and count
4. **Content Tools** (11 tools): direct import and count
5. **Brand Discovery**: live test with example.com
6. **Brief Parser**: structured parsing for social/ad briefs
7. **6-Node LangGraph Pipeline**: graph compile, state shape, routing
8. **Agency Content Agent**: singleton, receive_report, get_knowledge, get_stats, persistence
9. **Workspace Content Store**: memory create, record_success, record_failure, agency reporting
10. **Content Job Queue**: submit, priority ordering, retry, status
11. **Brief Enhancement**: dimensions, prompt engineering, brand colors
12. **API Routes**: all 27+ endpoints registered in router
13. **Interview Compliance**: FULL-SPECTRUM, visual-only, kaggle, brand discovery

No old imports. No phantom functions. All assertions match actual current code.

## Files Modified

1. NEW: `admin/tools/registry.py` — unified tool registry
2. MODIFIED: `admin/api/routes/content.py` — add 11 endpoints
3. REWRITTEN: `admin/tests/test_content_agent.py` — complete rewrite

## Files NOT Modified

- `admin/tools/visual_tools.py` — untouched
- `admin/tools/content_tools.py` — untouched
- `admin/workspace/agents/content.py` — untouched
- `admin/agency/content_agent.py` — untouched
- `admin/workspace/content_store.py` — untouched
- `admin/tools/content_queue.py` — untouched

## Risks

- Registry wraps existing functions — if those functions have bugs, registry passes them through
- New API routes need Pydantic request models for POST endpoints
- Test file must be runnable with `python admin/tests/test_content_agent.py`
