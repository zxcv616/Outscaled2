# Enterprise Database Schema Design

## 🗄️ Database Architecture Overview

This document outlines the complete database schema design for the enterprise-scale League of Legends prediction system, including primary transactional databases, caching layers, analytical databases, and data lake structures.

---

## 📊 Multi-Database Strategy

### Database Distribution by Use Case

```yaml
Primary Transactional (PostgreSQL):
  - User management and authentication
  - Prediction tracking and feedback
  - System configuration
  - Real-time operational data

High-Performance Cache (Redis):
  - Session management
  - Prediction results caching
  - Feature store (hot data)
  - Rate limiting counters

Analytical Database (ClickHouse):
  - User behavior analytics
  - Prediction performance metrics
  - Business intelligence queries
  - Real-time dashboards

Time-Series Database (InfluxDB):
  - System metrics and monitoring
  - Performance tracking
  - Alert generation data
  - Capacity planning metrics

Data Lake (S3 + Iceberg):
  - Historical match data
  - Raw event streams
  - ML model artifacts
  - Long-term archival
```

---

## 🐘 PostgreSQL Primary Database Schema

### Core User Management

```sql
-- Users table with partitioning for scale
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(20) DEFAULT 'free' 
        CHECK (subscription_tier IN ('free', 'premium', 'pro', 'enterprise')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    
    -- Audit fields
    created_by UUID,
    updated_by UUID
) PARTITION BY RANGE (created_at);

-- Partitions for user table (monthly partitions)
CREATE TABLE users_2025_01 PARTITION OF users 
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE users_2025_02 PARTITION OF users 
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- User profiles with extended information
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(100),
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language_code VARCHAR(10) DEFAULT 'en',
    preferences JSONB DEFAULT '{}',
    riot_account_id VARCHAR(100),
    summoner_name VARCHAR(50),
    region VARCHAR(10),
    
    -- Privacy settings
    profile_visibility VARCHAR(20) DEFAULT 'public' 
        CHECK (profile_visibility IN ('public', 'friends', 'private')),
    data_sharing_consent BOOLEAN DEFAULT FALSE,
    marketing_consent BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User authentication methods
CREATE TABLE user_auth_methods (
    auth_method_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    auth_type VARCHAR(20) NOT NULL 
        CHECK (auth_type IN ('password', 'oauth_google', 'oauth_discord', 'oauth_riot')),
    provider_id VARCHAR(255), -- External provider user ID
    auth_data JSONB, -- Provider-specific data
    is_primary BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(user_id, auth_type)
);

-- User sessions for security tracking
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    location_data JSONB,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
) PARTITION BY RANGE (created_at);
```

### Prediction System Core

```sql
-- Prediction requests with comprehensive tracking
CREATE TABLE prediction_requests (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    
    -- Request parameters
    player_names TEXT[] NOT NULL,
    prop_type VARCHAR(20) NOT NULL CHECK (prop_type IN ('kills', 'assists')),
    prop_value DECIMAL(5,2) NOT NULL,
    map_range INTEGER[] NOT NULL,
    opponent VARCHAR(100),
    tournament VARCHAR(100),
    team VARCHAR(100),
    match_date DATE,
    position_roles TEXT[],
    strict_mode BOOLEAN DEFAULT FALSE,
    
    -- Results
    prediction VARCHAR(10) CHECK (prediction IN ('OVER', 'UNDER')),
    confidence DECIMAL(5,2),
    base_model_confidence DECIMAL(5,2),
    expected_stat DECIMAL(5,2),
    confidence_interval DECIMAL(5,2)[],
    data_tier INTEGER,
    
    -- Model and processing info
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    
    -- Request metadata
    client_ip INET,
    user_agent TEXT,
    api_version VARCHAR(10),
    request_source VARCHAR(50), -- 'web', 'mobile', 'api'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Partitioning for performance
    CONSTRAINT check_map_range CHECK (array_length(map_range, 1) = 2)
) PARTITION BY RANGE (created_at);

-- Monthly partitions for prediction requests
CREATE TABLE prediction_requests_2025_01 PARTITION OF prediction_requests 
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Prediction feedback for model training
CREATE TABLE prediction_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES prediction_requests(prediction_id),
    user_id UUID REFERENCES users(user_id),
    
    -- Actual outcomes
    actual_result VARCHAR(10) CHECK (actual_result IN ('OVER', 'UNDER')),
    actual_stat_value DECIMAL(5,2),
    match_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Feedback metadata
    feedback_source VARCHAR(20) DEFAULT 'manual' 
        CHECK (feedback_source IN ('manual', 'automated', 'verified')),
    confidence_score DECIMAL(3,2), -- User confidence in their feedback
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prediction curve data for visualization
CREATE TABLE prediction_curves (
    curve_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES prediction_requests(prediction_id),
    
    -- Curve data points
    prop_values DECIMAL(5,2)[] NOT NULL,
    predictions TEXT[] NOT NULL,
    confidences DECIMAL(5,2)[] NOT NULL,
    expected_stats DECIMAL(5,2)[] NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_curve_arrays_length CHECK (
        array_length(prop_values, 1) = array_length(predictions, 1) AND
        array_length(predictions, 1) = array_length(confidences, 1) AND
        array_length(confidences, 1) = array_length(expected_stats, 1)
    )
);
```

