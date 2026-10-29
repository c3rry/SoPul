-- Pulse2026 PostgreSQL 16 Initial Schema DDL

CREATE TABLE IF NOT EXISTS races (
    race_id VARCHAR(32) PRIMARY KEY,
    state VARCHAR(2) NOT NULL,
    chamber VARCHAR(16) NOT NULL,
    district VARCHAR(8),
    historical_lean FLOAT NOT NULL DEFAULT 0.0,
    kalshi_market_ticker VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id VARCHAR(64) PRIMARY KEY,
    race_id VARCHAR(32) NOT NULL REFERENCES races(race_id) ON DELETE CASCADE,
    full_name VARCHAR(128) NOT NULL,
    party VARCHAR(16) NOT NULL,
    incumbent BOOLEAN NOT NULL DEFAULT FALSE,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    official_handles TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_posts (
    post_id VARCHAR(128) PRIMARY KEY,
    platform VARCHAR(32) NOT NULL,
    author_handle_hash VARCHAR(64) NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    caption TEXT,
    transcript TEXT,
    raw_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_post_mentions (
    post_id VARCHAR(128) NOT NULL REFERENCES social_posts(post_id) ON DELETE CASCADE,
    candidate_id VARCHAR(64) NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
    race_id VARCHAR(32) NOT NULL REFERENCES races(race_id) ON DELETE CASCADE,
    ideology_score FLOAT,
    stance_score FLOAT,
    comment_ratio_penalty FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS polls (
    poll_id VARCHAR(128) PRIMARY KEY,
    race_id VARCHAR(32) NOT NULL REFERENCES races(race_id) ON DELETE CASCADE,
    pollster VARCHAR(128) NOT NULL,
    pollster_rating FLOAT NOT NULL DEFAULT 1.0,
    start_date DATE,
    end_date DATE NOT NULL,
    sample_size INT NOT NULL,
    population_type VARCHAR(8) NOT NULL DEFAULT 'LV',
    dem_pct FLOAT NOT NULL,
    rep_pct FLOAT NOT NULL,
    undecided_pct FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement_snapshots (
    post_id VARCHAR(128) NOT NULL REFERENCES social_posts(post_id) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    views INT NOT NULL DEFAULT 0,
    likes INT NOT NULL DEFAULT 0,
    comments INT NOT NULL DEFAULT 0,
    shares INT NOT NULL DEFAULT 0,
    ewss_score FLOAT NOT NULL DEFAULT 0.0,
    PRIMARY KEY (post_id, observed_at)
);

CREATE TABLE IF NOT EXISTS kalshi_ticks (
    ticker VARCHAR(64) NOT NULL,
    tick_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    yes_bid INT NOT NULL DEFAULT 0,
    yes_ask INT NOT NULL DEFAULT 0,
    last_price INT NOT NULL DEFAULT 0,
    volume_24h INT NOT NULL DEFAULT 0,
    open_interest INT NOT NULL DEFAULT 0,
    vwap_24h FLOAT NOT NULL DEFAULT 0.0,
    liquidity_weight FLOAT NOT NULL DEFAULT 0.0,
    PRIMARY KEY (ticker, tick_time)
);

CREATE TABLE IF NOT EXISTS race_forecasts (
    race_id VARCHAR(32) NOT NULL REFERENCES races(race_id) ON DELETE CASCADE,
    forecast_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dem_win_prob FLOAT NOT NULL,
    rep_win_prob FLOAT NOT NULL,
    predicted_dem_margin FLOAT NOT NULL,
    ci_lower_90 FLOAT NOT NULL,
    ci_upper_90 FLOAT NOT NULL,
    poll_component_margin FLOAT NOT NULL,
    kalshi_component_margin FLOAT NOT NULL,
    social_component_shift FLOAT NOT NULL DEFAULT 0.0,
    shap_attributions JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (race_id, forecast_time)
);

-- Compound B-tree Indices
CREATE INDEX IF NOT EXISTS idx_social_posts_platform_published ON social_posts(platform, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentions_race ON social_post_mentions(race_id);
CREATE INDEX IF NOT EXISTS idx_mentions_candidate ON social_post_mentions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_polls_race_end_date ON polls(race_id, end_date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_post_observed ON engagement_snapshots(post_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_kalshi_ticks_ticker_time ON kalshi_ticks(ticker, tick_time DESC);
CREATE INDEX IF NOT EXISTS idx_forecasts_race_time ON race_forecasts(race_id, forecast_time DESC);
