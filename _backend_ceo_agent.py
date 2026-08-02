"""
CEO Agent - Fully conversational AI agent that understands natural language.
No rigid commands, no regex patterns. Just talk to it like a person.

Uses Groq function calling to execute actions (create clients, run workflows, etc.)
while responding in natural Hinglish/English.

Supports conversation history for contextual multi-turn dialogue.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from groq import Groq
from agent_engine import engine

logger = logging.getLogger("CEOAgent")

SYSTEM_PROMPT = """You are the CEO Agent of a Marketing Agency Platform. You're friendly, smart, and direct.
You can speak in Hinglish (Hindi+English mix), English, or whatever the user prefers.

YOUR PERSONALITY:
- You're like a startup CEO who knows everything going on
- You talk casually but professionally
- You can switch between English and Hinglish naturally
- You're proactive - suggest things before user asks
- You keep answers concise but helpful
- You remember what was discussed earlier in the conversation

WHAT YOU CAN DO (use these tools when needed):
1. Create/manage clients
2. Run marketing workflows (social-growth, email-marketing, full-package, paid-ads, seo-content, lead-generation, gym-membership, agency-flow)
3. Chat with or execute any agent
4. Check system status, agent stats, Groq usage
5. List agents, workflows, clients
6. Generate reports
7. Handle lead queue, inactive clients, workload alerts
8. Hermes lifecycle: onboard, requirements, delivery, checkin
9. OpenClaw: search leads, research companies
10. OpenCode: build and deliver client packages
11. Video/photo shoot planning (Mumbai=production, foreign=AI)
12. Full pipeline automation
13. Team delegation (openclaw:, hermes:, opencode:)

CONVERSATION RULES:
- If the user refers to something from earlier ("that client", "the workflow we ran"), use context
- If they ask follow-up questions, answer based on what you just did
- If they say "do it" or "go ahead" after you suggested something, execute the action
- If they ask "what can you do?", give a brief overview, not a list of tools
- Keep responses conversational — like chatting with a colleague, not reading a manual
- If the user says something unclear, ask clarifying questions instead of guessing

