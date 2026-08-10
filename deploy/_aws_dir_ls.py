import os
home = os.path.expanduser("~")
print("HOME", home)
aws_dir = os.path.join(home, ".aws")
if os.path.isdir(aws_dir):
    for name in sorted(os.listdir(aws_dir)):
        p = os.path.join(aws_dir, name)
        print(" ", name, "(dir)" if os.path.isdir(p) else os.path.getsize(p))
        if os.path.isdir(p):
            try:
                for sub in sorted(os.listdir(p)):
                    print("    ", sub)
            except OSError as e:
                print("    err", e)
else:
    print("NO .aws dir")
