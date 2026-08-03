"""Website Tools — Real tools for Website Agent.

15 tools (NO SEO — SEO Agent ka kaam hai):

Analysis (10):
1. analyze_website — Crawl site, detect tech stack, structure
2. check_performance — Page speed, load time, resources
3. check_links — Find broken links
4. security_check — Security headers check
5. tech_stack_advisor — Recommend tech stack
6. design_planner — Plan site architecture, navigation
7. check_accessibility — Basic a11y checks
8. competitor_sites — Scan competitor websites
9. responsive_check — Mobile responsiveness
10. check_ssl — SSL certificate status

Action (5):
11. generate_code — Generate Next.js/HTML/CSS code for a page
12. deploy_vercel — Deploy frontend+backend to Vercel
13. check_domain — Domain availability + DNS records
14. screenshot_site — Take a screenshot of a website
15. check_uptime — Monitor site uptime, response time, status
"""
from __future__ import annotations

import os
import re
import ssl
import json
import socket
import logging
import subprocess
import time
import dns.resolver
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_get(url: str, timeout: int = 15) -> requests.Response | None:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning("GET %s failed: %s", url, e)
        return None


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSITE PROJECT BUILDER (shared by build_site + generate_code)
# ═══════════════════════════════════════════════════════════════════════════════

_WEBSITE_PALETTES = {
    "modern": {"primary": "#2563EB", "secondary": "#1E293B", "accent": "#F59E0B", "bg": "#FFFFFF", "text": "#1E293B"},
    "minimal": {"primary": "#000000", "secondary": "#666666", "accent": "#2563EB", "bg": "#FFFFFF", "text": "#333333"},
    "bold": {"primary": "#DC2626", "secondary": "#1E293B", "accent": "#F59E0B", "bg": "#FFFFFF", "text": "#1E293B"},
    "warm": {"primary": "#D97706", "secondary": "#92400E", "accent": "#059669", "bg": "#FFFBEB", "text": "#451A03"},
    "tech": {"primary": "#7C3AED", "secondary": "#1E1B4B", "accent": "#06B6D4", "bg": "#FFFFFF", "text": "#1E1B4B"},
}

_DEFAULT_SERVICES = ["Fast Delivery", "Secure Builds", "Scalable Design"]


def _slugify(name: str) -> str:
    """Convert a name into a safe directory slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return slug or "website"


def _escape_html(text: Any) -> str:
    """Escape text for safe HTML embedding (XSS-safe)."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _html_section(sec: str, ctx: dict) -> str:
    esc = _escape_html
    title = esc(ctx["title"])
    tagline = esc(ctx["tagline"])
    email = esc(ctx["business_email"])
    services = ctx["services"]
    svc_cards = "".join(
        f'<div class="card"><h3>{esc(s)}</h3><p>Expert {esc(s.lower())} tailored to your goals.</p></div>'
        for s in services
    )
    if sec == "hero":
        subtitle = f'<p class="sub">{tagline}</p>' if tagline else ""
        return (
            f'<section class="hero"><h1>{title}</h1>{subtitle}'
            '<p>We build modern, fast, and secure websites that help your business grow.</p>'
            '<a href="#contact" class="btn">Get Started</a></section>'
        )
    if sec == "services":
        return f'<section class="services" id="services"><h2>Our Services</h2><div class="grid">{svc_cards}</div></section>'
    if sec == "about":
        return f'<section class="about" id="about"><h2>About Us</h2><p>{title} is a team of passionate builders creating impactful digital experiences.</p></section>'
    if sec == "testimonials":
        return (
            '<section class="testimonials" id="testimonials"><h2>What Clients Say</h2>'
            '<blockquote>"Professional, fast, and creative. Highly recommended!" — Happy Client</blockquote></section>'
        )
    if sec == "contact":
        contact_line = f'<p>Email us at <a href="mailto:{email}">{email}</a></p>' if email else ""
        return (
            f'<section class="contact" id="contact"><h2>Contact Us</h2>{contact_line}'
            '<form><input type="text" placeholder="Name" required><input type="email" placeholder="Email" required>'
            '<textarea placeholder="Message" required></textarea><button type="submit">Send</button></form></section>'
        )
    if sec == "footer":
        return f"<footer><p>&copy; 2026 {title}. All rights reserved.</p></footer>"
    if sec == "cta":
        return (
            '<section class="cta"><h2>Ready to Get Started?</h2>'
            '<p>Contact us today and let\'s build something amazing together.</p>'
            '<a href="#contact" class="btn">Contact Us</a></section>'
        )
    if sec == "features":
        return (
            '<section class="features" id="features"><h2>Features</h2><div class="grid">'
            '<div class="card"><h3>Fast</h3><p>Lightning fast performance</p></div>'
            '<div class="card"><h3>Secure</h3><p>Enterprise-grade security</p></div>'
            '<div class="card"><h3>Scalable</h3><p>Grows with your business</p></div>'
            '</div></section>'
        )
    if sec == "pricing":
        return (
            '<section class="pricing" id="pricing"><h2>Pricing</h2><div class="grid">'
            '<div class="card"><h3>Starter</h3><p>$29/mo</p></div>'
            '<div class="card"><h3>Pro</h3><p>$79/mo</p></div>'
            '<div class="card"><h3>Enterprise</h3><p>$199/mo</p></div>'
            '</div></section>'
        )
    return f'<section class="{sec}" id="{sec}"><h2>{sec.title()}</h2><p>Content for the {sec} section.</p></section>'


def _html_page(ctx: dict, body: str) -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"  <title>{_escape_html(ctx['title'])}</title>\n"
        "  <link rel=\"stylesheet\" href=\"style.css\">\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>"
    )


def _html_css(ctx: dict) -> str:
    c = ctx["colors"]
    return f"""/* Generated by Website Agent */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', system-ui, sans-serif; color: {c['text']}; background: {c['bg']}; }}
.hero {{ min-height: 80vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 4rem 2rem; background: {c['secondary']}; color: white; }}
.hero h1 {{ font-size: 3.5rem; margin-bottom: 1rem; }}
.hero .sub {{ font-size: 1.4rem; margin-bottom: 1rem; opacity: 0.95; }}
.hero p {{ font-size: 1.25rem; margin-bottom: 2rem; opacity: 0.9; }}
.services, .about, .testimonials, .pricing, .features, .contact {{ padding: 5rem 2rem; text-align: center; }}
.services h2, .about h2, .testimonials h2, .pricing h2, .features h2, .contact h2 {{ font-size: 2.5rem; margin-bottom: 2rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; max-width: 1100px; margin: 0 auto; }}
.card {{ background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
.card h3 {{ color: {c['primary']}; margin-bottom: 0.5rem; }}
.cta {{ background: {c['primary']}; color: white; padding: 5rem 2rem; text-align: center; }}
.cta h2 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
.cta p {{ font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.9; }}
.btn {{ display: inline-block; padding: 1rem 2.5rem; background: {c['accent']}; color: {c['secondary']}; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 1.1rem; transition: transform 0.2s; }}
.btn:hover {{ transform: translateY(-2px); }}
footer {{ background: {c['secondary']}; color: white; text-align: center; padding: 2rem; }}
form {{ display: flex; flex-direction: column; gap: 1rem; max-width: 500px; margin: 0 auto; }}
input, textarea {{ padding: 0.75rem; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; }}
button {{ padding: 0.75rem; background: {c['primary']}; color: white; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }}
blockquote {{ font-size: 1.2rem; font-style: italic; max-width: 600px; margin: 0 auto; padding: 2rem; border-left: 4px solid {c['primary']}; }}
@media (max-width: 768px) {{ .hero h1 {{ font-size: 2.2rem; }} }}
"""


