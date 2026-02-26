-- Optimized device list query with tag filtering
-- Replaces the N+1 pattern introduced in v2.8
-- Expected: p95 latency back to ~120ms for 100K+ device datasets

SELECT 
    d.id,
    d.name,
    d.status,
    d.last_seen_at,
    d.tenant_id,
    array_agg(DISTINCT dt.tag_name) FILTER (WHERE dt.tag_name IS NOT NULL) AS tags
FROM devices d
LEFT JOIN device_tags dt ON dt.device_id = d.id
WHERE d.tenant_id = :tenant_id
    AND (:status IS NULL OR d.status = :status)
    AND (:tag_filter IS NULL OR dt.tag_name = ANY(:tag_filter))
GROUP BY d.id, d.name, d.status, d.last_seen_at, d.tenant_id
ORDER BY d.last_seen_at DESC
LIMIT :limit OFFSET :offset;

-- Supporting index (add via migration)
-- CREATE INDEX CONCURRENTLY idx_device_tags_device_tag 
--   ON device_tags(device_id, tag_name);
