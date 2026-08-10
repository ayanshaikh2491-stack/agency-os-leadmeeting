"""Test _is_valid_lead_email gate rejects the 2 junk + accepts real emails."""
import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int")
from admin.agency.sba_autopilot import _is_valid_lead_email

cases = [
    # (email, allow_consumer, expected)
    ("feedback@ground.news", False, False),   # junk prefix + aggregator
    ("hi@mystore.com", False, False),         # junk prefix + template
    ("feedback@ground.news", True, False),    # still junk even with consumer flag
    ("hi@mystore.com", True, False),
    ("shop@mikesdowntowngarage.com", False, True),  # own-domain real
    ("info.pawwow.lv@gmail.com", True, True),       # verified consumer
    ("info.pawwow.lv@gmail.com", False, False),     # consumer not allowed unverified
    ("office@theaussieplumber.com", False, True),   # own-domain real
    ("chosautobodyshophouston@gmail.com", True, True),  # verified consumer
    ("victoria@boltelectricsa.com", False, True),       # own-domain real
]

ok = True
for email, allow, expected in cases:
    got = _is_valid_lead_email(email, allow_consumer=allow)
    mark = "OK " if got == expected else "FAIL"
    if got != expected:
        ok = False
    print(f"{mark} {email!r:45} allow={allow} -> {got} (expected {expected})")

assert ok, "some gate cases failed"
print("PASS: all gate cases correct")
