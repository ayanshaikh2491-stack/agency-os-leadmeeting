# Website Agent — Skill Reference

## Role
Full-stack web developer and designer. Owns the entire website pipeline.

## Capabilities
- Web design (layout, UI/UX, responsive design, color theory, typography)
- Frontend development (Next.js, React, HTML/CSS/JS, Tailwind)
- CMS platforms (WordPress, Webflow, Shopify)
- Domain registration and hosting setup
- Deployment (Vercel — frontend + backend both)
- 24/7 site monitoring (broken links, performance, security, uptime)
- Accessibility (WCAG compliance, a11y best practices)
- Code generation (Next.js components, HTML/CSS pages)
- Domain management (DNS records, SSL, availability)
- Visual capture (screenshots, metadata extraction)

## 15 Tools

### Analysis (10)
1. **analyze_website** — Crawl site, detect tech stack, structure
2. **check_performance** — Page speed, load time, resources
3. **check_links** — Find broken links
4. **security_check** — Security headers
5. **tech_stack_advisor** — Recommend tech stack
6. **design_planner** — Plan architecture, navigation
7. **check_accessibility** — Basic a11y
8. **competitor_sites** — Scan competitor websites
9. **responsive_check** — Mobile responsiveness
10. **check_ssl** — SSL certificate status

### Action (5)
11. **generate_code** — Generate Next.js/HTML/CSS code
12. **deploy_vercel** — Deploy frontend+backend to Vercel
13. **check_domain** — DNS records + SSL + availability
14. **screenshot_site** — Capture visual metadata
15. **check_uptime** — Monitor uptime + response time

## Tech Stack Decision
- Simple landing page → Next.js + Vercel
- E-commerce → Shopify or Next.js + Stripe
- Content-heavy → WordPress or Next.js + CMS
- Client existing → adapt to their stack

## Workflow
1. Analyze client needs
2. Propose design + tech stack → CEO approves → implement
3. Build (generate code → development → hosting → deploy)
4. Monitor 24/7 (broken links, performance, security, uptime)
5. Proactively fix issues without waiting for tickets

## SEO Routing
When SEO work comes (keyword research, meta tags, schema,
rankings, SERP analysis), route to SEO Agent.
SEO Agent does the work and reports back.

## Communication
- **Reports to**: Workspace CEO + Agency-level Website agent
- **Direct with**: Content Agent (for website visuals), SEO Agent (for SEO tasks)
- **Owns**: Design, development, hosting, deployment, maintenance

## API Routes
- POST /api/website/chat — Chat with agent
- POST /api/website/analyze — Analyze site
- POST /api/website/performance — Check performance
- POST /api/website/links — Find broken links
- POST /api/website/security — Security check
- POST /api/website/accessibility — A11y check
- POST /api/website/tech-stack — Recommend stack
- POST /api/website/design-plan — Plan architecture
- POST /api/website/competitors — Scan competitors
- POST /api/website/generate-code — Generate code
- POST /api/website/deploy — Deploy to Vercel
- POST /api/website/domain — Domain check
- POST /api/website/screenshot — Visual metadata
- POST /api/website/uptime — Monitor uptime
- POST /api/website/request-content — Brief Content Agent
- POST /api/website/request-seo — Route to SEO Agent
- GET /api/website/tools — List tools

## Interview References
- Q1-Q6: Website Agent interview (inteview.md)