def _nextjs_component(sec: str, ctx: dict) -> str:
    c = ctx["colors"]
    title = ctx["title"]
    tagline = ctx["tagline"]
    email = ctx["business_email"]
    services = ctx["services"]
    if sec == "services":
        return f"""export default function Services() {{
  const services = {json.dumps(services, ensure_ascii=False)};
  return (
    <section className="py-20 px-8 text-center" id="services">
      <h2 className="text-4xl font-bold mb-12">Our Services</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {{services.map((s, i) => (
          <div key={{i}} className="bg-white rounded-xl p-8 shadow-lg">
            <h3 className="text-lg font-bold mb-2" style={{{{color: '{c['primary']}'}}}}>{{s}}</h3>
            <p className="text-gray-600">Expert {{s.toLowerCase()}} tailored to your goals.</p>
          </div>
        ))}}
      </div>
    </section>
  );
}}"""
    if sec == "hero":
        return f"""export default function Hero() {{
  const title = {json.dumps(title, ensure_ascii=False)};
  const tagline = {json.dumps(tagline, ensure_ascii=False)};
  return (
    <section className="min-h-[80vh] flex flex-col items-center justify-center text-center px-8 bg-slate-800 text-white">
      <h1 className="text-5xl font-bold mb-4">{{title}}</h1>
      {{tagline && <p className="text-xl mb-4 opacity-95">{{tagline}}</p>}}
      <p className="text-xl mb-8 opacity-90">We build modern, fast, and secure websites that help your business grow.</p>
      <a href="#contact" className="bg-amber-500 text-slate-800 px-8 py-3 rounded-lg font-semibold hover:-translate-y-1 transition-transform">Get Started</a>
    </section>
  );
}}"""
    if sec == "about":
        return f"""export default function About() {{
  const title = {json.dumps(title, ensure_ascii=False)};
  return (
    <section className="py-20 px-8 text-center" id="about">
      <h2 className="text-4xl font-bold mb-12">About Us</h2>
      <p className="text-gray-600 max-w-2xl mx-auto">{{title}} is a team of passionate builders creating impactful digital experiences.</p>
    </section>
  );
}}"""
    if sec == "testimonials":
        return """export default function Testimonials() {
  return (
    <section className="py-20 px-8 text-center" id="testimonials">
      <h2 className="text-4xl font-bold mb-12">What Clients Say</h2>
      <blockquote className="text-xl italic max-w-2xl mx-auto border-l-4 border-blue-600 pl-8 text-left">
        "Professional, fast, and creative. Highly recommended!" — Happy Client
      </blockquote>
    </section>
  );
}"""
    if sec == "contact":
        email_block = ""
        if email:
            email_block = ('<p className="text-lg mb-4">Email us at <a href="mailto:{email}" className="underline">{email}</a></p>')
        return f"""export default function Contact() {{
  const email = {json.dumps(email, ensure_ascii=False)};
  return (
    <section className="py-20 px-8 text-center" id="contact">
      <h2 className="text-4xl font-bold mb-12">Contact Us</h2>
      {email_block}
      <form className="flex flex-col gap-4 max-w-md mx-auto" onSubmit={{e => e.preventDefault()}}>
        <input className="p-3 border border-gray-300 rounded-lg" placeholder="Name" required />
        <input className="p-3 border border-gray-300 rounded-lg" placeholder="Email" required />
        <textarea className="p-3 border border-gray-300 rounded-lg" placeholder="Message" required />
        <button className="p-3 bg-blue-600 text-white rounded-lg cursor-pointer">Send</button>
      </form>
    </section>
  );
}}"""
    if sec == "footer":
        return f"""export default function Footer() {{
  const title = {json.dumps(title, ensure_ascii=False)};
  return (
    <footer className="bg-slate-800 text-white text-center py-6">
      <p>&copy; 2026 {{title}}. All rights reserved.</p>
    </footer>
  );
}}"""
    if sec == "features":
        return """export default function Features() {
  const features = [
    { title: "Fast", desc: "Lightning fast performance" },
    { title: "Secure", desc: "Enterprise-grade security" },
    { title: "Scalable", desc: "Grows with your business" },
  ];
  return (
    <section className="py-20 px-8 text-center" id="features">
      <h2 className="text-4xl font-bold mb-12">Features</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {features.map((f, i) => (
          <div key={i} className="bg-white rounded-xl p-8 shadow-lg">
            <h3 className="text-lg font-bold text-blue-600 mb-2">{f.title}</h3>
            <p className="text-gray-600">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}"""
    if sec == "cta":
        return """export default function CTA() {
  return (
    <section className="py-20 px-8 text-center bg-blue-600 text-white">
      <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
      <p className="text-lg mb-8 opacity-90">Contact us today.</p>
      <a href="#contact" className="bg-amber-500 text-slate-800 px-8 py-3 rounded-lg font-semibold hover:-translate-y-1 transition-transform inline-block">Contact Us</a>
    </section>
  );
}"""
    if sec == "pricing":
        return """export default function Pricing() {
  return (
    <section className="py-20 px-8 text-center" id="pricing">
      <h2 className="text-4xl font-bold mb-12">Pricing</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        <div className="bg-white rounded-xl p-8 shadow-lg"><h3 className="text-lg font-bold mb-2">Starter</h3><p>$29/mo</p></div>
        <div className="bg-white rounded-xl p-8 shadow-lg"><h3 className="text-lg font-bold mb-2">Pro</h3><p>$79/mo</p></div>
        <div className="bg-white rounded-xl p-8 shadow-lg"><h3 className="text-lg font-bold mb-2">Enterprise</h3><p>$199/mo</p></div>
      </div>
    </section>
  );
}"""
    name = sec.title().replace(" ", "")
    return f"""export default function {name}() {{
  return (
    <section className="py-20 px-8 text-center" id="{sec}">
      <h2 className="text-4xl font-bold mb-4">{sec.title()}</h2>
      <p className="text-gray-600">Content for the {sec} section.</p>
    </section>
  );
}}"""


def _nextjs_page(section_list: list[str], ctx: dict) -> str:
    imports = "\n".join(
        f"import {s.title().replace(' ', '')} from './components/{s.title().replace(' ', '')}';"
        for s in section_list
    )
    calls = "\n      ".join(f"<{s.title().replace(' ', '')} />" for s in section_list)
    title = json.dumps(ctx["title"], ensure_ascii=False)
    return f"""// app/page.tsx — Generated by Website Agent
{imports}

export default function Home() {{
  const title = {title};
  return (
    <main>
      <h1 className="text-4xl font-bold text-center py-12">{{title}}</h1>
      {calls}
    </main>
  );
}}
"""


def _nextjs_layout(ctx: dict) -> str:
    title = _escape_html(ctx["title"])
    return f"""// app/layout.tsx — Generated by Website Agent
import type {{ Metadata }} from "next";
import "./globals.css";

export const metadata: Metadata = {{
  title: "{title}",
  description: "Official website of {title}.",
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def _nextjs_globals_css(ctx: dict) -> str:
    c = ctx["colors"]
    return f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --color-primary: {c['primary']};
  --color-secondary: {c['secondary']};
  --color-accent: {c['accent']};
  --color-bg: {c['bg']};
  --color-text: {c['text']};
}}

body {{
  color: var(--color-text);
  background: var(--color-bg);
}}
"""


def _nextjs_package_json(title: str) -> str:
    return json.dumps({
        "name": _slugify(title),
        "version": "0.1.0",
        "private": True,
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint"},
        "dependencies": {"next": "^14.2.0", "react": "^18.3.1", "react-dom": "^18.3.1"},
        "devDependencies": {
            "@types/node": "^20", "@types/react": "^18", "@types/react-dom": "^18",
            "autoprefixer": "^10", "postcss": "^8", "tailwindcss": "^3.4.0", "typescript": "^5",
        },
    }, indent=2)


def _nextjs_tailwind_config(ctx: dict) -> str:
    c = ctx["colors"]
    return f"""import type {{ Config }} from "tailwindcss";

const config: Config = {{
  content: [
    "./app/**/*.{{js,ts,jsx,tsx,mdx}}",
    "./components/**/*.{{js,ts,jsx,tsx,mdx}}",
  ],
  theme: {{
    extend: {{
      colors: {{
        primary: "{c['primary']}",
        secondary: "{c['secondary']}",
        accent: "{c['accent']}",
      }},
    }},
  }},
  plugins: [],
}};

export default config;
"""


def _build_readme(ctx: dict, framework: str) -> str:
    if framework == "html":
        return f"""# {ctx['title']}

Generated by the Website Agent.

## Run locally
Open `index.html` in a browser (or run `python -m http.server`).

## Customize
Edit `style.css` for colors and fonts. Sections live in `index.html`.
"""
    return f"""# {ctx['title']}

Generated by the Website Agent.

## Run locally
```bash
npm install
npm run dev
```

## Build & deploy
```bash
npm run build
npx vercel deploy --prod
```

## Structure
- `app/page.tsx` — home page (imports section components)
- `app/layout.tsx` — root layout + metadata
- `app/globals.css` — Tailwind + design tokens
- `components/*.tsx` — Hero, Services, About, Testimonials, Contact, Footer
"""


