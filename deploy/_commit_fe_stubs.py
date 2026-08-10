"""Commit frontend stub-agent removal changes."""
import subprocess, sys

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout.strip()[:2000])
    if r.stderr:
        print("ERR:", r.stderr.strip()[:500])
    return r.returncode

# Stage only our changes
sh('git add src/app/admin/agents/page.js src/app/admin/ceo/page.js src/app/admin/cto/page.js')
sh('git add src/components/OrgChart.jsx src/components/agents/AgentList.jsx src/components/ceo/CEODecisionLog.jsx')
sh('git add src/lib/chat-utils.js src/lib/client-context.js supabase/schema.sql')
sh('git add -A src/app/api/agents/')
sh('git commit --file=- <<MSG
chore(agents): remove stub agents (intake-researcher, sales-closer, client-success, review-qc)

These 4 agents were registry-only names aliased to SBA with no real
implementation. Removed from all frontend lists, proxy routes, and seeds.
Lead/sales routing now goes directly to the real SBA agent.
MSG')
sh('git log --oneline -1')
