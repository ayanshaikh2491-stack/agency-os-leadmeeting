---
description: Deep interview questions for Ayan about TAGS Agency — operations, challenges, vision. NOT about SBA architecture (already documented in ARCHITECTURE.md).
---
# TAGS Agency — Deep Interview Q&A

## Q&A (answered so far)

### Q23 — Client Reporting & Deliverables (July 10, 2026)
- **C — Meeting/deck-based:** Client ko periodic review meetings (weekly/bi-weekly) with slide decks showing progress. CEO ya Ayan present karega. Visual, structured, conversation-driven reporting.
- **Rationale**: Simplest initial setup, highest client touch, CEO personality (co-founder/strategic partner) ke saath fits well. Automated reports can be added later.

### Q22 — Pricing & Billing Model (July 10, 2026)
- **D — Hybrid (Base package + performance add-ons):**
  - Base retainer/package for core services
  - Performance-based bonuses ya add-ons for extra results
  - Jo D option tha, wohi sahi lag raha hai
- **Deferred details:** Exact pricing tiers, base scope, bonus structure — TBD (to be defined during build phase)

### Q21 — Failure Recovery & Error Handling (July 10, 2026)
- **B + D hybrid (Ayan flag + multi-layer escalation):**
  - **B (primary):** Ayan flags → CEO routes fix — Ayan notices errors in final review, tells CEO, CEO assigns fix to right agent. Human-in-loop error detection.
  - **D (flavor):** Multi-layer escalation — error caught at any layer:
    1. Agent self-detects (internal QA catches it)
    2. CEO catches during review
    3. Ayan catches during final sign-off
    4. Client reports (worst case — defined escalation path)
  - **Key:** CEO is the routing hub for all error recovery. Fixes always go CEO → sub-agent, never direct.

### Q18 — CEO Autonomy & Decision Authority (July 10, 2026)
- **D — Hybrid with distributed autonomy ("har agent khud sochega"):**
  - **Agency CEO** — Poori agency sambhalega. Agency & business ke liye strategic thinking karega, overall direction set karega. Jo strategy sochta hai, SBA ke saath **share** karega.
  - **SBA agent** — Leads find karega, verify karega ke leads sahi hain ya nahi. SBA apni domain mein "khud sochega" — sales strategy, lead qualification, outreach approach.
  - **Workspace CEO** — Per-client orchestration and execution.
  - **Sub-agents (SEO, Website, Ads, Content, Social)** — "Apne hisaab se sochenge aur strategy banayenge." Each agent thinks independently within their domain.
- **Key insight:** CEO agency-level strategic thinking SBA ko guide karti hai, lekin SBA apni execution khud decide karta hai. Dono ka thinking connected hai but independent execution.
- **Full model:** Agency CEO → shares strategy with SBA. SBA khud sochega. Sub-agents apne domain mein fully autonomous thinking. Workspace CEO per-client orchestration.

### Q19 — CEO Persona & Communication Style (July 10, 2026)
- **B + C hybrid (strategic partner with execution flavor):**
  - **B (dominant):** Co-founder jaisa — khud sochta hai, disagree bhi karta hai respectfully. Candid, direct. "Boss yeh deal kharab hai". Strategic thinking, not just task-following.
  - **C (undertone):** Executor bhi hai — follow-through, delivery, task completion. Sirf baat nahi karta, kaam bhi karta hai.
  - **Bottom line:** Strategic partner jo execution bhi kare. Co-founder + doer.

### Q20 — Quality & Iteration Cycle (July 10, 2026)
- **B + D hybrid (multi-stage internal QA + Ayan check):**

### Q3 — SEO Agent Tooling & Platform Access
- **B + C + D (All three — multi-tool + platform-dependent + agent decides):**
  - **B — Full toolkit:** Google Search Console, Analytics, Pagespeed + premium keyword tools (Ahrefs/SEMrush), competitor analysis tools
  - **C — Platform-dependent:** Client ke platform ke hisaab se tools — Shopify SEO apps, WordPress SEO plugins (Yoast/RankMath), Webflow SEO settings, etc.
  - **D — Agent decides:** Agent khud decide karega per client kaunsa tool set chahiye — kuch clients free tools se kaam ho jayega, kuch ke liye premium tools lagenge

### Q4 — SEO Agent Approval & Reporting Flow
- **B + C hybrid (strategy approval + regular check-ins):**
  - SEO agent CEO ke brief ke hisaab se **strategy propose karega** → CEO approve karega → tab execute karega
