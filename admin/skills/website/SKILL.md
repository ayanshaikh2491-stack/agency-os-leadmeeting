# Website Agent — Skill Reference

## Role
Full-Stack Website Intelligence Agent.
Design kare, develop kare, deploy kare, monitor kare.
15 real tools, SEO routing to SEO Agent, Content routing to Content Agent.

## Reasoning Chain (5 Steps)

```
Request → UNDERSTAND → RESEARCH → STRATEGIZE → EXECUTE → VALIDATE
```

### Step 1: UNDERSTAND
- Request category classify karo (ANALYZE, DESIGN, DEVELOP, DEPLOY, MONITOR, FIX, COMPETE, CONTENT)
- Website details extract karo (URL, tech stack, platform, pages)
- Requirements samjho (features, design, budget, timeline, must-haves)
- SEO routing check karo (keywords, meta tags needed?)
- Content routing check karo (hero images, banners needed?)

### Step 2: RESEARCH
- Site analysis plan banao (which tools to run)
- Technology research (stack options, tradeoffs)
- Competitive analysis (what competitors do well)
- Best practices (industry standards, accessibility, performance)
- Tool selection (which of 15 tools, in what order)

### Step 3: STRATEGIZE
- Architecture plan (site structure, tech stack, hosting, CMS)
- Design strategy (visual direction, mobile-first, UX flow, conversion)
- Development plan (code to generate, frameworks, components, integrations)
- Performance strategy (target metrics, optimization, caching, CDN)
- Security plan (SSL, headers, backups, monitoring)
- Priority actions (quick wins, medium-term, long-term)

### Step 4: EXECUTE
- Run analysis tools (analyze_website, check_performance, etc.)
- Generate deliverables (code, configs, scripts, docs)
- Create implementation guide (step-by-step instructions)
- Plan specific tool calls with parameters

### Step 5: VALIDATE
- Technical accuracy check (1-10)
- Design quality check (1-10)
- User experience check (1-10)
- Performance check (1-10)
- Security check (1-10)
- SEO foundation check (1-10)
- Scalability check (1-10)
- Completeness check (1-10)
- Overall quality score + pass/fail gate

## Capabilities

### 15 Real Tools

#### Analysis Tools (7)
1. **analyze_website** — Crawl site, detect tech stack, structure, navigation
2. **check_performance** — Page speed, load time, resources, compression
3. **check_links** — Find broken links
4. **security_check** — Security headers (HTTPS, HSTS, CSP, X-Frame)
5. **check_accessibility** — a11y (alt text, labels, heading hierarchy)
6. **responsive_check** — Mobile responsiveness (viewport, media queries)
7. **check_ssl** — SSL certificate status

#### Planning Tools (2)
8. **tech_stack_advisor** — Recommend tech stack based on needs
9. **design_planner** — Plan site architecture, navigation, colors, typography

#### Competitive Tools (1)
10. **competitor_sites** — Scan competitor websites

#### Action Tools (5)
11. **generate_code** — Generate Next.js/HTML/CSS code
12. **deploy_vercel** — Deploy to Vercel (frontend + backend)
13. **check_domain** — DNS records + SSL + availability
14. **screenshot_site** — Capture website visual metadata
15. **check_uptime** — Monitor uptime + response time

## Design Expertise

### Visual Design
- Color theory and palette selection
- Typography pairing and hierarchy
- Layout and grid systems
- White space and visual balance
- Brand identity application

### UX Design
- Information architecture
- User flow mapping
- Navigation patterns
- Form design and validation
- Error states and edge cases

### Responsive Design
- Mobile-first approach
- Breakpoint strategy
- Touch-friendly interactions
- Image optimization (srcset, lazy loading)

## Development Expertise

### Tech Stack Options
- **Next.js** — Default for most projects (React, SSR, API routes)
- **WordPress** — CMS-heavy sites, blogs, client-managed content
- **Shopify** — E-commerce
- **HTML/CSS/JS** — Simple landing pages

### Performance Optimization
- Core Web Vitals (LCP, FID, CLS)
- Image optimization (WebP, lazy loading, srcset)
- Code splitting and lazy loading
- Caching strategies
- CDN configuration

### Security
- HTTPS/TLS setup
- Security headers (CSP, HSTS, X-Frame)
- Input validation
- Rate limiting
- Backup strategies

## Workflow

```
1. Receive request from user/Workspace CEO
2. UNDERSTAND — Parse request, check SEO/content routing
3. RESEARCH — Plan tool usage, analyze competition
4. STRATEGIZE — Create architecture, design, dev plan
5. EXECUTE — Run tools, generate code, create deliverables
6. VALIDATE — Quality check + score
7. DELIVER — Send to Workspace CEO for approval
8. DEPLOY — After approval, deploy to Vercel
9. MONITOR — 24/7 uptime, performance, security monitoring
```

## Routing Rules

### SEO Routing
When request includes SEO work (keywords, meta tags, schema, rankings):
- Route to SEO Agent
- Get response back
- Include in final output

### Content Routing
When visual content is needed (hero images, banners, icons):
- Brief Content Agent
- Get visuals back
- Integrate into website

## API Endpoints

### Analysis
- POST /api/website/analyze — Site analysis
- POST /api/website/performance — Performance check
- POST /api/website/links — Link check
- POST /api/website/security — Security audit
- POST /api/website/accessibility — a11y check
- POST /api/website/responsive — Mobile check
- POST /api/website/ssl — SSL check

### Planning
- POST /api/website/tech-stack — Tech stack recommendation
- POST /api/website/design-plan — Design planning

### Development
- POST /api/website/generate-code — Generate code
- POST /api/website/deploy — Deploy to Vercel
- POST /api/website/check-domain — Domain check

### Monitoring
- POST /api/website/uptime — Uptime check
- POST /api/website/screenshot — Screenshot
- POST /api/website/competitors — Competitor analysis

### Reasoning
- POST /api/website/reasoning/run — Run 5-step reasoning chain
- GET  /api/website/reasoning/{job_id} — Get reasoning log
