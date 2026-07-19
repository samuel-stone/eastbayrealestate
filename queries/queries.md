# Prospect Analytics: Query Command Center

This document tracks the SQL scripts used to derive actionable intelligence from the `leads.sqlite3` database.

## 1. Investor/Developer Identification
Use this to find leads with multiple high-value projects (e.g., ADUs, additions).
```sql
SELECT 
    l.address, 
    COUNT(w.permit_no) AS project_count 
FROM leads l
JOIN walnut_creek_permits w ON l.normalized_address = w.clean_addr
WHERE w.description ILIKE '%ADU%' OR w.description ILIKE '%addition%'
GROUP BY l.id, l.address 
HAVING COUNT(w.permit_no) > 1 
ORDER BY project_count DESC;

2. Active Projects (Velocity Signal)
Identifies properties with multiple permits in the last 90 days.

SELECT 
    l.address, 
    COUNT(pd.permit_number) AS recent_permits
FROM leads l
JOIN permit_details pd ON l.id = pd.lead_id
WHERE pd.issued_date > CURRENT_DATE - INTERVAL '90 days'
GROUP BY l.id, l.address
HAVING COUNT(pd.permit_number) > 1
ORDER BY recent_permits DESC;


3. High-Intent Prospect List
Creates a consolidated list for outreach, filtering for major project types.
SELECT 
    l.address, 
    l.contact_name, 
    w.description AS project_type,
    w.status
FROM leads l
JOIN walnut_creek_permits w ON l.normalized_address = w.clean_addr
WHERE w.description ILIKE '%Expansion%' OR w.description ILIKE '%Renovation%'
AND w.status IS NOT NULL;


4. Weekly Prospect Report
SELECT * FROM v_prospect_intelligence 
WHERE issued_date > CURRENT_DATE - INTERVAL '7 days';