def _build_instructions(framework: str, title: str) -> str:
    if framework == "html":
        return "Save files next to each other and open index.html in a browser. Ready to deploy to any static host (Vercel, Netlify, GitHub Pages)."
    return "1. npm install\n2. npm run dev — preview locally\n3. npm run build && npx vercel deploy --prod — deploy to Vercel"


def _build_website_project(
    *,
    title: str = "My Website",
    tagline: str = "",
    industry: str = "",
    services: list[str] | None = None,
    business_email: str = "",
    sections: list[str] | None = None,
    style: str = "modern",
    color_primary: str = "#2563EB",
    framework: str = "nextjs",
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """Build a complete website project dict (rel_path -> content). Deterministic, no network, no LLM."""
    skills = [s for s in (skills or []) if s]
    title = (title or "").strip() or "My Website"
    tagline = (tagline or "").strip()
    services = [s.strip() for s in (services or []) if s and s.strip()] or list(_DEFAULT_SERVICES)
    section_list = [s.strip().lower() for s in (sections or ["hero", "services", "about", "testimonials", "contact", "footer"]) if s and s.strip()]
    if not section_list:
        section_list = ["hero", "services", "about", "testimonials", "contact", "footer"]

    colors = dict(_WEBSITE_PALETTES.get(style, _WEBSITE_PALETTES["modern"]))
    colors["primary"] = color_primary or colors["primary"]

    if "nextjs-developer" in skills or "react-expert" in skills:
        framework = framework or "nextjs"

    ctx = {
        "title": title,
        "tagline": tagline,
        "industry": industry,
        "services": services,
        "business_email": business_email or "",
        "colors": colors,
        "style": style,
    }

    if framework == "html":
        body = "".join(_html_section(s, ctx) for s in section_list)
        page_code = _html_page(ctx, body)
        files = {"index.html": page_code, "style.css": _html_css(ctx)}
        components = {}
    else:
        components = {}
        for s in section_list:
            name = s.title().replace(" ", "")
            components[f"components/{name}.tsx"] = _nextjs_component(s, ctx)
        page_code = _nextjs_page(section_list, ctx)
        files = {
            "package.json": _nextjs_package_json(title),
            "app/layout.tsx": _nextjs_layout(ctx),
            "app/globals.css": _nextjs_globals_css(ctx),
            "app/page.tsx": page_code,
            "tailwind.config.ts": _nextjs_tailwind_config(ctx),
            "README.md": _build_readme(ctx, framework),
        }
        files.update(components)

    return {
        "framework": framework,
        "style": style,
        "sections": section_list,
        "colors": colors,
        "title": title,
        "tagline": tagline,
        "industry": industry,
        "services": services,
        "business_email": business_email or "",
        "skills_applied": skills,
        "page_code": page_code,
        "files": files,
        "components": components,
        "file_count": len(files),
        "instructions": _build_instructions(framework, title),
        "generated_at": _now(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ANALYZE WEBSITE
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_website(url: str) -> dict[str, Any]:
    """Crawl a website and analyze structure, tech stack, meta info, navigation."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    parsed = urlparse(url)

    # Tech stack detection
    tech_stack = []
    html_lower = resp.text.lower()
    headers = {k.lower(): v for k, v in resp.headers.items()}

    if "next" in html_lower or "__next" in html_lower:
        tech_stack.append("Next.js")
    if "react" in html_lower or "_react" in html_lower:
        tech_stack.append("React")
    if "vue" in html_lower or "v-if" in html_lower or "v-for" in html_lower:
        tech_stack.append("Vue.js")
    if "angular" in html_lower or "ng-app" in html_lower:
        tech_stack.append("Angular")
    if "wordpress" in html_lower or "wp-content" in html_lower:
        tech_stack.append("WordPress")
    if "shopify" in html_lower or "cdn.shopify.com" in html_lower:
        tech_stack.append("Shopify")
    if "webflow" in html_lower or "webflow.com" in html_lower:
        tech_stack.append("Webflow")
    if "squarespace" in html_lower:
        tech_stack.append("Squarespace")
    if "wix" in html_lower:
        tech_stack.append("Wix")
    if "tailwind" in html_lower or "tw-" in html_lower:
        tech_stack.append("Tailwind CSS")
    if "bootstrap" in html_lower:
        tech_stack.append("Bootstrap")
    if "jquery" in html_lower:
        tech_stack.append("jQuery")
    if headers.get("server") == "cloudflare" or "cf-ray" in headers:
        tech_stack.append("Cloudflare")
    if headers.get("server", "").lower().startswith("nginx"):
        tech_stack.append("Nginx")
    if headers.get("server", "").lower().startswith("apache"):
        tech_stack.append("Apache")
    if "vercel" in headers.get("server", "").lower() or "x-vercel" in headers:
        tech_stack.append("Vercel")

    # Meta info
    meta = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name", "") or tag.get("property", "")
        content = tag.get("content", "")
        if name and content:
            meta[name] = content

    # Navigation
    nav_links = []
    nav = soup.find("nav") or soup.find(class_=re.compile(r"nav|menu", re.I))
    if nav:
        for a in nav.find_all("a", href=True):
            text = a.get_text(strip=True)[:50]
            if text:
                nav_links.append(text)

    # Pages (internal links)
    internal_links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") or parsed.netloc in href:
            full = urljoin(url, href)
            if urlparse(full).netloc == parsed.netloc:
                internal_links.add(full.split("#")[0].split("?")[0])

    # Images
    images = soup.find_all("img")
    images_without_alt = sum(1 for img in images if not img.get("alt", "").strip())

    # Headings
    headings = {}
    for level in range(1, 7):
        h_tags = soup.find_all(f"h{level}")
        if h_tags:
            headings[f"h{level}"] = len(h_tags)

    return {
        "url": url,
        "analyzed_at": _now(),
        "title": soup.title.string.strip() if soup.title and soup.title.string else "",
        "meta": meta,
        "tech_stack": tech_stack,
        "navigation": nav_links[:15],
        "page_count": len(internal_links),
        "internal_links": list(internal_links)[:50],
        "images": {"total": len(images), "without_alt": images_without_alt},
        "headings": headings,
        "headers": {k: v[:100] for k, v in headers.items() if k in ["server", "content-type", "x-powered-by"]},
        "status_code": resp.status_code,
        "redirect_chain": [r.url for r in resp.history] if resp.history else [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CHECK PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

def check_performance(url: str) -> dict[str, Any]:
    """Check page performance: load time, size, resources."""
    import time
    start = time.time()
    resp = _safe_get(url)
    load_time = round(time.time() - start, 2)

    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    html_size = len(resp.content)
    css_files = len(soup.find_all("link", rel="stylesheet"))
    js_files = len(soup.find_all("script", src=True))
    images = soup.find_all("img")

    large_images = 0
    for img in images:
        try:
            if int(img.get("width", 0)) > 1000 or int(img.get("height", 0)) > 1000:
                large_images += 1
        except (ValueError, TypeError):
            pass

    inline_styles = len(soup.find_all("style"))
    inline_scripts = len(soup.find_all("script", src=False))
    encoding = resp.headers.get("Content-Encoding", "none")
    cache_control = resp.headers.get("Cache-Control", "not set")

    score = 100
    issues = []
    if load_time > 3:
        score -= 30
        issues.append(f"Slow load: {load_time}s (target: <3s)")
    elif load_time > 1:
        score -= 10
        issues.append(f"Moderate load: {load_time}s")
    if html_size > 500_000:
        score -= 20
        issues.append(f"Large HTML: {html_size/1000:.0f}KB (target: <200KB)")
    if css_files > 10:
        score -= 10
        issues.append(f"Too many CSS files: {css_files}")
    if js_files > 15:
        score -= 15
        issues.append(f"Too many JS files: {js_files}")
    if encoding == "none":
        score -= 10
        issues.append("No compression (gzip/brotli)")
    if cache_control == "not set":
        score -= 5
        issues.append("No cache-control header")
    if large_images > 3:
        score -= 10
        issues.append(f"{large_images} large images detected")

    return {
        "url": url,
        "checked_at": _now(),
        "load_time_seconds": load_time,
        "html_size_bytes": html_size,
        "html_size_kb": round(html_size / 1024, 1),
        "resources": {"css_files": css_files, "js_files": js_files, "images": len(images), "large_images": large_images, "inline_styles": inline_styles, "inline_scripts": inline_scripts},
        "optimization": {"compression": encoding, "cache_control": cache_control},
        "score": max(0, score),
        "issues": issues,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CHECK LINKS
# ═══════════════════════════════════════════════════════════════════════════════

def check_links(url: str, max_links: int = 50) -> dict[str, Any]:
    """Find broken links on a page."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    links = []
    for a in soup.find_all("a", href=True)[:max_links * 2]:
        href = a["href"]
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        links.append(urljoin(url, href))
    links = list(set(links))[:max_links]

    broken = []
    working = 0
    for link in links:
        try:
            r = requests.head(link, headers=_HEADERS, timeout=10, allow_redirects=True)
            if r.status_code >= 400:
                broken.append({"url": link, "status": r.status_code})
            else:
                working += 1
        except Exception:
            broken.append({"url": link, "status": "timeout"})

    return {
        "url": url,
        "checked_at": _now(),
        "total_links_checked": len(links),
        "working": working,
        "broken": broken,
        "broken_count": len(broken),
        "health_score": round((working / max(len(links), 1)) * 100),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SECURITY CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def security_check(url: str) -> dict[str, Any]:
    """Check security headers."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    headers = {k.lower(): v for k, v in resp.headers.items()}
    issues = []
    score = 100

    security_headers = {
        "strict-transport-security": {"name": "HSTS", "critical": True},
        "content-security-policy": {"name": "Content Security Policy", "critical": True},
        "x-frame-options": {"name": "X-Frame-Options", "critical": False},
        "x-content-type-options": {"name": "X-Content-Type-Options", "critical": False},
        "x-xss-protection": {"name": "X-XSS-Protection", "critical": False},
        "referrer-policy": {"name": "Referrer Policy", "critical": False},
        "permissions-policy": {"name": "Permissions Policy", "critical": False},
    }

    present = {}
    missing = []
    for header, info in security_headers.items():
        if header in headers:
            present[header] = headers[header][:100]
        else:
            missing.append(info["name"])
            score -= 15 if info["critical"] else 5
            issues.append(f"Missing {info['name']}")

    is_https = url.startswith("https://")
    if not is_https:
        score -= 20
        issues.append("Not using HTTPS")

    x_powered = headers.get("x-powered-by", "")
    if x_powered:
        score -= 5
        issues.append(f"X-Powered-By exposed: {x_powered}")

    return {
        "url": url,
        "checked_at": _now(),
        "is_https": is_https,
        "score": max(0, score),
        "headers_present": present,
        "headers_missing": missing,
        "issues": issues,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TECH STACK ADVISOR
# ═══════════════════════════════════════════════════════════════════════════════

def tech_stack_advisor(
    site_type: str = "",
    needs_ecommerce: bool = False,
    needs_blog: bool = False,
    budget: str = "medium",
    client_preference: str = "",
) -> dict[str, Any]:
    """Recommend tech stack based on project needs."""
    recommendations = []

    if needs_ecommerce:
        if budget == "low":
            recommendations.append({"stack": "Shopify", "reason": "Quick setup, managed hosting, low maintenance"})
        else:
            recommendations.append({"stack": "Next.js + Stripe", "reason": "Full control, better performance, scalable"})

    if needs_blog:
        if budget == "low":
            recommendations.append({"stack": "WordPress", "reason": "Easy content management, huge plugin ecosystem"})
        else:
            recommendations.append({"stack": "Next.js + MDX", "reason": "Fast, SEO-friendly, developer-friendly"})

    if site_type in ("landing", "portfolio", "saas"):
        recommendations.append({"stack": "Next.js + Tailwind", "reason": "Fast, modern, great SEO, easy to deploy on Vercel"})
    if site_type in ("corporate", "enterprise"):
        recommendations.append({"stack": "Next.js + Headless CMS", "reason": "Scalable, secure, flexible content management"})
    if site_type in ("webapp", "dashboard"):
        recommendations.append({"stack": "Next.js + React + PostgreSQL", "reason": "Full-stack, type-safe, great DX"})

    if client_preference:
        recommendations.append({"stack": client_preference, "reason": "Client preference"})

    if not recommendations:
        recommendations.append({"stack": "Next.js + Tailwind + Vercel", "reason": "Default modern stack"})

    hosting = "Vercel" if any("Next.js" in r["stack"] for r in recommendations) else "AWS/Netlify"
    cms = "None (code-based)" if not needs_blog else ("Sanity/Contentful" if budget != "low" else "WordPress")

    return {
        "site_type": site_type,
        "needs_ecommerce": needs_ecommerce,
        "needs_blog": needs_blog,
        "budget": budget,
        "recommendations": recommendations,
        "hosting": hosting,
        "cms": cms,
        "design_tool": "Figma",
        "version_control": "Git + GitHub",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DESIGN PLANNER
# ═══════════════════════════════════════════════════════════════════════════════

def design_planner(
    site_type: str = "landing",
    pages: str = "home, about, services, contact",
    style: str = "modern",
) -> dict[str, Any]:
    """Plan site architecture, navigation, page structure."""
    page_list = [p.strip() for p in pages.split(",") if p.strip()]

    page_structures = {
        "home": {"sections": ["hero", "features/benefits", "testimonials", "cta", "footer"], "purpose": "First impression, convert visitors"},
        "about": {"sections": ["hero", "story", "team", "values", "cta"], "purpose": "Build trust, show brand personality"},
        "services": {"sections": ["hero", "service_list", "process", "pricing", "cta"], "purpose": "Showcase offerings, drive inquiries"},
        "contact": {"sections": ["hero", "contact_form", "map", "details", "social_links"], "purpose": "Enable communication, capture leads"},
        "blog": {"sections": ["hero", "featured_posts", "post_grid", "pagination"], "purpose": "Content marketing, SEO"},
        "pricing": {"sections": ["hero", "pricing_cards", "faq", "cta"], "purpose": "Show plans, drive conversions"},
        "portfolio": {"sections": ["hero", "project_grid", "case_study", "cta"], "purpose": "Showcase work, build credibility"},
    }

    planned_pages = [{"name": p, **page_structures.get(p, {"sections": ["hero", "content", "cta"], "purpose": "Custom page"})} for p in page_list]
    nav = {"primary": page_list[:6], "footer": page_list}

    palettes = {
        "modern": {"primary": "#2563EB", "secondary": "#1E293B", "accent": "#F59E0B", "bg": "#FFFFFF"},
        "minimal": {"primary": "#000000", "secondary": "#666666", "accent": "#2563EB", "bg": "#FFFFFF"},
        "bold": {"primary": "#DC2626", "secondary": "#1E293B", "accent": "#F59E0B", "bg": "#FFFFFF"},
        "warm": {"primary": "#D97706", "secondary": "#92400E", "accent": "#059669", "bg": "#FFFBEB"},
        "tech": {"primary": "#7C3AED", "secondary": "#1E1B4B", "accent": "#06B6D4", "bg": "#FFFFFF"},
    }

    return {
        "site_type": site_type,
        "style": style,
        "pages": planned_pages,
        "navigation": nav,
        "color_palette": palettes.get(style, palettes["modern"]),
        "typography": {"heading": "Inter" if style == "modern" else "Poppins", "body": "Inter"},
        "responsive_breakpoints": {"mobile": "375px", "tablet": "768px", "desktop": "1024px", "wide": "1280px"},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CHECK ACCESSIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

def check_accessibility(url: str) -> dict[str, Any]:
    """Basic accessibility checks: alt text, headings, ARIA, color contrast hints."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    issues = []
    score = 100

    images = soup.find_all("img")
    no_alt = [img.get("src", "")[:80] for img in images if not img.get("alt", "").strip()]
    if no_alt:
        score -= min(15, len(no_alt) * 3)
        issues.append(f"{len(no_alt)} images missing alt text")

    links = soup.find_all("a")
    empty_links = [a.get("href", "")[:80] for a in links if not a.get_text(strip=True) and not a.find("img") and not a.get("aria-label")]
    if empty_links:
        score -= min(10, len(empty_links) * 2)
        issues.append(f"{len(empty_links)} links without accessible text")

    inputs = soup.find_all(["input", "textarea", "select"])
    unlabeled = 0
    for inp in inputs:
        if inp.get("type") in ("hidden", "submit", "button"):
            continue
        inp_id = inp.get("id", "")
        has_label = bool(inp_id and soup.find("label", attrs={"for": inp_id}))
        has_aria = bool(inp.get("aria-label") or inp.get("aria-labelledby"))
        if not has_label and not has_aria:
            unlabeled += 1
    if unlabeled:
        score -= min(10, unlabeled * 2)
        issues.append(f"{unlabeled} form inputs without labels")

    headings = []
    for level in range(1, 7):
        for _ in soup.find_all(f"h{level}"):
            headings.append(level)
    skipped = 0
    for i in range(1, len(headings)):
        if headings[i] - headings[i - 1] > 1:
            skipped += 1
    if skipped:
        score -= min(10, skipped * 3)
        issues.append(f"Heading hierarchy skipped {skipped} levels")

    html_tag = soup.find("html")
    has_lang = bool(html_tag and html_tag.get("lang"))
    if not has_lang:
        score -= 5
        issues.append("Missing lang attribute on <html>")

    landmarks = soup.find_all(attrs={"role": True})
    if not landmarks and not soup.find("nav") and not soup.find("main"):
        score -= 5
        issues.append("No ARIA landmarks or semantic HTML")

    return {
        "url": url,
        "checked_at": _now(),
        "score": max(0, score),
        "images_total": len(images),
        "images_without_alt": len(no_alt),
        "empty_links": len(empty_links),
        "unlabeled_inputs": unlabeled,
        "heading_skips": skipped,
        "has_lang": has_lang,
        "issues": issues,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 8. COMPETITOR SITES
# ═══════════════════════════════════════════════════════════════════════════════

def competitor_sites(urls: list[str]) -> dict[str, Any]:
    """Scan multiple competitor websites for comparison."""
    results = []
    for url in urls[:5]:
        url = url.strip()
        if not url.startswith("http"):
            url = "https://" + url
        try:
            analysis = analyze_website(url)
            perf = check_performance(url)
            results.append({
                "url": url,
                "title": analysis.get("title", ""),
                "tech_stack": analysis.get("tech_stack", []),
                "page_count": analysis.get("page_count", 0),
                "performance_score": perf.get("score", 0),
                "load_time": perf.get("load_time_seconds", 0),
            })
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    return {"analyzed_at": _now(), "competitors": results, "count": len(results)}


# ═══════════════════════════════════════════════════════════════════════════════
# 9. RESPONSIVE CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def responsive_check(url: str) -> dict[str, Any]:
    """Check mobile responsiveness: viewport, media queries, mobile-friendly."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    issues = []
    score = 100

    viewport = soup.find("meta", attrs={"name": "viewport"})
    has_viewport = bool(viewport)
    viewport_content = viewport.get("content", "") if viewport else ""
    if not has_viewport:
        score -= 30
        issues.append("Missing viewport meta tag")
    elif "width=device-width" not in viewport_content:
        score -= 10
        issues.append("Viewport missing device-width")

    # CSS media queries
    media_queries = 0
    for tag in soup.find_all("style"):
        text = tag.string or ""
        media_queries += len(re.findall(r"@media", text))
    for tag in soup.find_all(style=True)[:20]:
        if "max-width" in tag.get("style", "") or "min-width" in tag.get("style", ""):
            media_queries += 1
    if media_queries == 0:
        score -= 15
        issues.append("No CSS media queries found (may not be responsive)")

    # Fixed widths
    fixed_widths = 0
    for tag in soup.find_all(style=True)[:30]:
        if re.search(r"width:\s*\d{4,}px", tag.get("style", "")):
            fixed_widths += 1
    if fixed_widths > 3:
        score -= 10
        issues.append(f"{fixed_widths} elements with fixed widths >1000px")

    # Large images
    images = soup.find_all("img")
    large_unconstrained = 0
    for img in images:
        try:
            if int(img.get("width", 0)) > 800:
                large_unconstrained += 1
        except (ValueError, TypeError):
            pass
    if large_unconstrained > 2:
        score -= 10
        issues.append(f"{large_unconstrained} large images may overflow on mobile")

    return {
        "url": url,
        "checked_at": _now(),
        "score": max(0, score),
        "has_viewport": has_viewport,
        "viewport_content": viewport_content,
        "media_queries_found": media_queries,
        "fixed_width_elements": fixed_widths,
        "images_total": len(images),
        "issues": issues,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 10. CHECK SSL
# ═══════════════════════════════════════════════════════════════════════════════

def check_ssl(url: str) -> dict[str, Any]:
    """Check SSL certificate status."""
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    hostname = parsed.hostname or ""
    port = parsed.port or 443

    if not hostname:
        return {"error": "Invalid URL", "status": "failed"}

    result: dict[str, Any] = {
        "url": url,
        "hostname": hostname,
        "checked_at": _now(),
        "is_https": url.startswith("https"),
        "ssl_valid": False,
        "issuer": "",
        "subject": "",
        "not_before": "",
        "not_after": "",
        "days_until_expiry": 0,
        "protocol": "",
        "issues": [],
    }

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                result["ssl_valid"] = True
                result["protocol"] = ssock.version() or ""

                issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                result["issuer"] = issuer_dict.get("organizationName", issuer_dict.get("commonName", ""))

                subject_dict = dict(x[0] for x in cert.get("subject", []))
                result["subject"] = subject_dict.get("commonName", "")

                result["not_before"] = cert.get("notBefore", "")
                not_after = cert.get("notAfter", "")
                result["not_after"] = not_after

                if not_after:
                    try:
                        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        days = (expiry - datetime.utcnow()).days
                        result["days_until_expiry"] = days
                        if days < 30:
                            result["issues"].append(f"SSL expires in {days} days!")
                        elif days < 90:
                            result["issues"].append(f"SSL expires in {days} days — renew soon")
                    except ValueError:
                        pass

    except ssl.SSLCertVerificationError as e:
        result["issues"].append(f"SSL verification failed: {str(e)[:100]}")
    except socket.timeout:
        result["issues"].append("Connection timeout")
    except socket.gaierror:
        result["issues"].append(f"Cannot resolve hostname: {hostname}")
    except Exception as e:
        result["issues"].append(f"SSL check failed: {str(e)[:100]}")

    if not result["is_https"]:
        result["issues"].insert(0, "Site is not using HTTPS")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 11. GENERATE CODE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_code(
    page_type: str = "landing",
    framework: str = "nextjs",
    style: str = "modern",
    sections: str = "hero,features,cta,footer",
    color_primary: str = "#2563EB",
    title: str = "My Website",
) -> dict[str, Any]:
    """Generate starter code for a website page (Next.js or HTML/CSS)."""
    section_list = [s.strip() for s in sections.split(",") if s.strip()]

    # Color palette
    palette = {
        "modern": {"primary": color_primary, "secondary": "#1E293B", "accent": "#F59E0B", "bg": "#FFFFFF", "text": "#1E293B"},
        "minimal": {"primary": "#000000", "secondary": "#666666", "accent": color_primary, "bg": "#FFFFFF", "text": "#333333"},
        "bold": {"primary": "#DC2626", "secondary": "#1E293B", "accent": "#F59E0B", "bg": "#FFFFFF", "text": "#1E293B"},
        "warm": {"primary": "#D97706", "secondary": "#92400E", "accent": "#059669", "bg": "#FFFBEB", "text": "#451A03"},
        "tech": {"primary": "#7C3AED", "secondary": "#1E1B4B", "accent": "#06B6D4", "bg": "#FFFFFF", "text": "#1E1B4B"},
    }
    colors = palette.get(style, palette["modern"])

    if framework == "html":
        # Generate plain HTML + CSS
        sections_html = ""
        for sec in section_list:
            if sec == "hero":
                sections_html += f"""
  <section class="hero">
    <h1>{title}</h1>
    <p>Welcome to our website. We build amazing things.</p>
    <a href="#contact" class="btn">Get Started</a>
  </section>"""
            elif sec == "features":
                sections_html += """
  <section class="features">
    <h2>Features</h2>
    <div class="grid">
      <div class="card"><h3>Fast</h3><p>Lightning fast performance</p></div>
      <div class="card"><h3>Secure</h3><p>Enterprise-grade security</p></div>
      <div class="card"><h3>Scalable</h3><p>Grows with your business</p></div>
    </div>
  </section>"""
            elif sec == "cta":
                sections_html += """
  <section class="cta">
    <h2>Ready to Get Started?</h2>
    <p>Contact us today and let's build something amazing together.</p>
    <a href="#contact" class="btn">Contact Us</a>
  </section>"""
            elif sec == "footer":
                sections_html += """
  <footer>
    <p>&copy; 2026 """ + title + """. All rights reserved.</p>
  </footer>"""
            elif sec == "about":
                sections_html += """
  <section class="about">
    <h2>About Us</h2>
    <p>We are a team of passionate developers building the future of web.</p>
  </section>"""
            elif sec == "contact":
                sections_html += """
  <section class="contact" id="contact">
    <h2>Contact Us</h2>
    <form><input type="text" placeholder="Name" required><input type="email" placeholder="Email" required><textarea placeholder="Message" required></textarea><button type="submit">Send</button></form>
  </section>"""
            elif sec == "testimonials":
                sections_html += """
  <section class="testimonials">
    <h2>What Our Clients Say</h2>
    <blockquote>"Amazing work! Highly recommend." — Client Name</blockquote>
  </section>"""
            elif sec == "pricing":
                sections_html += """
  <section class="pricing">
    <h2>Pricing</h2>
    <div class="grid">
      <div class="card"><h3>Starter</h3><p>$29/mo</p></div>
      <div class="card"><h3>Pro</h3><p>$79/mo</p></div>
      <div class="card"><h3>Enterprise</h3><p>$199/mo</p></div>
    </div>
  </section>"""
            else:
                sections_html += f'\n  <section class="{sec}"><h2>{sec.title()}</h2><p>Content for {sec} section.</p></section>'

        html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', system-ui, sans-serif; color: {colors['text']}; background: {colors['bg']}; }}
    .hero {{ min-height: 80vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 4rem 2rem; background: {colors['secondary']}; color: white; }}
    .hero h1 {{ font-size: 3.5rem; margin-bottom: 1rem; }}
    .hero p {{ font-size: 1.25rem; margin-bottom: 2rem; opacity: 0.9; }}
    .features, .about, .testimonials, .pricing, .contact {{ padding: 5rem 2rem; text-align: center; }}
    .features h2, .about h2, .testimonials h2, .pricing h2, .contact h2 {{ font-size: 2.5rem; margin-bottom: 2rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; max-width: 1100px; margin: 0 auto; }}
    .card {{ background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    .card h3 {{ color: {colors['primary']}; margin-bottom: 0.5rem; }}
    .cta {{ background: {colors['primary']}; color: white; padding: 5rem 2rem; text-align: center; }}
    .cta h2 {{ font-size: 2.5rem; margin-bottom: 1rem; }}
    .cta p {{ font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.9; }}
    .btn {{ display: inline-block; padding: 1rem 2.5rem; background: {colors['accent']}; color: {colors['secondary']}; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 1.1rem; transition: transform 0.2s; }}
    .btn:hover {{ transform: translateY(-2px); }}
    footer {{ background: {colors['secondary']}; color: white; text-align: center; padding: 2rem; }}
    form {{ display: flex; flex-direction: column; gap: 1rem; max-width: 500px; margin: 0 auto; }}
    input, textarea {{ padding: 0.75rem; border: 1px solid #ddd; border-radius: 8px; font-size: 1rem; }}
    button {{ padding: 0.75rem; background: {colors['primary']}; color: white; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; }}
    blockquote {{ font-size: 1.2rem; font-style: italic; max-width: 600px; margin: 0 auto; padding: 2rem; border-left: 4px solid {colors['primary']}; }}
    @media (max-width: 768px) {{ .hero h1 {{ font-size: 2.2rem; }} }}
  </style>
</head>
<body>
{sections_html}
</body>
</html>"""

        return {
            "framework": "html",
            "style": style,
            "sections": section_list,
            "colors": colors,
            "title": title,
            "code": html_code,
            "instructions": "Save as index.html and open in browser. Ready to deploy.",
            "generated_at": _now(),
        }

    # Next.js (default)
    components = []
    for sec in section_list:
        if sec == "hero":
            components.append("""export default function Hero() {
  return (
    <section className="min-h-[80vh] flex flex-col items-center justify-center text-center px-8 bg-slate-800 text-white">
      <h1 className="text-5xl font-bold mb-4">{title}</h1>
      <p className="text-xl mb-8 opacity-90">Welcome to our website. We build amazing things.</p>
      <a href="#contact" className="bg-amber-500 text-slate-800 px-8 py-3 rounded-lg font-semibold hover:-translate-y-1 transition-transform">Get Started</a>
    </section>
  );
}""")
        elif sec == "features":
            components.append("""export default function Features() {
  const features = [
    { title: "Fast", desc: "Lightning fast performance" },
    { title: "Secure", desc: "Enterprise-grade security" },
    { title: "Scalable", desc: "Grows with your business" },
  ];
  return (
    <section className="py-20 px-8 text-center">
      <h2 className="text-4xl font-bold mb-12">Features</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {features.map((f, i) => (
          <div key={i} className="bg-white rounded-xl p-8 shadow-lg">
            <h3 className="text-lg font-bold text-blue-600 mb-2">{f.title}</h3>
            <p className="text-gray-600">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}""")
        elif sec == "cta":
            components.append(f"""export default function CTA() {{
  return (
    <section className="py-20 px-8 text-center bg-blue-600 text-white">
      <h2 className="text-4xl font-bold mb-4">Ready to Get Started?</h2>
      <p className="text-lg mb-8 opacity-90">Contact us today.</p>
      <a href="#contact" className="bg-amber-500 text-slate-800 px-8 py-3 rounded-lg font-semibold hover:-translate-y-1 transition-transform inline-block">Contact Us</a>
    </section>
  );
}}""")
        elif sec == "footer":
            components.append(f"""export default function Footer() {{
  return (
    <footer className="bg-slate-800 text-white text-center py-6">
      <p>&copy; 2026 {title}. All rights reserved.</p>
    </footer>
  );
}}""")
        else:
            components.append(f"""export default function {sec.title()}() {{
  return (
    <section className="py-20 px-8 text-center">
      <h2 className="text-4xl font-bold mb-4">{sec.title()}</h2>
      <p className="text-gray-600">Content for {sec} section.</p>
    </section>
  );
}}""")

    # Build page.tsx
    imports = "\n".join(f"import {sec.title()} from './components/{sec.title()}';" for sec in section_list)
    calls = "\n      ".join(f"<{sec.title()} />" for sec in section_list)

    page_code = f"""// app/page.tsx — Generated by Website Agent
{imports}

export default function Home() {{
  return (
    <main>
      {calls}
    </main>
  );
}}
"""

    nextjs_code = {
        "framework": "nextjs",
        "style": style,
        "sections": section_list,
        "colors": colors,
        "title": title,
        "page_code": page_code,
        "components": {sec.title(): code for sec, code in zip(section_list, components)},
        "instructions": (
            "1. Create Next.js project: npx create-next-app@latest\n"
            "2. Replace app/page.tsx with page_code above\n"
            "3. Create components/ folder with each component file\n"
            "4. Run: npm run dev\n"
            "5. Deploy: vercel deploy"
        ),
        "generated_at": _now(),
    }

    return nextjs_code


def build_site(
    title: str = "My Website",
    tagline: str = "",
    industry: str = "",
    sections: str = "hero,services,about,testimonials,contact,footer",
    style: str = "modern",
    color_primary: str = "#2563EB",
    framework: str = "nextjs",
    services: str = "",
    business_email: str = "",
    output_dir: str = "",
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """Build a complete website project on disk from business info.

    Writes real files (Next.js project or HTML) and returns the file list.
    """
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    project = _build_website_project(
        title=title,
        tagline=tagline,
        industry=industry,
        services=[s.strip() for s in services.split(",") if s.strip()],
        business_email=business_email,
        sections=[s.strip() for s in sections.split(",") if s.strip()],
        style=style,
        color_primary=color_primary,
        framework=framework,
        skills=skills or [],
    )
    if not output_dir:
        output_dir = os.path.join("generated_sites", _slugify(project["title"]))
    written = []
    for rel_path, content in project["files"].items():
        full_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(rel_path)
    preview = "open index.html in a browser" if project["framework"] == "html" else f"run `npm run dev` in {output_dir}"
    return {
        **project,
        "status": "built",
        "output_dir": output_dir,
        "files_written": written,
        "file_count": len(written),
        "preview_url_hint": preview,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 12. DEPLOY TO VERCEL
# ═══════════════════════════════════════════════════════════════════════════════

def deploy_vercel(
    project_path: str = ".",
    project_name: str = "",
    prod: bool = True,
    env_vars: str = "",
) -> dict[str, Any]:
    """Deploy a project to Vercel (frontend+backend). Uses vercel CLI."""
    import os

    # Check if vercel CLI is installed
    try:
        result = subprocess.run(
            ["vercel", "--version"],
            capture_output=True, text=True, timeout=10,
            cwd=project_path if os.path.isdir(project_path) else ".",
        )
        if result.returncode != 0:
            return {
                "error": "Vercel CLI not found. Install: npm i -g vercel",
                "status": "failed",
                "install_command": "npm i -g vercel",
            }
    except FileNotFoundError:
        return {
            "error": "Vercel CLI not found. Install: npm i -g vercel",
            "status": "failed",
            "install_command": "npm i -g vercel",
        }
    except subprocess.TimeoutExpired:
        return {"error": "Vercel CLI check timed out", "status": "failed"}

    # Build deploy command
    cmd = ["vercel", "--yes"]
    if prod:
        cmd.append("--prod")
    if project_name:
        cmd.extend(["--name", project_name])

    # Parse env vars (KEY=VALUE,KEY2=VALUE2)
    env_list = []
    if env_vars:
        for pair in env_vars.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                env_list.append(f"{k.strip()}={v.strip()}")

    for env in env_list:
        cmd.extend(["--env", env])

    # Deploy
    try:
        deploy_start = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=300,
            cwd=project_path if os.path.isdir(project_path) else ".",
        )
        deploy_time = round(time.time() - deploy_start, 1)

        output = result.stdout + result.stderr

        # Extract URL from output
        url = ""
        for line in output.split("\n"):
            line = line.strip()
            if "https://" in line and "vercel" in line:
                url = line
                break
            if line.startswith("https://"):
                url = line
                break

        return {
            "status": "deployed" if result.returncode == 0 else "failed",
            "project_name": project_name or "auto",
            "project_path": project_path,
            "production": prod,
            "url": url,
            "deploy_time_seconds": deploy_time,
            "output": output[:3000],
            "deployed_at": _now(),
        }
    except subprocess.TimeoutExpired:
        return {"error": "Deploy timed out (300s limit)", "status": "failed"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}


# ═══════════════════════════════════════════════════════════════════════════════
# 13. CHECK DOMAIN
# ═══════════════════════════════════════════════════════════════════════════════

def check_domain(domain: str) -> dict[str, Any]:
    """Check domain availability, DNS records, and registrar info."""
    # Clean domain
    domain = domain.strip().lower()
    if domain.startswith("http"):
        domain = urlparse(domain).hostname or domain
    domain = domain.replace("www.", "")

    result: dict[str, Any] = {
        "domain": domain,
        "checked_at": _now(),
        "dns_records": {},
        "has_website": False,
        "ssl_info": {},
        "issues": [],
    }

    # DNS records
    record_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS"]
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records = [str(r) for r in answers]
            result["dns_records"][rtype] = records
            if rtype == "A" or rtype == "AAAA":
                result["has_website"] = True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass
        except Exception:
            pass

    # Check if site responds
    for scheme in ["https", "http"]:
        url = f"{scheme}://{domain}"
        resp = _safe_get(url, timeout=8)
        if resp:
            result["has_website"] = True
            result["status_code"] = resp.status_code
            result["final_url"] = resp.url
            result["title"] = ""
            soup = _soup(resp.text)
            if soup.title and soup.title.string:
                result["title"] = soup.title.string.strip()[:100]
            break

    # SSL check
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert.get("issuer", []))
                result["ssl_info"] = {
                    "valid": True,
                    "issuer": issuer.get("organizationName", issuer.get("commonName", "")),
                    "expires": cert.get("notAfter", ""),
                }
    except Exception:
        result["ssl_info"] = {"valid": False}

    # Suggestions
    if not result["has_website"]:
        result["issues"].append("Domain has no active website")
    if not result["dns_records"]:
        result["issues"].append("No DNS records found — domain may be available")
    if not result.get("ssl_info", {}).get("valid"):
        result["issues"].append("No valid SSL certificate")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 14. SCREENSHOT SITE
# ═══════════════════════════════════════════════════════════════════════════════

def screenshot_site(
    url: str,
    width: int = 1280,
    height: int = 800,
) -> dict[str, Any]:
    """Take a screenshot of a website using requests-based approach.

    For full browser screenshots, use the Chrome Agent (CDP).
    This tool captures page metadata + visual indicators.
    """
    resp = _safe_get(url, timeout=15)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)

    # Extract visual metadata
    og_image = ""
    for meta in soup.find_all("meta"):
        if meta.get("property") == "og:image":
            og_image = meta.get("content", "")
            break

    # Extract all images
    images = []
    for img in soup.find_all("img")[:20]:
        src = img.get("src", "")
        if src:
            src = urljoin(url, src)
        images.append({
            "src": src,
            "alt": img.get("alt", ""),
            "width": img.get("width", ""),
            "height": img.get("height", ""),
        })

    # Favicon
    favicon = ""
    link = soup.find("link", rel=lambda r: r and "icon" in r)
    if link:
        favicon = urljoin(url, link.get("href", ""))

    # Background colors
    bg_colors = set()
    for tag in soup.find_all(style=True)[:30]:
        style = tag.get("style", "")
        color_match = re.findall(r"background(?:-color)?:\s*(#[0-9a-fA-F]{3,8})", style)
        bg_colors.update(color_match)

    # Try to capture screenshot via CDP if available
    screenshot_path = ""
    try:
        from admin.tools.chrome_tool import ChromeTool
        chrome = ChromeTool()
        # This would need async context — skip for sync tool
        # Just report that CDP is available
    except Exception:
        pass

    return {
        "url": url,
        "captured_at": _now(),
        "viewport": {"width": width, "height": height},
        "title": soup.title.string.strip()[:100] if soup.title and soup.title.string else "",
        "og_image": og_image,
        "favicon": favicon,
        "images": images,
        "image_count": len(images),
        "bg_colors": list(bg_colors)[:10],
        "screenshot_available": bool(screenshot_path),
        "note": "For full browser screenshots, use Chrome Agent via CDP or Playwright",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 15. CHECK UPTIME
# ═══════════════════════════════════════════════════════════════════════
def check_uptime(
    url: str,
    checks: int = 3,
    interval: int = 2,
) -> dict[str, Any]:
    """Monitor site uptime: check response time, status code, SSL over multiple pings."""
    results = []
    status_counts: dict[str, int] = {}
    response_times = []

    for i in range(checks):
        start = time.time()
        try:
            resp = requests.get(
                url, headers=_HEADERS, timeout=15, allow_redirects=True
            )
            elapsed = round(time.time() - start, 3)
            status = resp.status_code

            results.append({
                "check": i + 1,
                "status": status,
                "response_time_ms": round(elapsed * 1000),
                "size_bytes": len(resp.content),
                "redirected": len(resp.history) > 0,
                "final_url": resp.url,
            })

            status_key = f"{status}"
            status_counts[status_key] = status_counts.get(status_key, 0) + 1
            response_times.append(elapsed)
        except requests.exceptions.Timeout:
            elapsed = round(time.time() - start, 3)
            results.append({"check": i + 1, "status": "timeout", "response_time_ms": round(elapsed * 1000)})
            status_counts["timeout"] = status_counts.get("timeout", 0) + 1
        except requests.exceptions.ConnectionError:
            results.append({"check": i + 1, "status": "connection_error"})
            status_counts["connection_error"] = status_counts.get("connection_error", 0) + 1
        except Exception as e:
            results.append({"check": i + 1, "status": "error", "error": str(e)[:100]})
            status_counts["error"] = status_counts.get("error", 0) + 1

        if i < checks - 1:
            time.sleep(interval)

    # Calculate stats
    avg_response = round(sum(response_times) / len(response_times) * 1000, 1) if response_times else 0
    min_response = round(min(response_times) * 1000, 1) if response_times else 0
    max_response = round(max(response_times) * 1000, 1) if response_times else 0

    success_count = sum(v for k, v in status_counts.items() if k.startswith("2"))
    uptime_percent = round((success_count / max(checks, 1)) * 100, 1)

    # SSL check
    ssl_valid = False
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        hostname = parsed.hostname
        if hostname:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=8) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    ssl_valid = True
    except Exception:
        pass

    # Health assessment
    if uptime_percent == 100 and avg_response < 2000:
        health = "healthy"
    elif uptime_percent >= 80:
        health = "degraded"
    else:
        health = "unhealthy"

    return {
        "url": url,
        "checked_at": _now(),
        "checks_performed": checks,
        "uptime_percent": uptime_percent,
        "health": health,
        "response_time": {
            "avg_ms": avg_response,
            "min_ms": min_response,
            "max_ms": max_response,
        },
        "status_distribution": status_counts,
        "ssl_valid": ssl_valid,
        "checks": results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

WEBSITE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_website",
            "description": "Crawl a website and analyze structure, tech stack, meta info, navigation, images.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Website URL to analyze"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_performance",
            "description": "Check page performance: load time, HTML size, resources, compression, caching. Returns score.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to check"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_links",
            "description": "Find broken links on a page. Checks each link and reports broken ones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Page URL to check"},
                    "max_links": {"type": "integer", "description": "Max links to check (default 50)", "default": 50},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "security_check",
            "description": "Check security headers: HTTPS, HSTS, CSP, X-Frame-Options, etc.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to check"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tech_stack_advisor",
            "description": "Recommend tech stack based on project needs (site type, ecommerce, blog, budget).",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_type": {"type": "string", "description": "landing, corporate, saas, webapp, portfolio"},
                    "needs_ecommerce": {"type": "boolean", "default": False},
                    "needs_blog": {"type": "boolean", "default": False},
                    "budget": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
                    "client_preference": {"type": "string", "description": "Client's preferred tech"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "design_planner",
            "description": "Plan site architecture: pages, sections, navigation, color palette, typography.",
            "parameters": {
                "type": "object",
                "properties": {
                    "site_type": {"type": "string", "default": "landing"},
                    "pages": {"type": "string", "description": "Comma-separated page names", "default": "home, about, services, contact"},
                    "style": {"type": "string", "enum": ["modern", "minimal", "bold", "warm", "tech"], "default": "modern"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_accessibility",
            "description": "Basic a11y check: alt text, labels, heading hierarchy, ARIA landmarks, lang attribute.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to check"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "competitor_sites",
            "description": "Scan competitor websites: tech stack, performance, SEO score comparison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "List of competitor URLs"},
                },
                "required": ["urls"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "responsive_check",
            "description": "Check mobile responsiveness: viewport meta, CSS media queries, fixed widths, large images.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to check"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_ssl",
            "description": "Check SSL certificate: valid, expiry date, issuer, protocol version.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to check"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_code",
            "description": "Generate starter code for a website page (Next.js components or HTML/CSS). Returns ready-to-use code with color palette and sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_type": {"type": "string", "description": "landing, portfolio, saas, corporate", "default": "landing"},
                    "framework": {"type": "string", "enum": ["nextjs", "html"], "default": "nextjs"},
                    "style": {"type": "string", "enum": ["modern", "minimal", "bold", "warm", "tech"], "default": "modern"},
                    "sections": {"type": "string", "description": "Comma-separated sections: hero,features,cta,footer,about,contact,testimonials,pricing", "default": "hero,features,cta,footer"},
                    "color_primary": {"type": "string", "description": "Primary color hex code", "default": "#2563EB"},
                    "title": {"type": "string", "description": "Website/page title", "default": "My Website"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_site",
            "description": "Build a complete website project on disk (Next.js or HTML) from business info: title, tagline, services, email, sections, colors. Writes real files and returns the file list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Website/business name", "default": "My Website"},
                    "tagline": {"type": "string", "description": "One-line value proposition", "default": ""},
                    "industry": {"type": "string", "description": "Industry (tech, food, agency, etc.)", "default": ""},
                    "sections": {"type": "string", "description": "Comma-separated sections: hero,services,about,testimonials,contact,footer", "default": "hero,services,about,testimonials,contact,footer"},
                    "style": {"type": "string", "enum": ["modern", "minimal", "bold", "warm", "tech"], "default": "modern"},
                    "color_primary": {"type": "string", "description": "Primary color hex code", "default": "#2563EB"},
                    "framework": {"type": "string", "enum": ["nextjs", "html"], "default": "nextjs"},
                    "services": {"type": "string", "description": "Comma-separated service names (e.g. Web Design, SEO, Branding)", "default": ""},
                    "business_email": {"type": "string", "description": "Contact email shown in contact section + footer", "default": ""},
                    "output_dir": {"type": "string", "description": "Where to write the project (default generated_sites/<title-slug>)", "default": ""},
                    "skills": {"type": "array", "items": {"type": "string"}, "description": "Matched skill names to bias defaults", "default": []},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_vercel",
            "description": "Deploy a project to Vercel (frontend+backend). Uses vercel CLI. Returns deploy URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to project directory", "default": "."},
                    "project_name": {"type": "string", "description": "Vercel project name"},
                    "prod": {"type": "boolean", "description": "Deploy to production", "default": True},
                    "env_vars": {"type": "string", "description": "Comma-separated env vars: KEY1=val1,KEY2=val2"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_domain",
            "description": "Check domain: DNS records (A, AAAA, CNAME, MX, TXT, NS), SSL, website status, availability hints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain name to check (e.g. example.com)"},
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot_site",
            "description": "Capture website visual metadata: title, OG image, favicon, images, background colors, layout info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to capture"},
                    "width": {"type": "integer", "description": "Viewport width", "default": 1280},
                    "height": {"type": "integer", "description": "Viewport height", "default": 800},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_uptime",
            "description": "Monitor site uptime: multiple health checks, response time stats, SSL validity, health assessment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to monitor"},
                    "checks": {"type": "integer", "description": "Number of checks to perform (default 3)", "default": 3},
                    "interval": {"type": "integer", "description": "Seconds between checks (default 2)", "default": 2},
                },
                "required": ["url"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL EXECUTION ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def execute_website_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Route tool call to actual function."""
    dispatch = {
        "analyze_website": lambda a: analyze_website(a["url"]),
        "check_performance": lambda a: check_performance(a["url"]),
        "check_links": lambda a: check_links(a["url"], a.get("max_links", 50)),
        "security_check": lambda a: security_check(a["url"]),
        "tech_stack_advisor": lambda a: tech_stack_advisor(
            site_type=a.get("site_type", ""),
            needs_ecommerce=a.get("needs_ecommerce", False),
            needs_blog=a.get("needs_blog", False),
            budget=a.get("budget", "medium"),
            client_preference=a.get("client_preference", ""),
        ),
        "design_planner": lambda a: design_planner(
            site_type=a.get("site_type", "landing"),
            pages=a.get("pages", "home, about, services, contact"),
            style=a.get("style", "modern"),
        ),
        "check_accessibility": lambda a: check_accessibility(a["url"]),
        "competitor_sites": lambda a: competitor_sites(a["urls"]),
        "responsive_check": lambda a: responsive_check(a["url"]),
        "check_ssl": lambda a: check_ssl(a["url"]),
        "generate_code": lambda a: generate_code(
            page_type=a.get("page_type", "landing"),
            framework=a.get("framework", "nextjs"),
            style=a.get("style", "modern"),
            sections=a.get("sections", "hero,features,cta,footer"),
            color_primary=a.get("color_primary", "#2563EB"),
            title=a.get("title", "My Website"),
        ),
        "build_site": lambda a: build_site(
            title=a.get("title", "My Website"),
            tagline=a.get("tagline", ""),
            industry=a.get("industry", ""),
            sections=a.get("sections", "hero,services,about,testimonials,contact,footer"),
            style=a.get("style", "modern"),
            color_primary=a.get("color_primary", "#2563EB"),
            framework=a.get("framework", "nextjs"),
            services=a.get("services", ""),
            business_email=a.get("business_email", ""),
            output_dir=a.get("output_dir", ""),
            skills=a.get("skills", []),
        ),
        "deploy_vercel": lambda a: deploy_vercel(
            project_path=a.get("project_path", "."),
            project_name=a.get("project_name", ""),
            prod=a.get("prod", True),
            env_vars=a.get("env_vars", ""),
        ),
        "check_domain": lambda a: check_domain(a["domain"]),
        "screenshot_site": lambda a: screenshot_site(
            url=a["url"],
            width=a.get("width", 1280),
            height=a.get("height", 800),
        ),
        "check_uptime": lambda a: check_uptime(
            url=a["url"],
            checks=a.get("checks", 3),
            interval=a.get("interval", 2),
        ),
    }
    fn = dispatch.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            logger.exception("Website tool failed: %s", name)
            return {"error": str(e), "status": "failed"}
    return {"error": f"Unknown tool: {name}", "status": "failed"}
