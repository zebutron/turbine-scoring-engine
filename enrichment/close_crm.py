"""
Close CRM enrichment: Funnel status, meetings, engagement -> update warmth signals.

Pulls deal progression data from Close CRM API to refresh Demand pillar data.
Priority columns: Close Status, Close Status Change Dt.
Also updates warmth scores for people who've had recent CRM interactions.

Status: STUB — Close CRM accessible via Slack MCP (AppTurbine workspace).
"""
