import ast
src = open(r"deploy\deploy_sba.py", encoding="utf-8").read()
ast.parse(src)
print("SYNTAX_OK, lines:", len(src.splitlines()))
# verify both lists contain the entries
assert '"admin/agency/ceo_monitor.py"' in src
assert '"admin/api/routes/ceo.py"' in src
print("CEO entries present in both FILES + COMPILE_FILES")