### ML Model Management

```sql
-- Model registry for version control
CREATE TABLE ml_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'prediction', 'feature', 'ensemble'
    
    -- Model metadata
    framework VARCHAR(50), -- 'sklearn', 'tensorflow', 'xgboost'
    algorithm VARCHAR(100),
    hyperparameters JSONB,
    feature_schema JSONB,
    
    -- Performance metrics
    training_accuracy DECIMAL(5,4),
    validation_accuracy DECIMAL(5,4),
    test_accuracy DECIMAL(5,4),
    training_metrics JSONB,
    
    -- Deployment info
    deployment_status VARCHAR(20) DEFAULT 'training' 
        CHECK (deployment_status IN ('training', 'testing', 'staging', 'production', 'deprecated')),
    deployment_percentage DECIMAL(5,2) DEFAULT 0, -- For A/B testing
    
    -- File references
    model_artifact_path TEXT,
    model_size_bytes BIGINT,
    checksum VARCHAR(64),
    
    -- Lifecycle
    trained_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(user_id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(model_name, model_version)
);

-- Feature definitions for the feature store
CREATE TABLE feature_definitions (
    feature_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_name VARCHAR(100) NOT NULL UNIQUE,
    feature_type VARCHAR(50) NOT NULL, -- 'numerical', 'categorical', 'text', 'vector'
    data_type VARCHAR(50) NOT NULL, -- 'float', 'int', 'string', 'array'
    
    -- Computation logic
    computation_logic TEXT, -- SQL or Python code
    dependencies TEXT[], -- Other features this depends on
    update_frequency VARCHAR(50), -- 'real-time', 'hourly', 'daily'
    
    -- Validation rules
    validation_rules JSONB, -- Min/max values, allowed categories, etc.
    data_quality_checks JSONB,
    
    -- Metadata
    description TEXT,
    business_context TEXT,
    created_by UUID REFERENCES users(user_id),
    
    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    deprecated_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model performance tracking
CREATE TABLE model_performance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(model_id),
    
    -- Performance data
    metric_date DATE NOT NULL,
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall SCORE DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_score DECIMAL(5,4),
    
    -- Prediction distribution
    total_predictions INTEGER,
    over_predictions INTEGER,
    under_predictions INTEGER,
    correct_predictions INTEGER,
    
    -- Data drift metrics
    feature_drift_score DECIMAL(5,4),
    target_drift_score DECIMAL(5,4),
    data_quality_score DECIMAL(5,4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(model_id, metric_date)
) PARTITION BY RANGE (metric_date);
```

### System Configuration & Operations

