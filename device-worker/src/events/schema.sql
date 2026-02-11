-- Event Store Schema
-- Append-only event log for device state management
-- Partitioned by tenant_id for query isolation

CREATE TABLE IF NOT EXISTS events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id       VARCHAR(255) NOT NULL,       -- e.g., "device:<device_id>"
    tenant_id       VARCHAR(100) NOT NULL,
    event_type      VARCHAR(255) NOT NULL,        -- e.g., "DeviceRegistered", "PolicyApplied"
    event_version   INTEGER NOT NULL,             -- schema version for this event type  
    stream_version  BIGINT NOT NULL,              -- optimistic concurrency control
    payload         JSONB NOT NULL,
    metadata        JSONB DEFAULT '{}',
    correlation_id  UUID,                         -- links related events across services
    causation_id    UUID,                         -- the event that caused this event
    actor_id        VARCHAR(255),                 -- who/what triggered this event
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY HASH (tenant_id);

-- Create partitions (start with 8, scale as needed)
CREATE TABLE events_p0 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE events_p1 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE events_p2 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE events_p3 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE events_p4 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE events_p5 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE events_p6 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE events_p7 PARTITION OF events FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- Unique constraint for optimistic concurrency
CREATE UNIQUE INDEX idx_events_stream_version 
    ON events (stream_id, stream_version);

-- Query by stream (get all events for a device)
CREATE INDEX idx_events_stream_id 
    ON events (stream_id, stream_version ASC);

-- Query by type (rebuild projections)
CREATE INDEX idx_events_type_created 
    ON events (event_type, created_at ASC);

-- Correlation tracking
CREATE INDEX idx_events_correlation 
    ON events (correlation_id) WHERE correlation_id IS NOT NULL;

-- Snapshots for performance (avoid replaying full history)
CREATE TABLE IF NOT EXISTS snapshots (
    stream_id       VARCHAR(255) NOT NULL,
    tenant_id       VARCHAR(100) NOT NULL,
    stream_version  BIGINT NOT NULL,
    state           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (stream_id, stream_version)
);

CREATE INDEX idx_snapshots_latest 
    ON snapshots (stream_id, stream_version DESC);

