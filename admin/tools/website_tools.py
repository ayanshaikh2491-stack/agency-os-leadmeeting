"""Website Tools — Real tools for Website Agent.

10 tools (NO SEO — SEO Agent ka kaam hai):
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
"""
from __future__ import annotations

import re
import ssl
import json
import socket
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
    }
    fn = dispatch.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            logger.exception("Website tool failed: %s", name)
            return {"error": str(e), "status": "failed"}
    return {"error": f"Unknown tool: {name}", "status": "failed"}