```sql
-- Application configuration
CREATE TABLE app_configurations (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    config_type VARCHAR(50) NOT NULL, -- 'feature_flag', 'setting', 'secret'
    
    -- Environment and deployment
    environment VARCHAR(20) NOT NULL DEFAULT 'production',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    description TEXT,
    last_modified_by UUID REFERENCES users(user_id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API rate limiting and usage tracking
CREATE TABLE api_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    api_key_id UUID, -- For API key usage
    
    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    
    -- Rate limiting
    rate_limit_key VARCHAR(255), -- User ID or API key
    requests_in_window INTEGER,
    window_start TIMESTAMP WITH TIME ZONE,
    
    -- Request metadata
    client_ip INET,
    user_agent TEXT,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Audit log for security and compliance
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    
    -- Action details
    action VARCHAR(100) NOT NULL, -- 'login', 'prediction_request', 'model_deploy'
    resource_type VARCHAR(50), -- 'user', 'prediction', 'model'
    resource_id UUID,
    
    -- Event details
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Results
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

### Indexes for Performance

```sql
-- User table indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);
CREATE INDEX CONCURRENTLY idx_users_username ON users (username);
CREATE INDEX CONCURRENTLY idx_users_active ON users (is_active, created_at);
CREATE INDEX CONCURRENTLY idx_users_subscription ON users (subscription_tier);