IMPORTANT: Always use the appropriate tool when the user's request matches a tool's purpose.
If no tool matches, just respond conversationally with helpful advice.
When you call a tool, explain what you're doing in natural language before showing results.
"""


class CEOAgent:
    def __init__(self):
        self.engine = engine
        self._client = None
        self._conversations: Dict[str, List[Dict]] = {}
        self._max_history = 20
        self._init_groq_client()

    def _init_groq_client(self):
        try:
            if hasattr(self.engine, 'router') and hasattr(self.engine.router, 'keys'):
                keys = self.engine.router.keys
                if keys and len(keys) > 0:
                    api_key = keys[0].api_key
                    if api_key:
                        self._client = Groq(api_key=api_key)
                        return
            logger.warning("No Groq keys available, CEO agent will use fallback mode")
        except Exception as e:
            logger.error(f"Failed to init Groq client: {e}")

    def _get_conversation(self, session_id: str) -> List[Dict]:
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        return self._conversations[session_id]

    def _add_to_history(self, session_id: str, role: str, content: str):
        history = self._get_conversation(session_id)
        history.append({"role": role, "content": content})
        if len(history) > self._max_history:
            self._conversations[session_id] = history[-self._max_history:]

    def clear_conversation(self, session_id: str):
        if session_id in self._conversations:
            del self._conversations[session_id]

    def process(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        if not message or not message.strip():
            return {"status": "ok", "response": "Bolo bhai, kya chahiye?", "agent": "CEO Agent"}

        if self._client is None:
            return self._fallback_respond(message, session_id)

        try:
            return self._call_with_tools(message, session_id)
        except Exception as e:
            logger.error(f"CEO tool call error: {e}")
            return self._fallback_respond(message, session_id)

    def _call_with_tools(self, message: str, session_id: str = "default") -> Dict:
        self._add_to_history(session_id, "user", message)
        history = self._get_conversation(session_id)
        tools = self._build_tools()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        response = self._client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=2000,
        )

        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls:
            tool_results = []
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                handler = self._get_tool_handler(fn_name)
                if handler:
                    try:
                        result = handler(fn_args)
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        error_result = {"status": "error", "message": str(e)}
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(error_result)
                        })

            followup = self._client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages + [{"role": "assistant", "tool_calls": msg.tool_calls}] + tool_results,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000,
            )

            final_msg = followup.choices[0].message
            content = final_msg.content or "Ho gaya. Kuch aur chahiye?"
            self._add_to_history(session_id, "assistant", content)
            return {"status": "ok", "response": content, "agent": "CEO Agent"}

        content = msg.content or "Ho gaya. Kuch aur chahiye?"
        self._add_to_history(session_id, "assistant", content)
        return {"status": "ok", "response": content, "agent": "CEO Agent"}

    def _build_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_client",
                    "description": "Create a new client. Name and optional brief.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Client name (e.g. GymPro)"},
                            "brief": {"type": "string", "description": "Optional client brief"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_workflow",
                    "description": "Run a marketing workflow for a client. Workflows: social-growth, email-marketing, full-package, paid-ads, seo-content, lead-generation, gym-membership, agency-flow.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workflow": {"type": "string", "description": "Workflow slug (e.g. social-growth, full-package)"},
                            "client": {"type": "string", "description": "Client name"}
                        },
                        "required": ["workflow", "client"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_agents",
                    "description": "List all available AI agents in the system.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_workflows",
                    "description": "List all available workflows.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_clients",
                    "description": "List all clients in the system.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_status",
                    "description": "Get full system status: agents count, workflows, Groq API keys status.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_today_stats",
                    "description": "Get today's stats: leads, conversions, cold emails sent.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "chat_with_agent",
                    "description": "Chat with a specific agent. Use this when user wants to talk to a specific agent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name (e.g. content-writer, social-commander)"},
                            "message": {"type": "string", "description": "What to say to the agent"}
                        },
                        "required": ["agent", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_agent",
                    "description": "Execute a specific agent with a task. Use this to run a single agent for a job.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent": {"type": "string", "description": "Agent name (e.g. content-writer, brand-strategist)"},
                            "task": {"type": "string", "description": "Task description"}
                        },
                        "required": ["agent", "task"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_leads",
                    "description": "Search for leads using OpenClaw. Specify industry and location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "industry": {"type": "string", "description": "Industry (e.g. fitness, tech, real estate)"},
                            "location": {"type": "string", "description": "Location (default: global)"}
                        },
                        "required": ["industry"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "hermes_onboard",
                    "description": "Start Hermes onboarding for a lead. Use email and client type (A=self-service, B=managed).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "description": "Lead's email"},
                            "client_type": {"type": "string", "description": "A for self-service, B for managed"}
                        },
                        "required": ["email", "client_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "opencode_build",
                    "description": "Tell OpenCode to build a full package for a client in an industry.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client": {"type": "string", "description": "Client name"},
                            "industry": {"type": "string", "description": "Industry"}
                        },
                        "required": ["client", "industry"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_lead_queue",
                    "description": "Check the lead queue status and agent workload.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_inactive_clients",
                    "description": "Find clients who haven't had activity recently and may need followup.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_workload",
                    "description": "Check if any agents are overloaded and need attention.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": "Generate a performance report for a client.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client": {"type": "string", "description": "Client name"}
                        },
                        "required": ["client"]
                    }
                }
            },
        ]

    def _get_tool_handler(self, name: str):
        handlers = {
            "create_client": self._handle_create_client,
            "run_workflow": self._handle_run_workflow,
            "list_agents": self._handle_list_agents,
            "list_workflows": self._handle_list_workflows,
            "list_clients": self._handle_list_clients,
            "get_status": self._handle_status,
            "get_today_stats": self._handle_today_stats,
            "chat_with_agent": self._handle_chat_agent,
            "execute_agent": self._handle_execute_agent,
            "search_leads": self._handle_search_leads,
            "hermes_onboard": self._handle_hermes_onboard,
            "opencode_build": self._handle_opencode_build,
            "get_lead_queue": self._handle_lead_queue,
            "check_inactive_clients": self._handle_inactive_clients,
            "check_workload": self._handle_workload,
            "generate_report": self._handle_generate_report,
        }
        return handlers.get(name)

    def _format_tool_result(self, fn_name: str, result: Dict, original_message: str) -> Dict:
        response = result.get("response") or result.get("message") or json.dumps(result.get("data", {}))
        return {
            "status": result.get("status", "ok"),
            "response": response,
            "agent": "CEO Agent",
            "action": fn_name,
            "data": result.get("data")
        }

    def _handle_create_client(self, args: Dict) -> Dict:
        name = args.get("name", "").lower().replace(" ", "-")
        brief = args.get("brief", "")
        result = self.engine.create_client(name, brief)
        return {
            "status": "success",
            "message": f"Client '{name}' created successfully.{' Brief saved too.' if brief else ' You can now run workflows for this client.'}",
            "data": result
        }

    def _handle_run_workflow(self, args: Dict) -> Dict:
        wf = args.get("workflow", "").lower().replace(" ", "-")
        client = args.get("client", "").lower().replace(" ", "-")
        result = self.engine.run_workflow(wf, client)
        wf_name = result.get("workflow", wf)
        token_count = result.get("total_tokens", 0)
        time_taken = result.get("total_time", 0)
        return {
            "status": "success",
            "message": f"Workflow '{wf_name}' completed for '{client}'! Status: {result.get('status', 'done')}. Used {token_count} tokens in {time_taken:.1f}s.",
            "data": result
        }

    def _handle_list_agents(self, args: Dict) -> Dict:
        agents = self.engine.list_agents()
        names = "\n".join([f"  - {a['name']} ({a['slug']}) — {a.get('description', '')[:60]}" for a in agents])
        return {
            "status": "success",
            "message": f"We have {len(agents)} agents:\n{names}",
            "data": agents
        }

    def _handle_list_workflows(self, args: Dict) -> Dict:
        wfs = self.engine.list_workflows()
        names = "\n".join([f"  - {w['name']} ({w['slug']}) — {w.get('description', '')[:60]}" for w in wfs])
        return {
            "status": "success",
            "message": f"We have {len(wfs)} workflows:\n{names}",
            "data": wfs
        }

    def _handle_list_clients(self, args: Dict) -> Dict:
        clients = self.engine.list_clients()
        c_str = "\n".join([f"  - {c}" for c in clients]) if clients else "  No clients yet."
        return {
            "status": "success",
            "message": f"{len(clients)} client(s):\n{c_str}",
            "data": clients
        }

    def _handle_status(self, args: Dict) -> Dict:
        status = self.engine.get_agent_status()
        workflows = self.engine.list_workflows()
        groq = status.get("groq", {})
        return {
            "status": "success",
            "message": f"""System is running smooth:
- Agents: {status.get('total_agents', 0)} loaded
- Workflows: {len(workflows)} available
- Groq: {groq.get('active_keys', 0)}/{groq.get('total_keys', 0)} keys active
- Tokens used: {groq.get('total_tokens_used', 0)}
- Cache: {groq.get('cache_size', 0)} entries, {groq.get('cache_hits', 0)} hits
- Total requests: {groq.get('total_requests', 0)}""",
            "data": status
        }

    def _handle_today_stats(self, args: Dict) -> Dict:
        stats = self.engine.get_today_stats()
        return {
            "status": "success",
            "message": f"""Today's numbers ({stats['date']}):
- New leads: {stats['leads_today']}
- Converted: {stats['converted_today']}
- Replies: {stats['replies_today']}
- Cold emails: {stats['cold_emails_today']}
- Queue: {stats['total_leads_in_queue']} leads waiting
- Hermes load: {stats['hermes_load']}
- OpenCode load: {stats['opencode_load']}""",
            "data": stats
        }

    def _handle_chat_agent(self, args: Dict) -> Dict:
        agent = args.get("agent", "")
        message = args.get("message", "")
        result = self.engine.chat_with_agent(agent, message)
        return {
            "status": "success",
            "response": result.get("response", "Agent responded."),
            "data": result
        }

    def _handle_execute_agent(self, args: Dict) -> Dict:
        agent = args.get("agent", "")
        task = args.get("task", "Execute default task")
        result = self.engine.execute_agent(agent, task)
        return {
            "status": "success",
            "message": f"{agent} completed the task.",
            "response": result.get("response", "")[:500],
            "data": result
        }

    def _handle_search_leads(self, args: Dict) -> Dict:
        industry = args.get("industry", "all")
        location = args.get("location", "global")
        result = self.engine.openclaw_search(industry, location)
        leads = result.get("leads_found", [])
        leaders = "\n".join([f"  {i+1}. {l.get('business_name', l.get('name', 'Lead'))} ({l.get('industry', '?')}) — Score: {l.get('score', 0)}" for i, l in enumerate(leads[:5])]) if leads else "  No leads found."
        return {
            "status": "success",
            "message": f"Found {len(leads)} leads in {industry}/{location}:\n{leaders}",
            "data": result
        }

    def _handle_hermes_onboard(self, args: Dict) -> Dict:
        email = args.get("email", "")
        ctype = args.get("client_type", "B")
        result = self.engine.hermes_onboard(email, ctype)
        return {
            "status": "success",
            "message": f"Hermes onboarding started for {email} (type: {ctype}). Welcome email sent.",
            "data": result
        }

    def _handle_opencode_build(self, args: Dict) -> Dict:
        client = args.get("client", "")
        industry = args.get("industry", "")
        result = self.engine.opencode_build(client, industry)
        return {
            "status": "success",
            "message": f"OpenCode built the full package for {client} in {industry}! Social, blog, email, ads — all ready.",
            "data": result
        }

    def _handle_lead_queue(self, args: Dict) -> Dict:
        stats = self.engine.get_queue_stats()
        return {
            "status": "success",
            "message": f"Lead queue: {stats['new']} new, {stats['processing']} processing, {stats['converted']} converted. Hermes load: {stats['hermes_load']}",
            "data": stats
        }

    def _handle_inactive_clients(self, args: Dict) -> Dict:
        inactive = self.engine.check_inactive_clients()
        if not inactive:
            return {"status": "success", "message": "All clients are active, no one needs followup.", "data": []}
        c_list = "\n".join([f"  - {c.get('name', c.get('email', '?'))}" for c in inactive])
        return {
            "status": "success",
            "message": f"{len(inactive)} inactive client(s):\n{c_list}",
            "data": inactive
        }

    def _handle_workload(self, args: Dict) -> Dict:
        alerts = self.engine.get_workload_alerts()
        if not alerts:
            return {"status": "success", "message": "All agents running smooth ✅"}
        return {
            "status": "success",
            "message": f"{len(alerts)} alert(s): {', '.join(alerts)}",
            "data": alerts
        }

    def _handle_generate_report(self, args: Dict) -> Dict:
        client = args.get("client", "").lower().replace(" ", "-")
        result = self.engine.generate_report(client)
        return {
            "status": "success",
            "message": f"Report generated for {client}.",
            "data": result
        }

    def _fallback_respond(self, message: str, session_id: str = "default") -> Dict:
        history = self._get_conversation(session_id)
        context = "Earlier in this conversation: " + " | ".join([m["content"][:100] for m in history[-4:]]) if history else ""
        full_message = f"{context}\n\nUser says: {message}" if context else message
        result = self.engine.chat_with_agent("agency-manager", full_message)
        response = result.get("response", "Samajh gaya. Kya karna chahte ho?")
        self._add_to_history(session_id, "assistant", response)
        return {
            "status": "ok",
            "response": response,
            "agent": "CEO Agent"
        }


ceo = CEOAgent()
