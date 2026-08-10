"""Verify prioritize puts email-ready > enrichment-ready > no-website leads first."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")
from admin.agency.sba_reason import prioritize

leads = [
    {"name": "No Site A", "raw": {"lead_score": 90}, "website": "", "email": ""},
    {"name": "Site NoMail A", "raw": {"lead_score": 10}, "website": "https://a.com", "email": ""},
    {"name": "Has Email A", "raw": {"lead_score": 1}, "website": "", "email": "x@a.com"},
    {"name": "No Site B", "raw": {"lead_score": 95}, "website": "", "email": ""},
    {"name": "Site NoMail B", "raw": {"lead_score": 5}, "website": "https://b.com", "email": ""},
    {"name": "Site + Email", "raw": {"lead_score": 3}, "website": "https://c.com", "email": "y@c.com"},
]

order = [l["name"] for l in prioritize(leads)]
print("order:", order)
assert order[0] == "Site + Email", "email+website should top"
assert order[1] == "Has Email A", "email should beat website-only"
assert order.index("Site NoMail A") < order.index("No Site A"), "website-only beats no-site regardless of score"
assert order.index("Site NoMail B") < order.index("No Site B")
# within tier: score desc
assert order.index("Site NoMail A") < order.index("Site NoMail B")
print("PASS prioritize")