-- Prediction request indexes
CREATE INDEX CONCURRENTLY idx_predictions_user_date ON prediction_requests (user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_predictions_model_version ON prediction_requests (model_version, created_at);
CREATE INDEX CONCURRENTLY idx_predictions_performance ON prediction_requests (prediction, confidence, created_at);
CREATE INDEX CONCURRENTLY idx_predictions_parameters ON prediction_requests USING GIN (player_names);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY idx_predictions_lookup ON prediction_requests 
(user_id, prop_type, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '30 days';

-- Partial indexes for active data
CREATE INDEX CONCURRENTLY idx_active_sessions ON user_sessions (user_id, last_activity_at) 
WHERE is_active = TRUE;

-- GIN indexes for JSONB columns
CREATE INDEX CONCURRENTLY idx_user_metadata ON users USING GIN (metadata);
CREATE INDEX CONCURRENTLY idx_model_hyperparameters ON ml_models USING GIN (hyperparameters);
CREATE INDEX CONCURRENTLY idx_feature_validation ON feature_definitions USING GIN (validation_rules);
```

---

## 🔥 Redis Cache Schema Design

### Session Management

```redis
# User sessions (Hash)
# Key: session:{session_id}
# TTL: 30 minutes (sliding expiration)
HSET session:abc123 user_id "550e8400-e29b-41d4-a716-446655440000"
HSET session:abc123 created_at "2025-01-15T10:30:00Z"
HSET session:abc123 last_activity "2025-01-15T11:15:00Z"
HSET session:abc123 ip_address "192.168.1.100"
HSET session:abc123 device_fingerprint "fp_abc123"
EXPIRE session:abc123 1800

# User session index (Set)
# Key: user_sessions:{user_id}
SADD user_sessions:550e8400-e29b-41d4-a716-446655440000 "abc123"
EXPIRE user_sessions:550e8400-e29b-41d4-a716-446655440000 1800
```

### Prediction Results Cache

```redis
# Prediction cache (Hash)
# Key: prediction:{hash_of_parameters}
# TTL: 15 minutes
HSET prediction:sha256_abc123 result "OVER"
HSET prediction:sha256_abc123 confidence "78.5"
HSET prediction:sha256_abc123 expected_stat "4.2"
HSET prediction:sha256_abc123 model_version "v1.2.3"
HSET prediction:sha256_abc123 cached_at "2025-01-15T11:00:00Z"
EXPIRE prediction:sha256_abc123 900

# Prediction curve cache (String - JSON)
# Key: curve:{prediction_hash}
# TTL: 15 minutes
SET curve:sha256_abc123 '{"prop_values":[2.5,3.0,3.5,4.0,4.5],"predictions":["UNDER","UNDER","OVER","OVER","OVER"],"confidences":[85.2,72.1,68.9,75.3,81.7]}'
EXPIRE curve:sha256_abc123 900

# User prediction history (Sorted Set)
# Key: user_predictions:{user_id}
# Score: timestamp, Value: prediction_id
ZADD user_predictions:550e8400-e29b-41d4-a716-446655440000 1642248000 "pred_abc123"
EXPIRE user_predictions:550e8400-e29b-41d4-a716-446655440000 86400
```

### Feature Store (Hot Data)

```redis
# Player features (Hash)
# Key: features:player:{player_name}
# TTL: 1 hour
HSET features:player:faker avg_kills "5.2"
HSET features:player:faker avg_assists "7.8"
HSET features:player:faker form_z_score "0.85"
HSET features:player:faker position_factor "1.15"
HSET features:player:faker last_updated "2025-01-15T11:00:00Z"
EXPIRE features:player:faker 3600

# Team aggregated features (Hash)
# Key: features:team:{team_name}
HSET features:team:t1 avg_team_kills "15.8"
HSET features:team:t1 avg_game_duration "1847"
HSET features:team:t1 win_rate "0.75"
EXPIRE features:team:t1 3600

# Tournament context (Hash)
# Key: context:tournament:{tournament_name}
HSET context:tournament:lck patch_version "14.1"
HSET context:tournament:lck meta_champions '["azir","jinx","graves"]'
HSET context:tournament:lck avg_kills_per_game "25.3"
EXPIRE context:tournament:lck 7200
```

### Rate Limiting

```redis
# Token bucket rate limiting
# Key: rate_limit:{user_id}:{window}
# TTL: Window duration
SETEX rate_limit:550e8400:minute 60 "45"
SETEX rate_limit:550e8400:hour 3600 "450"
SETEX rate_limit:550e8400:day 86400 "5000"

# API key rate limiting
# Key: api_rate_limit:{api_key}:{window}
SETEX api_rate_limit:key_abc123:minute 60 "1000"
SETEX api_rate_limit:key_abc123:hour 3600 "50000"

# Global rate limiting (for DDoS protection)
# Key: global_rate_limit:{ip}:{window}
SETEX global_rate_limit:192.168.1.100:minute 60 "100"
```

---

## 📈 ClickHouse Analytical Database Schema

### User Behavior Analytics

```sql
-- User interaction events
CREATE TABLE user_events (
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UUID,
    session_id String,
    
    -- Event details
    event_type LowCardinality(String), -- 'page_view', 'prediction_request', 'user_action'
    event_category LowCardinality(String), -- 'navigation', 'prediction', 'account'
    event_action String,
    event_label Nullable(String),
    
    -- Page/context information
    page_url String,
    page_title Nullable(String),
    referrer Nullable(String),
    
    -- Device and browser info
    user_agent String,
    device_type LowCardinality(String), -- 'desktop', 'mobile', 'tablet'
    browser LowCardinality(String),
    operating_system LowCardinality(String),
    
    -- Geographic data
    ip_address IPv4,
    country LowCardinality(String),
    region Nullable(String),
    city Nullable(String),
    
    -- Custom dimensions
    custom_data Map(String, String),
    
    -- Timing
    event_time DateTime('UTC'),
    server_time DateTime('UTC') DEFAULT now()
) 
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (user_id, event_time, event_type)
SETTINGS index_granularity = 8192;

-- Prediction performance analytics
CREATE TABLE prediction_analytics (
    prediction_id UUID,
    user_id UUID,
    
    -- Prediction details
    model_version LowCardinality(String),
    prop_type LowCardinality(String),
    prop_value Decimal(5,2),
    prediction LowCardinality(String),
    confidence Decimal(5,2),
    
    -- Performance metrics
    response_time_ms UInt32,
    cache_hit UInt8, -- 0 or 1
    data_tier UInt8,
    
    -- Context
    tournament LowCardinality(String),
    player_names Array(String),
    team Nullable(String),
    
    -- Results (when available)
    actual_result Nullable(String),
    was_correct Nullable(UInt8),
    
    -- Timing
    created_at DateTime('UTC'),
    feedback_received_at Nullable(DateTime('UTC'))
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (user_id, created_at, model_version)
SETTINGS index_granularity = 8192;

-- Business metrics aggregation
CREATE TABLE daily_metrics (
    metric_date Date,
    
    -- User metrics
    total_users UInt32,
    active_users UInt32,
    new_users UInt32,
    returning_users UInt32,
    
    -- Prediction metrics
    total_predictions UInt32,
    successful_predictions UInt32,
    failed_predictions UInt32,
    avg_response_time Float32,
    
    -- Revenue metrics
    subscription_revenue Decimal(10,2),
    api_revenue Decimal(10,2),
    
    -- System metrics
    avg_cpu_usage Float32,
    avg_memory_usage Float32,
    total_requests UInt64,
    
    -- Geographic distribution
    top_countries Array(String),
    country_distribution Map(String, UInt32)
)
ENGINE = MergeTree()
ORDER BY metric_date
SETTINGS index_granularity = 8192;
```

### Materialized Views for Real-Time Analytics

```sql
-- Real-time user activity aggregation
CREATE MATERIALIZED VIEW user_activity_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_hour)
ORDER BY (user_id, event_hour, event_type)
AS SELECT
    user_id,
    toStartOfHour(event_time) as event_hour,
    event_type,
    count() as event_count,
    uniq(session_id) as unique_sessions
FROM user_events
GROUP BY user_id, event_hour, event_type;

-- Model performance real-time tracking
CREATE MATERIALIZED VIEW model_performance_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(prediction_hour)
ORDER BY (model_version, prediction_hour)
AS SELECT
    model_version,
    toStartOfHour(created_at) as prediction_hour,
    count() as total_predictions,
    avg(confidence) as avg_confidence,
    avg(response_time_ms) as avg_response_time,
    sum(cache_hit) as cache_hits,
    countIf(was_correct = 1) as correct_predictions,
    countIf(was_correct = 0) as incorrect_predictions
FROM prediction_analytics
WHERE actual_result IS NOT NULL
GROUP BY model_version, prediction_hour;
```

---

## ⏰ InfluxDB Time-Series Schema

### System Metrics

```influxdb
# CPU and Memory metrics
# Measurement: system_metrics
# Tags: service, pod_name, node
# Fields: cpu_usage, memory_usage, disk_usage
system_metrics,service=prediction-engine,pod=pred-engine-abc123,node=worker-1 cpu_usage=75.5,memory_usage=82.3,disk_usage=45.2 1642248000000000000

# API performance metrics
# Measurement: api_metrics
# Tags: endpoint, method, status_code, service
# Fields: response_time, request_size, response_size
api_metrics,endpoint=/predict,method=POST,status_code=200,service=api-gateway response_time=125.5,request_size=1024,response_size=2048 1642248000000000000

# Database performance
# Measurement: db_metrics
# Tags: database, operation, table
# Fields: query_time, rows_affected, connections_active
db_metrics,database=postgres,operation=select,table=prediction_requests query_time=45.2,rows_affected=1,connections_active=25 1642248000000000000

# Cache performance
# Measurement: cache_metrics
# Tags: cache_type, operation
# Fields: hit_rate, miss_rate, latency
cache_metrics,cache_type=redis,operation=get hit_rate=85.2,miss_rate=14.8,latency=1.2 1642248000000000000
```

### Business Metrics

```influxdb
# User engagement metrics
# Measurement: user_metrics
# Tags: subscription_tier, region, device_type
# Fields: session_duration, pages_per_session, predictions_per_session
user_metrics,subscription_tier=premium,region=na,device_type=desktop session_duration=1245.5,pages_per_session=8.2,predictions_per_session=3.1 1642248000000000000

# Revenue metrics
# Measurement: revenue_metrics
# Tags: subscription_tier, payment_method, region
# Fields: amount, conversion_rate
revenue_metrics,subscription_tier=premium,payment_method=stripe,region=eu amount=9.99,conversion_rate=12.5 1642248000000000000

# Prediction accuracy metrics
# Measurement: prediction_quality
# Tags: model_version, prop_type, tournament
# Fields: accuracy, precision, recall, f1_score
prediction_quality,model_version=v1.2.3,prop_type=kills,tournament=lck accuracy=87.5,precision=85.2,recall=89.1,f1_score=87.1 1642248000000000000
```

---

## 🏔️ Data Lake Schema (S3 + Iceberg)

### Directory Structure

```
s3://lol-prediction-datalake/
├── bronze/                          # Raw, unprocessed data
│   ├── riot_api/
│   │   ├── year=2025/month=01/day=15/hour=14/
│   │   │   ├── matches_001.parquet
│   │   │   ├── player_stats_001.parquet
│   │   │   └── live_events_001.parquet
│   │   └── _symlink_format_v1/
│   ├── external_apis/
│   │   └── opgg/year=2025/month=01/day=15/
│   └── user_events/
│       └── year=2025/month=01/day=15/hour=14/
├── silver/                          # Cleaned, validated data
│   ├── matches/
│   │   └── year=2025/month=01/day=15/
│   ├── player_statistics/
│   │   └── year=2025/month=01/day=15/
│   └── predictions/
│       └── year=2025/month=01/day=15/
├── gold/                           # Business-ready, aggregated data
│   ├── player_features/
│   ├── team_statistics/
│   ├── tournament_summaries/
│   └── model_training_datasets/
└── models/                         # ML model artifacts
    ├── prediction_models/
    │   └── v1.2.3/
    │       ├── model.pkl
    │       ├── feature_schema.json
    │       ├── metadata.json
    │       └── performance_metrics.json
    └── feature_definitions/
```

### Iceberg Table Schemas

```sql
-- Match results table
CREATE TABLE lol_datalake.match_results (
    match_id STRING,
    tournament STRING,
    date DATE,
    patch_version STRING,
    duration_seconds INT,
    
    -- Team information
    blue_team STRING,
    red_team STRING,
    winning_team STRING,
    
    -- Game statistics
    blue_kills INT,
    red_kills INT,
    blue_towers INT,
    red_towers INT,
    blue_dragons INT,
    red_dragons INT,
    blue_barons INT,
    red_barons INT,
    
    -- Metadata
    data_source STRING,
    ingested_at TIMESTAMP,
    processing_version STRING
)
USING iceberg
PARTITIONED BY (tournament, years(date))
TBLPROPERTIES (
    'write.parquet.compression-codec' = 'snappy',
    'write.target-file-size-bytes' = '536870912'
);

-- Player performance table
CREATE TABLE lol_datalake.player_performance (
    player_id STRING,
    match_id STRING,
    tournament STRING,
    date DATE,
    
    -- Player details
    player_name STRING,
    team STRING,
    position STRING,
    champion STRING,
    
    -- Core statistics
    kills INT,
    deaths INT,
    assists INT,
    cs INT,
    gold INT,
    damage_to_champions BIGINT,
    vision_score INT,
    
    -- Time-based statistics
    cs_at_10 INT,
    gold_at_10 INT,
    xp_at_10 INT,
    cs_at_15 INT,
    gold_diff_at_15 INT,
    xp_diff_at_15 INT,
    
    -- Advanced metrics
    kda DECIMAL(5,2),
    kill_participation DECIMAL(5,4),
    damage_per_minute DECIMAL(8,2),
    gold_per_minute DECIMAL(8,2),
    
    -- Metadata
    data_source STRING,
    ingested_at TIMESTAMP,
    processing_version STRING
)
USING iceberg
PARTITIONED BY (tournament, position, years(date))
TBLPROPERTIES (
    'write.parquet.compression-codec' = 'snappy',
    'write.target-file-size-bytes' = '268435456'
);

-- Feature store table
CREATE TABLE lol_datalake.player_features (
    player_id STRING,
    feature_date DATE,
    
    -- Historical aggregations
    avg_kills_30d DECIMAL(5,2),
    avg_assists_30d DECIMAL(5,2),
    avg_deaths_30d DECIMAL(5,2),
    std_kills_30d DECIMAL(5,2),
    std_assists_30d DECIMAL(5,2),
    
    -- Form metrics
    form_z_score DECIMAL(5,3),
    recent_performance_trend DECIMAL(5,3),
    volatility_index DECIMAL(5,3),
    
    -- Contextual features
    position_primary STRING,
    team_current STRING,
    tournaments_played ARRAY<STRING>,
    champions_played ARRAY<STRING>,
    
    -- Derived features
    kill_participation_avg DECIMAL(5,4),
    damage_share_avg DECIMAL(5,4),
    vision_score_avg DECIMAL(6,2),
    
    -- Metadata
    feature_version STRING,
    computed_at TIMESTAMP,
    data_quality_score DECIMAL(3,2)
)
USING iceberg
PARTITIONED BY (months(feature_date))
TBLPROPERTIES (
    'write.parquet.compression-codec' = 'snappy',
    'write.target-file-size-bytes' = '134217728'
);
```

---

## 🔄 Data Migration & ETL Patterns

### PostgreSQL to Data Lake ETL

```sql
-- Daily ETL job to move prediction data to data lake
WITH daily_predictions AS (
    SELECT 
        prediction_id,
        user_id,
        player_names,
        prop_type,
        prop_value,
        prediction,
        confidence,
        model_version,
        created_at::date as prediction_date,
        processing_time_ms,
        cache_hit
    FROM prediction_requests 
    WHERE created_at::date = CURRENT_DATE - 1
)
-- Export to S3 as Parquet files
COPY daily_predictions 
TO 's3://lol-prediction-datalake/silver/predictions/year={year}/month={month}/day={day}/'
WITH (FORMAT PARQUET, COMPRESSION 'snappy');
```

### Real-time Stream Processing (Kafka → Data Lake)

```python
# Kafka consumer for real-time data ingestion
from kafka import KafkaConsumer
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

def process_prediction_stream():
    consumer = KafkaConsumer(
        'prediction-events',
        bootstrap_servers=['kafka-cluster:9092'],
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    batch_size = 1000
    batch_data = []
    
    for message in consumer:
        event_data = message.value
        
        # Transform to data lake schema
        transformed_data = {
            'prediction_id': event_data['prediction_id'],
            'user_id': event_data['user_id'],
            'player_names': event_data['player_names'],
            'prop_type': event_data['prop_type'],
            'prediction': event_data['prediction'],
            'confidence': event_data['confidence'],
            'model_version': event_data['model_version'],
            'created_at': datetime.fromisoformat(event_data['created_at']),
            'processing_metadata': {
                'kafka_offset': message.offset,
                'kafka_partition': message.partition,
                'processed_at': datetime.utcnow()
            }
        }
        
        batch_data.append(transformed_data)
        
        if len(batch_data) >= batch_size:
            write_batch_to_s3(batch_data)
            batch_data = []

def write_batch_to_s3(batch_data):
    """Write batch data to S3 in Parquet format"""
    df = pd.DataFrame(batch_data)
    
    # Partition by date
    partition_date = df['created_at'].dt.date.iloc[0]
    s3_path = f"s3://lol-prediction-datalake/bronze/predictions/year={partition_date.year}/month={partition_date.month:02d}/day={partition_date.day:02d}/"
    
    # Write as Parquet with Snappy compression
    table = pa.Table.from_pandas(df)
    pq.write_table(table, s3_path, compression='snappy')
```

---

## 📊 Performance Optimization Strategies

### Database Partitioning Strategy

```sql
-- Automatic partition creation for prediction_requests
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    -- Create partitions for the next 12 months
    FOR i IN 0..11 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + interval '1 month';
        partition_name := 'prediction_requests_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF prediction_requests 
                       FOR VALUES FROM (%L) TO (%L)', 
                       partition_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule automatic partition creation
SELECT cron.schedule('create-partitions', '0 0 1 * *', 'SELECT create_monthly_partitions();');
```

### Connection Pooling Configuration

```yaml
# PgBouncer configuration for connection pooling
[databases]
lol_prediction = host=postgres-primary port=5432 dbname=lol_prediction

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
max_db_connections = 100
max_user_connections = 50

# Connection lifetime management
server_lifetime = 3600
server_idle_timeout = 600
client_idle_timeout = 0

# Authentication
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

### Read Replica Configuration

```sql
-- Read replica routing for analytical queries
-- Primary database: Write operations
-- Read replicas: Read operations with eventual consistency

-- Example query routing in application code
@read_replica
def get_user_prediction_history(user_id: UUID, limit: int = 50):
    return db.query("""
        SELECT prediction_id, player_names, prediction, confidence, created_at
        FROM prediction_requests 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (user_id, limit))

@primary_db
def create_prediction_request(prediction_data: dict):
    return db.execute("""
        INSERT INTO prediction_requests (user_id, player_names, prop_type, ...) 
        VALUES (%(user_id)s, %(player_names)s, %(prop_type)s, ...)
        RETURNING prediction_id
    """, prediction_data)
```

This comprehensive database schema design provides the foundation for an enterprise-scale League of Legends prediction system, with proper partitioning, indexing, caching strategies, and performance optimizations to handle millions of users and predictions efficiently.