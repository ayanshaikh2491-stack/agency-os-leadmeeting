import sys
sys.path.insert(0, r"C:\Users\TAUSHEF\Downloads\int\deploy")
import pb_gateway as gw

# Test _record_out coercion
rec = {
    "id": "abc123def456ghi",
    "name": "Test Biz",
    "phone": 3464049915,
    "email": "test@example.com",
    "has_website": True,
    "status": "candidate",
    "website_status": 0,
    "legacy_id": 522,
    "raw": {"lead_score": 80},
}
out = gw._record_out(rec)
assert isinstance(out["phone"], str) and out["phone"] == "3464049915", out.get("phone")
assert isinstance(out["name"], str)
assert isinstance(out["email"], str)
assert isinstance(out["status"], str)
assert out["website_status"] == "0", out.get("website_status")
# bool stays readable
# bool fields stay bool (not coerced to str)
assert out["has_website"] is True, out.get("has_website")
# json/raw and legacy_id untouched (legacy_id not in _STRING_FIELDS)
assert out["legacy_id"] == 522
assert out["raw"] == {"lead_score": 80}
print("coercion OK:", out["phone"], out["name"], out["status"], out["has_website"])

# Test _field_type
assert gw._field_type("phone") == "text"
assert gw._field_type("name") == "text"
assert gw._field_type("has_website") == "bool"
assert gw._field_type("raw") == "json"
assert gw._field_type("unknown_col") == "json"
print("field types OK")
