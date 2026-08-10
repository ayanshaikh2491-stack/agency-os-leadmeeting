"""Remote: deep crawl diagnosis - why does own-website crawl return nothing?"""
import os, sys, json, time, re
sys.path.insert(0, "/home/ubuntu/sba-backend")
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass

import requests
from bs4 import BeautifulSoup
sys.path.insert(0, "/home/ubuntu/sba-backend")
import admin.tools.lead_enrichment as le

SITES = [
    "https://papermoonpainting.com/",
    "https://beyondwow.com/",
    "https://www.texasqualityplumbing.com/",
    "https://www.johnmooreservices.com/",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

for site in SITES:
    print("\n" + "=" * 70)
    print("SITE:", site)
    dom = le._clean_domain(site)
    print("domain:", dom)
    for p in ("/", "/contact", "/about"):
        u = f"{site.rstrip('/')}{p}"
        try:
            r = requests.get(u, timeout=(3, 8), allow_redirects=True, headers=le.HEADERS)
            raw_emails = set(EMAIL_RE.findall(r.text or ""))
            valid = {e for e in raw_emails if le._is_valid_email(e, allow_consumer=True)}
            soup = BeautifulSoup(r.text or "", "html.parser")
            title = (soup.title.get_text() if soup.title else "")[:60]
            print(f"  {p:10s} status={r.status_code} len={len(r.text or ''):7d} raw_emails={len(raw_emails)} valid={len(valid)} title={title!r}")
            for e in sorted(raw_emails)[:6]:
                print(f"        raw: {e!r} valid={e in valid}")
            mailtos = [a['href'][7:].split('?')[0] for a in soup.select('a[href^="mailto:"]')]
            if mailtos:
                print(f"        mailto links: {mailtos[:5]}")
        except Exception as e:
            print(f"  {p:10s} ERROR: {type(e).__name__}: {str(e)[:100]}")
