# Analytics Agent — Skill Reference

## Role
Performance tracking specialist. Data-driven insights across all channels. Email reports to agency owner, CEO, and client.

## Interview Reference
- Q23: Weekly/monthly reporting
- Cross-workspace knowledge sharing (CRITICAL)

## Platforms
- **Data Sources**: GA4, Meta Ads Manager, Google Ads, Social APIs, SEO tools
- **Email**: SMTP (Gmail/custom) for report delivery

## 20 Real Tools

### Reporting (4)
1. `weekly_report` — Weekly performance summary across all channels
2. `monthly_report` — Comprehensive monthly with trends + recommendations
3. `campaign_report` — Detailed campaign performance breakdown
4. `custom_report` — CEO-requested custom analysis

### Tracking (4)
5. `track_traffic` — Website traffic metrics (visitors, bounce rate, sources)
6. `track_rankings` — Keyword rankings on search engines
7. `track_conversions` — Conversion metrics across channels
8. `track_revenue` — Revenue and profitability tracking

### Analysis (4)
9. `cross_channel_analysis` — Analyze all channels together
10. `roi_calculator` — Calculate ROI per channel
11. `funnel_analysis` — Conversion funnel performance
12. `competitor_benchmark` — Benchmark against competitors

### Alerts (3)
13. `anomaly_detector` — Detect metric anomalies
14. `threshold_alert` — Check thresholds and alert
15. `competitor_alert` — Alert on competitor activity

### Forecasting (3)
16. `traffic_forecast` — Forecast traffic growth
17. `budget_forecast` — Forecast budget needs
18. `growth_projection` — Project growth to targets

### Data (2)
19. `data_aggregator` — Aggregate all channel data
20. `email_report` — Send report via email

## Email Reports
Sends to:
- **Agency owner** (Taushef)
- **Workspace CEO**
- **Client**

Uses SMTP (Gmail or custom). Set in .env:
```
TAGS_SMTP_EMAIL=your-email@gmail.com
TAGS_SMTP_PASSWORD=your-app-password
```

## Workflow
1. Receive request from CEO or workspace context
2. Aggregate data from all channels
3. Generate insights and recommendations
4. Alert CEO on anomalies
5. Send email reports (weekly/monthly)
6. Generate scheduled reports

## Error Handling
- Data unavailable: Log gap, report to CEO, suggest alternative data source
- Anomaly detected: Classify severity, alert CEO, suggest investigation
- Report generation fails: Retry once, fallback to summary, notify CEO
- Email fails: Log error, provide report as text fallback

## Communication
- **Reports to**: CEO + Workspace CEO + Agency Owner (email)
- **Receives from**: All agents (SEO, Ads, Social, Website) provide performance data
- **Briefs**: CEO (insights, alerts, recommendations)

## Report Types
- Weekly Digest: All channels summary
- Monthly Deep Dive: Detailed analysis
- Campaign Report: Specific campaign performance
- SEO Report: Rankings, traffic, technical health
- Social Report: Engagement, growth
- Custom Report: CEO-requested

## API Routes (23)
- `GET /api/analytics/status` — Agent status
- `GET /api/analytics/tools` — List all 20 tools
- `POST /api/analytics/weekly-report` — Generate weekly report
- `POST /api/analytics/monthly-report` — Generate monthly report
- `POST /api/analytics/campaign-report` — Campaign report
- `POST /api/analytics/custom-report` — Custom report
- `POST /api/analytics/track-traffic` — Track traffic
- `POST /api/analytics/track-rankings` — Track rankings
- `POST /api/analytics/track-conversions` — Track conversions
- `POST /api/analytics/track-revenue` — Track revenue
- `POST /api/analytics/cross-channel` — Cross-channel analysis
- `POST /api/analytics/roi` — Calculate ROI
- `POST /api/analytics/funnel` — Funnel analysis
- `POST /api/analytics/competitor-benchmark` — Competitor benchmark
- `POST /api/analytics/anomaly` — Anomaly detection
- `POST /api/analytics/threshold` — Threshold alerts
- `POST /api/analytics/competitor-alert` — Competitor alerts
- `POST /api/analytics/traffic-forecast` — Traffic forecast
- `POST /api/analytics/budget-forecast` — Budget forecast
- `POST /api/analytics/growth-projection` — Growth projection
- `POST /api/analytics/aggregate` — Data aggregation
- `POST /api/analytics/email-report` — Send email report

## LangGraph
- Nodes: call_llm → run_tools → finalize
- Agent uses real tool registry from analytics_tools.py
- State: AnalyticsAgentState with tool_round tracking

## Interview Compliance
- Q23: Weekly/monthly reporting via tools ✓
- Cross-workspace knowledge sharing via data_aggregator ✓
