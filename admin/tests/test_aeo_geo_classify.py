from admin.agency import sba_biztypes as b

for ws, ind in [
    ("agency", ""),
    ("Houston Plumbing Co", "plumbing"),
    ("Bright Smile Dental", "dentist clinic"),
    ("Metro Law Group", "law firm"),
]:
    r = b.classify_business(ws, industry=ind)
    print("===", ws, "===")
    print("  category:", r["category"])
    print("  angle   :", r["angle"][:60])
    print("  AEO     :", r["aeo_angle"][:70])
    print("  GEO     :", r["geo_angle"][:70])
    print()