### Q5 — SEO Agent Content Ownership
- **B + D hybrid (brief Content Agent + owns small content):**
  - **B (primary):** SEO agent content strategy, brief, aur plan banayega — execution Content Agent karega
  - **D (flavor):** Meta descriptions, title tags, schema markup, small on-page SEO tweaks — ye sab SEO agent khud karega
  - **Boundary:** Bada aur complex content (blog posts, guides, landing pages) → Content Agent ko brief. Small on-page content → SEO agent directly

### Q6 — SEO Agent Activation Trigger
- **B + C hybrid (always-on + workspace-based):**
  - **B (primary):** Har active client ke liye SEO agent continuously monitoring karta rehta hai — performance tracking, keyword position monitoring, competitor changes
  - **C (setup):** Nayi client workspace create hote hi SEO agent automatically activate ho jata hai. CEO brief ka wait nahi karta — basic monitoring/setup immediately start ho jata hai
  - **Flow:** Workspace create → SEO agent auto-activates (monitoring starts) → CEO brief deta hai → SEO agent active execution/optimization start karta hai


  - Agent regular progress reports dega (weekly/bi-weekly) to CEO
### Q7 — SEO ↔ Website Agent Dependency
- **B + D hybrid (SEO briefs + shared execution):**
  - **B (primary):** SEO agent identifies changes needed — Website Agent implements them
  - **D (flavor):** Hybrid execution — chhoti changes (meta tags, schema markup) SEO agent khud karega. Badi structural changes (page restructure, redirects, page speed fixes) → Website Agent ko brief for implementation
  - **Key:** SEO agent is the identifier/strategist for technical changes; Website Agent is the implementer for larger items

### Q8 — SEO Agent Error Handling & Recovery
- **C + D hybrid (agent auto-fix + critical auto-rollback):**
  - **C (primary):** Agent khud fix karega — rollback nahi karega, analysis karke naya fix apply karega. CEO ka wait nahi karega recovery ke liye.
  - **D (flavor):** Critical issues (404 spikes, broken pages, site down) → auto-rollback first. Non-critical (ranking dip, traffic fluctuation) → analyze + new fix apply.
  - **Flow:** Error detect → is it critical? Yes → rollback + analyze + new fix. No → analyze + new fix. CEO notified after fix.


### Q9 — SEO Agent Priority & Concurrency (July 10, 2026)
- **C — Parallel processing, per-workspace isolation:** Har workspace ka apna SEO agent hai. Wo sirf apne workspace ka kaam karega. Priority/concurrency ka cross-workspace issue nahi hai — sab independent hain.

### CRITICAL — Cross-Workspace Agent Knowledge Sharing (July 10, 2026)
**Ayan's correction/nouveau point:**
- **Dual reporting per agent:** Har workspace agent (SEO, Ads, Content, Social, etc.) apna SBA/context **donon** ko share karega:
  1. **Workspace CEO** — direct overseer (already established)
  2. **Agency-level corresponding agent** — e.g., Workspace SEO → Agency SEO, Workspace Ads → Agency Ads
- **Purpose:** Centralized role-based knowledge pool. Agency-level SEO ko pata hai sab workspace SEOs kya kar rahe hain. Har workspace SEO dekh sakta hai doosre workspace SEOs kya kar rahe hain. Successful strategies cross-pollinate.
- **Flow:** Workspace Agent → Workspace CEO + Agency-level Agent (same role). Sab ka history/learnings ek centralized jagah.



  - **CEO overall reporting:** CEO SBA, client, aur Ayan ko **weekly + monthly reports** provide karega


  - **Primary (B):** Agent self-QA loop — agent khud apna output check karega, internal improvements karega before sending to CEO
