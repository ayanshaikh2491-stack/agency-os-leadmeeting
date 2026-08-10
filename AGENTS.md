# AGENTS.md

## Test commands
npm test
npm run lint

## Loop conventions
- Report-only week one (L1) before enabling auto-fix (L2)
- See LOOP.md for cadence and human gates
  
## AWS Guidance  
  
- Prefer the AWS MCP Server for AWS interactions (sandboxed execution, observability, audit logging). If unavailable, use the AWS CLI directly.  
- Before starting a task, check whether a relevant AWS skill is available. Load the skill and prefer its guidance over general knowledge.  
- When uncertain about specific AWS details, verify against documentation rather than guessing. State uncertainty explicitly if you cannot confirm.  
- When creating infrastructure, prefer infrastructure-as-code (AWS CDK or CloudFormation) over direct CLI commands.  
- When working with infrastructure, follow AWS Well-Architected Framework principles.  
- Do not use em dashes in AWS resource names or descriptions. Use hyphens instead.  
  
## Secret Safety  
- MUST load the aws-secrets-manager skill first for any secret, credential, API key, token, or password task. MUST NOT call secretsmanager get-secret-value or batch-get-secret-value directly. Use resolve:secretsmanager:secret-id:SecretString:json-key with asm-exec so the secret resolves at runtime without entering context.  
