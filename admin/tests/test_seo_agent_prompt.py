from admin.workspace.agents.seo import build_seo_system_prompt

for ws in ["agency", "Houston Plumbing Co", "Bright Smile Dental"]:
    prompt = build_seo_system_prompt(ws, "Test Client", "how do I rank in ChatGPT for emergency plumber")
    print("=" * 30, ws, "=" * 30)
    # Show only the injected sections
    aeo_start = prompt.find("## Per-Business AEO")
    skill_start = prompt.find("## Relevant Skill Guidance")
    if aeo_start != -1:
        print(prompt[aeo_start:aeo_start + 350])
    if skill_start != -1:
        print("\n" + prompt[skill_start:skill_start + 300])
    print()
