@echo off
set KEYDIR=%USERPROFILE%\.ssh
for %%k in (agency-backend-key-v2.pem.fixed agency-ec2-key-fixed.pem deploy-key-20260520.pem.fixed ec2-deploy-key ec2-key.pem) do (
  echo ==== %%k ====
  ssh -o ConnectTimeout=8 -o BatchMode=yes -o StrictHostKeyChecking=no -i "%KEYDIR%\%%k" ubuntu@18.213.66.136 "echo CONNECTED_WITH_%%k"
  echo EXITCODE=%errorlevel%
)
