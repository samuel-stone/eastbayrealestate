# Prospect Analytics: Query Command Center

This document tracks the SQL scripts used to derive actionable intelligence from the `leads.sqlite3` database.

## 1. Investor/Developer Identification
Use this to find leads with multiple high-value projects (e.g., ADUs, additions).
```sql
SELECT 
    l.address, 
    count(pi.id) as project_count 
FROM leads l
JOIN permit_insights pi ON l.id = pi.lead_id
WHERE pi.intent_category = 'Expansion' 
GROUP BY l.id 
HAVING project_count > 1 
ORDER BY project_count DESC;


2. Active Projects (Velocity Signal)
Identifies properties with multiple permits in the last 90 days.
SELECT 
    l.address, 
    count(pd.id) as recent_permits
FROM leads l
JOIN permit_details pd ON l.id = pd.lead_id
WHERE pd.date_processed > date('now', '-90 days')
GROUP BY l.id
HAVING recent_permits > 1
ORDER BY recent_permits DESC;

3. High-Intent Prospect List
Creates a consolidated list for outreach, filtering for major project types.
SQL
SELECT 
    l.address, 
    l.contact_name, 
    pi.intent_category,
    pi.description
FROM leads l
JOIN permit_insights pi ON l.id = pi.lead_id
WHERE pi.intent_category IN ('Expansion', 'Renovation');