### Q10 — SEO Agent Learning & Improvement (July 10, 2026)
- **C + D hybrid (auto-learning + CEO override):**
  - **C (primary):** Auto-learning — SEO agent khud analyze karega past campaign performance (what worked, what didn't) and automatically adjust future strategies. Kisi specific strategy fail kare to agent adjust karega without manual intervention.
  - **D (flavor):** CEO can correct/override anytime — agent ko autonomy hai but CEO ka feedback/override higher priority.


  - **Internal multi-stage pipeline:** Agent self-QA → CEO review/validation
  - **Ayan final gate:** Ayan will personally check final output before client delivery ("mai bhi check kaorga")
  - **No client-facing iteration cycle** — internal QA/QC only, client sees final
- **Flow:** Agent self-QA → CEO review → Ayan sign-off → Client delivery

### Q17 — SBA → CEO Handoff Protocol (July 10, 2026)
- **A + B hybrid (structured brief + full dump):** Jab SBA lead convert kare to CEO ko dono milega:
  1. **Clean structured brief** — client info, needs, agreed scope, key signals, next steps
  2. **Full data dump** — all research, conversations, lead history, granular data
- CEO ke paas puri visibility hai — overview bhi, raw data bhi.

### Q16 — SBA First Target Platform (July 10, 2026)
- **E — Sab ek saath:** Multi-threaded approach. SBA sab platforms ek sath launch karega — LinkedIn, freelancer platforms (Upwork, Fiverr), cold email, Reddit & communities sab ek saath. Real browser handle kar lega parallel execution.
- SBA ek sath multiple channels run karega, ek ke baad ek nahi.

### Q15 — SBA Daily Operating Rhythm (July 10, 2026)
- **B + D hybrid (pipeline mode + always-on hunter):** SBA leads continuously find karega (24/7, always-on monitoring) aur saath hi pipeline mein multiple leads ko manage karega — kuch discovery stage mein, kuch outreach mein, kuch nurture mein, kuch handoff-ready.
- **Key:** SBA kabhi nahi rukega. "24/7 chalega yaar" — continuous operation, har stage ke leads ek sath manage ho rahe hain.
- **Full ownership:** Leads find bhi karega, SBA ka saara kaam bhi karega (qualification, nurture, handoff prep). Sab ek sath.

### Q14 — SBA Lead Source & Prospecting Strategy (July 10, 2026)
- **C + D hybrid (multi-channel hunter + platform-specific):** SBA sab channels use karega — cold outreach, inbound monitoring, freelancer platforms, social listening, etc. Lekin specific platform/source bhi decide karenge.
- **CRITICAL — SBA ko apna dedicated real browser milega:** Ayan jaise Chrome use karta hai, waise hi SBA apna browser use karega. Real browser agent — isse lead generation, LinkedIn, freelancer platforms, sab par koi problem nahi hoga (no CAPTCHA/blocking issues).
- **No issues with C + D approach** because SBA has a real browser environment.

### Q13 — SBA Agent Role & Scope (July 10, 2026)
- **Full SBA lifecycle: Lead → Client Handoff → Workspace**
  - SBA agent finds leads, qualifies them, nurtures them, then hands off to CEO when lead converts to client
  - **SBA "khud leads find karega"** — active lead prospecting, not passive processing
  - No agents beyond the SBA-to-CEO flow (no extra layers or intermediaries)
- **Model: B (full lifecycle)** — SBA handles lead generation through conversion, not just initial contact
- **Confirmed**: No CrewAI/LiteLLM. LangGraph only. Frontend/ARCHITECTURE.md deferred to post-build.

### Q12 — Agent Communication Protocol (July 10, 2026)
- **B + C + D (Sub-graph per workspace + Direct calls + Hybrid):**
  - **B (architecture):** Har workspace ka apna alag LangGraph sub-graph hai. Agency CEO ka graph workspace sub-graphs ko invoke karta hai. Workspace ke andar CEO node → sub-agent node communication shared state se hoti hai. Hierarchical.
  - **C (execution):** LangGraph NodeFunction pattern — ek agent seedha doosre agent ko invoke karta hai structured input/output ke saath. Jaise function call. CEO "brief_SBA(brief_data)" call karega, SBA process karega aur result return karega.
  - **D (flavor):** CEO ke liye shared state graph (brief + monitoring + review), lekin sub-agents aapas mein (SEO↔Website, Social↔Content Agent, SEO↔Content) direct focused sub-graphs ke through communicate karte hain. Dono patterns ek saath.
- **Key:** Hierarchical workspace sub-graphs + direct agent-to-agent function calls + shared CEO monitoring state. No external message queue.

### Q11 — Agent Build Priority (July 10, 2026)
- **SBA first (A):** SBA agent (lead/sales agent) pehle build karna hai. Baaki agents baad mein.
- **Rationale:** Leads/sales engine comes before service delivery — SBA handles incoming leads, then hands off to CEO → sub-agents
- **Order after SBA:** Not specified yet — remaining agents (SEO, Website, Ads, Content, Social) built after SBA

### Q10 — Client Onboarding & Lead-to-Client Flow (July 10, 2026)
- **B + C hybrid (auto-detect + Ayan-initiated):**
  - Jo leads ayenge wo agency hi le kar ayegi — leads come through agency channels
  - CEO aur SBA **email mein baat karege**
  - **Kuch client** Ayan ke paas directly aayenge — tab Ayan khud CEO ko batayega
- **CRITICAL — Lead-to-Client handoff:**
  - **SBA agent leads se baat karega** — handles all lead communication, qualification, information gathering
  - **CEO agent tab baat karega jab lead client mein transfer hoga** — CEO does NOT get involved during lead stage
  - SBA gives **all information** to CEO when lead converts to client
  - CEO then takes over — workspace creation, sub-agent briefing, execution
- **Key:** SBA owns the lead stage entirely. CEO only activates post-conversion.


## Sub-Agent Interviews

### Website Agent — Interview Q&A

### Q1 — Website Agent Scope (July 10, 2026)
- **A + C + D (full pipeline + maintenance + agent decides):**
  - **A (primary for new clients):** Full pipeline owner — Layout Design → Development (tech stack autonomously decides) → Domain + Hosting setup → Deploy
### Q2 — Website Agent Tech Stack (July 10, 2026)
- **A + D (agent decides + client preference):**
  - Agent khud decide karega tech stack per client (WordPress, Next.js, Webflow, etc.)
  - Client ki bhi preference consider karega
  - **Constraint:** Frontend hosting Vercel par by default (baaki details build phase mein refine)
- **Note:** Full autonomy abhi, baad mein build time par refine karenge
### Q3 — Website Agent Design Ownership (July 10, 2026)
- **A + C + D (agent designs + hybrid review + decides per client):**
  - **A:** Agent visual design/layout khud karega (client brief ke hisaab se)
  - **C:** Agent apna design propose karega → CEO approve karega → tab implement karega
  - **D:** Requirement ke hisaab se decide — kabhi design bhi karega, kabhi sirf implement
  - **Key:** CEO review/approval gate before implementation

### Per-Agent Skill Folders (July 10, 2026)
- **Ayan's requirement:** Har sub-agent (CEO, SBA, SEO, Website, Ads, Content, Social) ke liye **alag skill folder** create karna
  - E.g., Website Agent ke liye frontend skill, SEO agent ke liye SEO skill
  - Each agent ka apna domain-specific skill folder hoga
  - **Action:** Build time par create karna (interview phase ke baad)



### Q4 — Website Agent Domain & Hosting Setup (July 10, 2026)
- **A + D (plan-dependent + client decides):**
  - **A — Full setup:** Client ke plan mein hosting + domain included hai → agent domain register karega, hosting setup karega, deploy karega. Sab khud.
  - **D — Client provides:** Client khud apna domain aur hosting dega ("mai dunga") → agent uske environment ke hisaab se adapt karega
  - **Key:** Client ke plan aur preference decide karta hai kaunsa approach use hoga



  - **C (for existing clients):** Maintenance, updates, fixes for existing sites
  - **D (flavor):** Agent apne expertise aur client requirement ke hisaab se decide karega exactly kitna scope lega
### Q5 — Website Agent Maintenance & Monitoring (July 10, 2026)
- **C — AI self-monitoring, 24/7:**
  - Website Agent continuously monitors the site — broken links, performance, security updates, uptime — 24/7
  - Agent proactively detects and fixes issues without waiting for a ticket
  - "C aur wo 24/7 dekhta rahega sab cheezein" — fully autonomous maintenance loop
### Q6 — Website Agent ↔ Content Agent Integration (July 10, 2026)
- **Direct agent-to-agent communication:** Website Agent aur Content Agent direct communicate karenge. CEO ko intermediary nahi hona.
- "Direct communication karege content agent se and jo kaam karna hoga karege" — autonomous cross-agent coordination.
- Agents figure out and do the work together without CEO needing to mediate every interaction.





### Q9 — Agent Learning & Memory (July 10, 2026)
- **B (primary) — Cross-project learning:** Agents automatically learn from experience — successful strategies, patterns, client preferences sab yaad rakhein aur future projects mein apply karein
- **D (flavor, no manual):** Self-correcting approach — agents khud seekhein, adjust karein, improve karein. **Ayan manually kuch nahi karega**, na validate, na playbooks — full autonomy.
- **Key:** "Jaisa agent seekhta hai waisa" — natural learning, no manual intervention

### Q8 — Agent Tooling & Knowledge Access (July 10, 2026)
- **B + C hybrid:** Per-domain toolkits + Tiered access
- **Per-domain toolkits:** Har agent ke paas sirf apne domain ke specific tools hain (SEO agent ko keyword tools, Website agent ko hosting/dev tools, etc.)
- **Tiered access:** CEO ke paas sab tools ka access. Sub-agents ke paas limited domain-specific tools. Kuch tools sirf CEO ke paas (client data, pricing, contracts)
- **Shared + specialized:** Common API/integrations shared hain, lekin har agent apne specialized environment mein kaam karta hai

### Q7 — Sub-Agent Service Menu / Scope (July 9, 2026)
- **Hierarchy: D (primary) → B (per-plan) → C (add-ons/offers)**
  1. **Agent decides (D):** CEO brief ke hisaab se agent khud decide karega exactly kya deliver karna hai — agent apni expertise se scope define karega. Ye primary mode hai.
  2. **Fixed package (B):** Client ke plan/package ke hisaab se predefined core services. Agent D-based approach use karta hai, lekin package boundaries ke andar.
  3. **Core + add-ons (C):** Jab koi special offer chal raha ho, ya client ne extra pay kiya ho premium features ke liye, ya lower-price plan ke liye.
- **Agent ka autonomy real hai** — agent decide karta hai kya deliver karna hai, sirf plan/budget constraints hain.

### Q6 — Client Information System (July 9, 2026)
- **Agent workspace (C):** Har client ka dedicated workspace hai jahan us client ka CEO hai. Client info, requirements, history — sab workspace ke andar hi rehta hai.
- **Flow confirmed:**
  1. Agency CEO workspace CEO ko brief/context provide karega
  2. Workspace CEO apne sub-agents ko task provide karega
  3. Sub-agents kaam karke output workspace CEO ko provide karenge
  4. Workspace CEO wo results Agency CEO ko provide karega
  5. Agency CEO Ayan (founder) aur client ke liye final output ready karega
- **Key hierarchy:** Agency CEO → Workspace CEO → Sub-agents → return flow up

### Q5 — Sub-Agent Autonomy Model (July 9, 2026)
- **Fully autonomous + CEO review (A + D):** Agents kaam karte hain fully independently — decisions khud lete hain (tech stack, design, copy, approach), CEO se har step nahi poochte. Lekin final output par **CEO review/QA stage** hota hai jahan CEO sab agents ka kaam ek saath review karta hai.
- **Flow:** CEO brief → Agents work autonomously → All agents submit output → CEO reviews everything together → CEO delivers/approves

### Q4 — CEO Execution Model (July 9, 2026)
- **Parallel blast (B):** CEO sab agents ko ek saath brief karega. Sab agents apna kaam parallel mein karenge.
- **CRITICAL: CEO hamesha sab brief karega, SBA agent nahi.** SBA agent sirf leads/sales handle karta hai. SBA se jo bhi information/client signal aata hai, wo **CEO ko jaata hai** — not to other sub-agents. CEO then briefs each sub-agent directly.
- **Flow confirmed:** SBA (leads/sales) → CEO → All sub-agents (Website, SEO, Ads, Content, Social). CEO is the single source of truth for all briefs.

### Q1 — Service Offerings (July 9, 2026)
- **TAGS Agency sells full-stack growth packages.** Client ko ek comprehensive package offer kiya jayega — website, SEO, ads, content, social media — sab kuch ek sath.
- **Clients NEVER talk to agents directly.** Only Ayan/CEO interacts with clients. All agents are internal.
- **Goal-based selling**: Client ke goal ke hisaab se service package design hoga, but overall approach is full-stack (not modular/ala-carte).
- **Pricing model**: TBD — still under discussion.
- **Retainer vs one-time**: Not yet decided.

### Q1b — Agency DNA / Positioning (July 9, 2026)
- **Hybrid model (C):** Standardized core packages + high-touch customization per client. Not pure "bespoke for every client" and not pure "cookie-cutter volume play." TAGS Agency will offer structured packages but with meaningful customization for each client's unique needs.

### Q1c — Agency Service Scope (July 9, 2026)
- **Full digital marketing stack (A):** Website + SEO + ads + content + social + email — sab kuch ek hi roof ke neeche. TAGS Agency will be a true full-service digital agency, not a niche/specialized shop.

### Q2 — Current State (July 9, 2026)
- **Ayan is fully solo** — "a mai hoa nd tu bas or koi nahi" (Ayan himself IS TAGS Agency; the agent is his only partner/team member).
- **Goal**: The AI agent system will be his "team" — agents will do the work that a full agency team would do. Ayan + agent = TAGS Agency.
- **Currently**: No active clients yet. Building the infrastructure first. Ayan confirmed he is building before selling.

### Q3 — Client Intake & Communication Channel (July 9, 2026)
- **No agency website for intake.** Clients don't come through a website. Instead, client communication happens via **email and WhatsApp**.
- **Only Ayan and CEO talk to clients.** Client ko sirf Ayan and CEO communicate karte hain. Sub-agents directly client se baat nahi karte.
- **Client sees only results and reports.** Client ko sirf deliverables, reports, aur results mile ga — agents ka internal work visible nahi hai. "Sirf result and report mile ga."
- **CEO is Ayan's interface** — Ayan talks to CEO, CEO orchestrates sub-agents internally.

## Questions deferred (post-build phase)

Ayan explicitly redirected: **"phele ham sab agents banayge and sab service yaar"** -- build agents and services FIRST, then think about clients. These questions are deferred until after core agents and services are built.

### 3. Pain Points (Deferred)
- Operations mein sabse bada friction kahan hai?
- Scale karne mein kya rok raha hai?
- Clients se kya common complaints/re-requests aati hain?

### 4. Client Details (Deferred)
- Typical client profile kya hai? (D2C, local, SaaS, etc.)
- Client budgets range?
- Client onboarding process kaise dikhta hai abhi?

### 5. Vision (Deferred)
- 1 year vision kya hai?
- Kitne clients par scale karna hai?
- Fully automated ya Ayan + agents hybrid?

## Sub-Agent Interviews

### Social Agent — Interview Q&A

### Q1 — Social Agent Scope & Platforms (July 10, 2026)
- **A + D (major platforms + strategy-only):**
  - **A (primary):** Instagram + LinkedIn + X — yehi teen primary platforms. Agent per client decide karega kaunsa activate karna hai based on client's industry/goals.
  - **D (critical distinction):** Social Agent is a **strategist, not an execution engine.** It creates the strategy — content calendar, posting schedule, engagement plan, content themes, growth tactics — but actual posting/engagement happens through external tools (later integrated).
  - **Key:** Social Agent = brains, not hands. Strategy deta hai, execution tools handle karte hain.

### Q2 — Social Agent Content Ownership (July 10, 2026)
- **A + D (brief Content Agent for visuals + hybrid execution):**
  - **A (primary):** Social Agent strategy + content calendar banayega. Visual posts (images, videos, reels, graphics) ke liye **Content Agent ko brief karega**. Captions, text content, hashtags — ye sab Social Agent khud handle karega.
  - **D (flavor):** Per campaign decide — chhoti updates, quick posts, text-only content Social Agent khud karega. Badi visual campaigns, reels, branded graphics → Content Agent ko brief.
  - **Key:** Text content ownership Social Agent ke paas. Visual execution Content Agent ke through.

### Q3 — Social Agent Growth & Engagement Strategy (July 10, 2026)
- **A + D (strategy-first, client-dependent):**
  - **A (primary foundation):** Organic-first — content strategy, hashtag research, posting cadence, community engagement. Sab organic growth tactics se start.
  - **D (flavor):** Client goal ke hisaab se decide karega — kabhi organic, kabhi paid (boosts/ads), kabhi influencer collab. Agent samjhega ke client ko social media chahiye ya ads/paid approach.
  - **Key abhi:** Pehle Social Agent ko solid strategy + execution foundation banana hai. Growth aur progress real mein dikhni chahiye. "Strategy aur sab chiz sahi se bana sake" — ye primary goal hai abhi. Execution tools/paid layers baad mein aayenge.

### Content Agent — Interview Q&A

### Q4 — Content Agent Workflow & Coordination (July 10, 2026)
- **C — Per-workspace isolation:** Har workspace ka apna Content Agent hai. Workspace ke andar domain agents (SEO, Ads, Social, Website) apne Content Agent ko requests bhejte hain. Cross-workspace conflict nahi hai — sab independent hain.
- **System constraint:** Multi-request handling needs concurrency-safe design. Har workspace ka Content Agent apne queue/execution loop mein chalta hai taake ek saath multiple workspaces mein problem na ho.
- **Flow confirmed:** CEO → Content Agent (within same workspace). Domain agents brief Content Agent for visual execution. Content Agent is pure visual execution engine (no strategy ownership).

### Q5 — Content Agent Brand Discovery (July 10, 2026)
- **A + D hybrid (CEO brief + agent self-discovery):**
  - CEO brief mein brand guidelines ka initial context dega
  - **Content Agent ko dimag do** — wo khud client ka social media, website, existing presence analyze karega. Logo, colors, style elements — sab khud discover karega ("uske social media account se pata chal jayega kya logo hai kya colour wo use kar raha hai")
  - Content Agent is not a dumb execution engine — it has its own intelligence to figure out brand identity autonomously
  - CEO provides starting context; Content Agent fills in the rest through self-discovery

### Q6 — Content Agent Revision & Approval Cycle (July 10, 2026)
- **C — Domain agent owns approval:** Jis domain agent ne brief kiya (Ads, Social, SEO, Website), wohi approve karega. Wohi feedback dega, wohi iteration gate hai.
- **CEO bypass:** CEO ko sirf last mein inform karega — "ye kaam ho gaya ads ke liye" / SBA ke liye. CEO visual approval cycle mein directly involved nahi.
- **Flow:** Domain agent brief → Content Agent creates → Domain agent reviews/approves → CEO notified of completion

### Q1 — Content Agent Scope (July 10, 2026)
- **Visual-only execution engine:** Content Agent ONLY creates visual content — images/photos and videos. NO strategy, NO text content ownership.
- **Strategy flow:** Har domain agent (SEO, Ads, Social, Website) apni content strategy khud sochega → Content Agent ko brief karega for visual creation. Content Agent khud strategy nahi banayega — sirf execute karega.
- **Text content ownership:** Har domain agent apna text content khud handle karega:
  - SEO Agent → blogs, articles, SEO copy
  - Ads Agent → ad copy, hooks
  - Social Agent → captions, social posts
  - Website Agent → landing page copy, website text
- **Key principle:** "Agar ads soche hai tho dono lad jayenge" — cross-domain conflict avoid karne ke liye content strategy ka ownership respective domain agents ke paas rahega. Content Agent pure visual execution hai.

### Q2 — Content Agent Visual Scope (July 10, 2026)
- **B + D (full visual spectrum + agent decides per brief):**
  - **B:** Sab kuch banayega — social graphics, ad creatives, website images, infographics, brand collateral, presentation visuals, videos, reels. Whatver visual is needed, Content Agent creates it.
  - **D:** Brief ke hisaab se decide karega — kabhi image-heavy campaign, kabhi video-heavy. Agent khud scope decide karega based on what's needed.

### Q7 — Content Agent Learning & Memory (July 10, 2026)
- **B — Cross-project learning (same pattern as all agents):**
  - Workspace Content Agent apna kaam/learnings **workspace CEO ko report karega** — primary reporting line
  - **Agency Content Agent** is integrated in the same loop — CEO ensures agency-level Content Agent gets the learnings
  - Flow: Workspace Content Agent → **Workspace CEO** (with Agency Content Agent involved in that flow)
  - **NOT** two independent reports — workspace sub-agent reports to workspace CEO, agency sub-agent is part of that loop
- **Purpose:** Agency Content Agent maintains centralized knowledge pool — sab workspace ke visual design patterns, brand preferences, successful strategies ek jagah
- **Cross-pollination:** Har workspace Content Agent dekh sakta hai doosre workspace Content Agents kya kar rahe hain via Agency Content Agent

### Q3 — Content Agent Tooling & Compute (July 10, 2026)
- **FINAL DECISION (July 10, 2026):** Content Agent image/video generation will use **Kaggle API (`kaggle kernels push`)** as the primary free GPU solution. Not browser-based — API-driven, session-free.
- **Architecture:** Content Agent → Kaggle API → notebook (GPU) → poll → download output. Two notebooks planned: `tags-image-gen` (FLUX.1-schnell) and `tags-video-gen` (CogVideo/ModelScope).
- **Ayan rejected:** Kaggle notebook UI, Google Colab, any browser-session approach. Only API-driven workflow accepted.
- **Status:** Saved to memory. Implementation deferred to agent build phase.
- **Future upgrade:** Replicate/fal.ai when GPU budget available.

## Sub-Agent Interviews

### Ads Agent — Interview Q&A

### Q1 — Ads Agent Scope & Platforms (July 10, 2026)
- **B (primary) + A + D (full scope):**
  - **B (primary focus):** Meta (Facebook + Instagram) aur Google Ads — yehi do platforms par main expertise abhi. Full ownership: strategy → campaign creation → optimization → reporting.
  - **A + D (full scope):** Agent per client decide karega. Kuch clients ke liye sirf Meta/Google. Kabhi LinkedIn, TikTok, X bhi add karega client goals/game plan ke hisaab se.
  - **Phased approach:** Pehle Meta + Google solid karo, phir baaki platforms expand honge.
- **Key:** Agent decides — "a and d ok main fouce tho b mai hoga"

### Q2 — Ads Agent Creative & Budget Ownership (July 10, 2026)
- **A + D (full ownership + agent decides):**
  - **A (full ownership):** Ads Agent owns everything — ad copy khud likhega, visuals ke liye Content Agent ko brief karega. Budget bhi khud manage karega (allocation across platforms, prospecting vs retargeting).
  - **D (flavor):** Agent decides per campaign — kabhi khud copy likhega, kabhi Content Agent ko brief. Campaign complexity, timeline, aur requirements ke hisaab se decide karega.
  - **Key:** 100% ownership of creative + budget. Content Agent is visual execution arm for ads.

### Q3 — Ads Agent Success Measurement (July 10, 2026)
- **A + B + D (comprehensive + autonomous):**
  - **A (ROAS/ROI driven):** Client goal ke hisaab se ROAS/ROI target set karega. Usi ke against measure karega.
  - **B (multi-metric dashboard):** CTR, CPC, CPA, ROAS, Impression Share, Frequency — sab kuch track karega. Comprehensive visibility.
  - **D (auto-optimization loop):** Metrics se trigger hoke agent khud optimize karega — budget shift underperforming se outperforming campaigns, pause failing creatives, adjust bids. No manual wait.
  - **Key:** ROAS target + full metric visibility + autonomous optimization loop. Sab ek sath.

### Q4 — Ads Agent Error Handling & Recovery (July 10, 2026)
- **B + D + C (multi-layer recovery pipeline):**
  - **Layer 1 — Auto-optimize (B):** Agent khud fixes try karega — budget reallocation underperforming se performing campaigns, creative rotation, bid adjustments. Pause hai but last resort.
  - **Layer 2 — Multi-layer recovery (D):** Step by step approach with thresholds — minor fixes first, aggressive optimization next, pause last.
  - **Layer 3 — CEO escalation (C):** Sustained failure ya major budget impact ho tab CEO ko report with recommendations. CEO decides final action.
  - **Flow:** Error detect → auto-optimize → still failing? → aggressive fix → still failing? → pause → report CEO

### Q5 — Ads Agent Audience Targeting (July 10, 2026)
- **A + C (automated discovery + prospecting/retargeting hybrid):**
  - **A (automated discovery):** Agent khud audiences build karega — lookalikes, interests, behaviors. Different segments test karega autonomously.
  - **C (hybrid approach):** Prospecting + retargeting dono ek sath chalega. Agent khud budget split manage karega between prospecting and retargeting campaigns.
  - **Skill boost:** Ads Agent ko dedicated skill milega — audience targeting aur bhi smarter ho jayega.

### SEO Agent — Interview Q&A

### Q1 — SEO Agent Scope
- **B + D hybrid (Full-stack + agent decides):**
  - Full-stack SEO: technical audits, keyword research, on-page, off-page/backlinks, content gap analysis, local SEO, reporting
  - Agent apne domain mein scope khud decide karega — kuch clients ko sirf technical chahiye, kuch ko full-stack
  - SBA agent ki tarah autonomous decision-making within domain

### Q2 — SEO Agent Success Measurement
- **D — Client-goal based hybrid (SBA pattern follow karega):**
  - Kuch clients ke liye organic traffic growth primary metric
  - Kuch ke liye keyword ranking improvements
  - Kuch ke liye leads/conversions from organic
  - Agent apne domain expertise se decide karega kaun sa KPI track karna hai per client

## Per-Agent Skill Folders (July 10, 2026)
- **Ayan's requirement:** Har sub-agent (CEO, SBA, SEO, Website, Ads, Content, Social) ke liye **alag skill folder** create karna
- **find-skills mechanism (July 10, 2026):** `npx skills add https://github.com/vercel-labs/skills --skill find-skills -y -g` installed globally. Now I can autonomously search and install skills per agent using `npx skills find <query>` and `npx skills add <package> -y -g`.
- **Workflow:** For each agent → run `npx skills find <relevant-keywords>` → discover relevant skills → `npx skills add` them per agent folder
- Installed at `~\.agents\skills\find-skills\SKILL.md`

## Notes
- SBA architecture ALREADY CAPTURED — do NOT re-ask
- CEOs call/invoke sub-agents (confirmed July 9)
- LangGraph/LangChain only (CrewAI/LiteLLM banned)
- Per-workspace mirrors agency structure

## SBA Dedicated Browser (chrome-agent) — Build Complete (July 10, 2026)
- **`chrome-agent` binary successfully built** at `C:\Users\TAUSHEF\Downloads\int\chrome-agent\target\release\chrome-agent.exe` (2,486,272 bytes)
- **Build fix**: LLVM's `dlltool.exe` was at `C:\tools\llvm-bin` but not in `PATH`. Appended to session PATH, `cargo build --release` passed clean.
- **Purpose**: This binary IS SBA's dedicated real Chrome browser instance (confirmed per Q14). SBA uses this for:
  - Lead generation — LinkedIn prospecting, freelancer platforms (Upwork, Fiverr)
  - Multi-threaded outreach — sab ek saath (per Q16)
  - No CAPTCHA/blocking issues — real browser, real user agent, real session
- **Deployed to**: `chrome-agent/` directory at project root

## Priority (Confirmed July 9)
- **Build first, sell later.** Priority order:
  1. First build SBA agent and ALL agents
  2. Build ALL services
  3. Then think about clients
- Interview about current operations/clients is premature — focus must be on building the agent system first.

## Interview Methodology
- **Grill-style questions**: Always use direct multiple-choice options (A/B/C/D) when asking questions. Ayan explicitly confirmed this pattern — "jaise pehel grill skill sue kareke option ke stah dirct wlala puchta tah." Do not ask open-ended questions; give concrete choices.
- Save each answer immediately as it comes.
- Questions should be deep ("deep se deep"), not surface-level.
