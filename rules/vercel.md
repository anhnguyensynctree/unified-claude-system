# Vercel Rules — Always Follow

## Canonical URLs
Always use the canonical production alias when reporting a Vercel deployment to the user or in any brief. Never output the deployment-specific hash URL (e.g. `project-abc123-org.vercel.app`).

To find the canonical alias:
```bash
VERCEL_TOKEN=$(cat ~/.config/vercel/key)
curl -s "https://api.vercel.com/v9/projects/<projectId>?teamId=<teamId>" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['targets']['production']['alias'][0])"
```

The canonical alias is `targets.production.alias[0]` — the first entry, which is the stable `<name>.vercel.app` domain.

## Environment Variables
- Set via Vercel dashboard (Production + Preview) — never committed to the repo
- App secrets (API keys, thresholds) belong in Vercel env vars, not GitHub Actions secrets
- GitHub Actions secrets: only deployment credentials (`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`)

## Deploy Pattern
- Production: push to master → CI passes → `vercel --prod --token $VERCEL_TOKEN`
- Preview: PR opened/updated → CI passes → `vercel --token $VERCEL_TOKEN` → URL posted as PR comment
- No GitHub App required — CLI handles everything

## Key Locations
- Vercel API token: `~/.config/vercel/key` (chmod 600)
- Project IDs: `.vercel/project.json` (`projectId`, `orgId`)
