import subprocess

r = subprocess.run(
    ["wmic", "process", "where", "name='aws.exe'", "get", "ProcessId,CreationDate,CommandLine", "/format:list"],
    capture_output=True, text=True)
print(r.stdout)
