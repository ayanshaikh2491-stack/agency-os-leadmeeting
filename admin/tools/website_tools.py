"""Website Tools — Real tools for Website Agent.

10 tools:
1. analyze_website — Crawl site, detect tech stack, structure, meta
2. check_performance — Page speed, load time, resources
3. check_links — Find broken links
4. seo_basics — Title, meta, headings, images SEO check
5. security_check — Security headers check
6. tech_stack_advisor — Recommend tech stack
7. design_planner — Plan site architecture, navigation
8. check_accessibility — Basic a11y checks
9. competitor_sites — Scan competitor websites
10. generate_sitemap — Generate XML sitemap
"""
from __future__ import annotations

import re
import json
import logging
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
_WEBSITE_TOOLS_LIST: list[dict[str, Any]] = []


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

    # Headings structure
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
        "images": {
            "total": len(images),
            "without_alt": images_without_alt,
        },
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

    # Resource counts
    css_files = len(soup.find_all("link", rel="stylesheet"))
    js_files = len(soup.find_all("script", src=True))
    images = soup.find_all("img")

    # Image sizes (approximate)
    large_images = 0
    for img in images:
        src = img.get("src", "")
        if src:
            width = img.get("width", "")
            height = img.get("height", "")
            try:
                if (int(width) > 1000 or int(height) > 1000):
                    large_images += 1
            except (ValueError, TypeError):
                pass

    # Inline styles/scripts
    inline_styles = len(soup.find_all("style"))
    inline_scripts = len(soup.find_all("script", src=False))

    # Compression check
    encoding = resp.headers.get("Content-Encoding", "none")

    # Caching
    cache_control = resp.headers.get("Cache-Control", "not set")

    # Score
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
        "resources": {
            "css_files": css_files,
            "js_files": js_files,
            "images": len(images),
            "large_images": large_images,
            "inline_styles": inline_styles,
            "inline_scripts": inline_scripts,
        },
        "optimization": {
            "compression": encoding,
            "cache_control": cache_control,
        },
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
    parsed = urlparse(url)
    links = []

    for a in soup.find_all("a", href=True)[:max_links * 2]:
        href = a["href"]
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full_url = urljoin(url, href)
        links.append(full_url)

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
# 4. SEO BASICS
# ═══════════════════════════════════════════════════════════════════════════════

