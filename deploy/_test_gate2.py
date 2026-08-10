"""Local gate test: placeholder emails must be rejected, legit ones pass."""
import sys, os
sys.path.insert(0, ".")
from admin.agency.sba_autopilot import _is_valid_lead_email

cases = [
    # (email, allow_consumer, expect)
    ("user@domain.com", False, False),
    ("john@doe.com", False, False),
    ("user@domain.com", True, False),
    ("john@doe.com", True, False),
    ("chad@thenashvillehandyman.com", False, True),
    ("customerservice@avantigreen.com", False, True),
    ("nathan@texasplumbing911.com", False, True),
    ("office@presidioroof.com", False, True),
    ("marissamunizocdcleaners@gmail.com", True, True),
    ("marissamunizocdcleaners@gmail.com", False, False),
    ("hello-austin@radiantplumbing.com", False, True),
    ("katie@wayneslawnservice.com", False, True),
]

fails = 0
for email, allow, expect in cases:
    got = _is_valid_lead_email(email, allow_consumer=allow)
    status = "PASS" if got == expect else "FAIL"
    if got != expect:
        fails += 1
    print(f"{status} {email} allow_consumer={allow} got={got} expect={expect}")

print(f"\n{len(cases)-fails}/{len(cases)} PASS")
sys.exit(1 if fails else 0)
