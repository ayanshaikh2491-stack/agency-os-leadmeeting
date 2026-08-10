import subprocess

out = subprocess.run(["powershell", "-Command",
    "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' } | Select-Object ProcessId,CommandLine | Format-List"],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
print(out.stdout)
print(out.stderr[:1000])