def seo_basics(url: str) -> dict[str, Any]:
    """Basic SEO check: title, meta, headings, images, OG tags."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    issues = []
    score = 100

    # Title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if not title:
        score -= 15
        issues.append("Missing title tag")
    elif len(title) < 30:
        score -= 5
        issues.append(f"Title too short: {len(title)} chars (target: 30-60)")
    elif len(title) > 60:
        score -= 5
        issues.append(f"Title too long: {len(title)} chars (target: 30-60)")

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
    if not desc:
        score -= 15
        issues.append("Missing meta description")
    elif len(desc) < 120:
        score -= 5
        issues.append(f"Meta description too short: {len(desc)} chars (target: 120-160)")
    elif len(desc) > 160:
        score -= 5
        issues.append(f"Meta description too long: {len(desc)} chars")

    # OG Tags
    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    og_image = soup.find("meta", property="og:image")
    if not og_title:
        score -= 5
        issues.append("Missing og:title")
    if not og_desc:
        score -= 5
        issues.append("Missing og:description")
    if not og_image:
        score -= 5
        issues.append("Missing og:image")

    # Canonical
    canonical = soup.find("link", rel="canonical")
    if not canonical:
        score -= 5
        issues.append("Missing canonical tag")

    # Headings
    h1s = soup.find_all("h1")
    if len(h1s) == 0:
        score -= 10
        issues.append("No H1 tag found")
    elif len(h1s) > 1:
        score -= 5
        issues.append(f"Multiple H1 tags: {len(h1s)} (should be 1)")

    # Images without alt
    images = soup.find_all("img")
    no_alt = sum(1 for img in images if not img.get("alt", "").strip())
    if no_alt > 0:
        score -= min(10, no_alt * 2)
        issues.append(f"{no_alt}/{len(images)} images missing alt text")

    # Schema/structured data
    schemas = soup.find_all("script", type="application/ld+json")
    if not schemas:
        score -= 5
        issues.append("No structured data (JSON-LD)")

    # Viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        score -= 10
        issues.append("Missing viewport meta tag (not mobile-friendly)")

    return {
        "url": url,
        "checked_at": _now(),
        "score": max(0, score),
        "title": {"text": title, "length": len(title)},
        "meta_description": {"text": desc[:200], "length": len(desc)},
        "og_tags": {
            "title": bool(og_title),
            "description": bool(og_desc),
            "image": bool(og_image),
        },
        "canonical": bool(canonical),
        "headings": {"h1_count": len(h1s)},
        "images": {"total": len(images), "without_alt": no_alt},
        "structured_data": bool(schemas),
        "viewport": bool(viewport),
        "issues": issues,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SECURITY CHECK
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

    # HTTPS check
    is_https = url.startswith("https://")
    if not is_https:
        score -= 20
        issues.append("Not using HTTPS")

    # Server info leak
    server = headers.get("server", "")
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
# 6. TECH STACK ADVISOR
# ═══════════════════════════════════════════════════════════════════════════════

def tech_stack_advisor(
    site_type: str = "",
    needs_ecommerce: bool = False,
    needs_blog: bool = False,
    needs_admin: bool = False,
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
        recommendations.append({"stack": client_preference, "reason": "Client preference — adapt to their existing stack"})

    if not recommendations:
        recommendations.append({"stack": "Next.js + Tailwind + Vercel", "reason": "Default modern stack — fast, free hosting, great SEO"})

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
# 7. DESIGN PLANNER
# ═══════════════════════════════════════════════════════════════════════════════

def design_planner(
    site_type: str = "landing",
    pages: str = "home, about, services, contact",
    style: str = "modern",
) -> dict[str, Any]:
    """Plan site architecture, navigation, page structure."""
    page_list = [p.strip() for p in pages.split(",") if p.strip()]

    # Default page structure
    page_structures = {
        "home": {
            "sections": ["hero", "features/benefits", "testimonials", "cta", "footer"],
            "purpose": "First impression, convert visitors",
        },
        "about": {
            "sections": ["hero", "story", "team", "values", "cta"],
            "purpose": "Build trust, show brand personality",
        },
        "services": {
            "sections": ["hero", "service_list", "process", "pricing", "cta"],
            "purpose": "Showcase offerings, drive inquiries",
        },
        "contact": {
            "sections": ["hero", "contact_form", "map", "details", "social_links"],
            "purpose": "Enable communication, capture leads",
        },
        "blog": {
            "sections": ["hero", "featured_posts", "post_grid", "pagination"],
            "purpose": "Content marketing, SEO, thought leadership",
        },
        "pricing": {
            "sections": ["hero", "pricing_cards", "faq", "cta"],
            "purpose": "Show plans, drive conversions",
        },
        "portfolio": {
            "sections": ["hero", "project_grid", "case_study", "cta"],
            "purpose": "Showcase work, build credibility",
        },
    }

    planned_pages = []
    for page in page_list:
        structure = page_structures.get(page, {
            "sections": ["hero", "content", "cta"],
            "purpose": "Custom page",
        })
        planned_pages.append({"name": page, **structure})

    # Navigation
    nav = {"primary": page_list[:6], "footer": page_list}

    # Color palette suggestion based on style
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
        "typography": {
            "heading": "Inter" if style == "modern" else "Poppins",
            "body": "Inter",
        },
        "responsive_breakpoints": {"mobile": "375px", "tablet": "768px", "desktop": "1024px", "wide": "1280px"},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 8. CHECK ACCESSIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

def check_accessibility(url: str) -> dict[str, Any]:
    """Basic accessibility checks: alt text, headings, ARIA, color contrast hints."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    issues = []
    score = 100

    # Images without alt
    images = soup.find_all("img")
    no_alt = [img.get("src", "")[:80] for img in images if not img.get("alt", "").strip()]
    if no_alt:
        score -= min(15, len(no_alt) * 3)
        issues.append(f"{len(no_alt)} images missing alt text")

    # Links without text
    links = soup.find_all("a")
    empty_links = [a.get("href", "")[:80] for a in links if not a.get_text(strip=True) and not a.find("img") and not a.get("aria-label")]
    if empty_links:
        score -= min(10, len(empty_links) * 2)
        issues.append(f"{len(empty_links)} links without accessible text")

    # Form inputs without labels
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

    # Heading hierarchy
    headings = []
    for level in range(1, 7):
        for _ in soup.find_all(f"h{level}"):
            headings.append(level)
    skipped = 0
    for i in range(1, len(headings)):
        if headings[i] - headings[i-1] > 1:
            skipped += 1
    if skipped:
        score -= min(10, skipped * 3)
        issues.append(f"Heading hierarchy skipped {skipped} levels")

    # Language attribute
    html_tag = soup.find("html")
    has_lang = bool(html_tag and html_tag.get("lang"))
    if not has_lang:
        score -= 5
        issues.append("Missing lang attribute on <html>")

    # ARIA landmarks
    landmarks = soup.find_all(attrs={"role": True})
    if not landmarks and not soup.find("nav") and not soup.find("main"):
        score -= 5
        issues.append("No ARIA landmarks or semantic HTML (nav, main, footer)")

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
# 9. COMPETITOR SITES
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
            seo = seo_basics(url)
            results.append({
                "url": url,
                "title": analysis.get("title", ""),
                "tech_stack": analysis.get("tech_stack", []),
                "page_count": analysis.get("page_count", 0),
                "performance_score": perf.get("score", 0),
                "seo_score": seo.get("score", 0),
                "load_time": perf.get("load_time_seconds", 0),
            })
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    return {
        "analyzed_at": _now(),
        "competitors": results,
        "count": len(results),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 10. GENERATE SITEMAP
# ═══════════════════════════════════════════════════════════════

def generate_sitemap(url: str) -> dict[str, Any]:
    """Generate XML sitemap from website."""
    resp = _safe_get(url)
    if not resp:
        return {"error": f"Cannot reach {url}", "status": "failed"}

    soup = _soup(resp.text)
    parsed = urlparse(url)
    urls_found = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full = urljoin(url, href).split("#")[0].split("?")[0]
        if urlparse(full).netloc == parsed.netloc:
            urls_found.add(full)

    urls_found.add(url.rstrip("/"))

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in sorted(urls_found):
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{u}</loc>")
        xml_lines.append("    <changefreq>weekly</changefreq>")
        xml_lines.append("    <priority>0.8</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    return {
        "url": url,
        "generated_at": _now(),
        "url_count": len(urls_found),
        "xml": "\n".join(xml_lines),
        "urls": sorted(urls_found),
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
            "description": "Check page performance: load time, HTML size, resources, compression, caching. Returns performance score.",
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
            "name": "seo_basics",
            "description": "Basic SEO check: title, meta description, OG tags, headings, images alt, canonical, schema, viewport.",
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
            "name": "generate_sitemap",
            "description": "Generate XML sitemap from website by crawling internal links.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Website URL"}},
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
        "seo_basics": lambda a: seo_basics(a["url"]),
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
        "generate_sitemap": lambda a: generate_sitemap(a["url"]),
    }
    fn = dispatch.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            logger.exception("Website tool failed: %s", name)
            return {"error": str(e), "status": "failed"}
    return {"error": f"Unknown tool: {name}", "status": "failed"}
