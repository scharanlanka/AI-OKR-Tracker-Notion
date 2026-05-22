-- Optional manual schema setup if you want to run via psql.
-- Example:
-- psql "postgresql://postgres:postgres@localhost:5432/okr_tracker" -f scripts/init_schema.sql

CREATE TABLE IF NOT EXISTS objectives (
  id SERIAL PRIMARY KEY,
  notion_id VARCHAR(100) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  owner VARCHAR(255),
  status VARCHAR(100),
  progress DOUBLE PRECISION DEFAULT 0.0,
  target_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS key_results (
  id SERIAL PRIMARY KEY,
  notion_id VARCHAR(100) NOT NULL UNIQUE,
  objective_id INTEGER NOT NULL REFERENCES objectives(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  owner VARCHAR(255),
  status VARCHAR(100),
  progress DOUBLE PRECISION DEFAULT 0.0,
  deadline DATE,
  is_blocked BOOLEAN DEFAULT FALSE,
  blocker_notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_logs (
  id SERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  routed_agent VARCHAR(100) NOT NULL,
  response TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_objectives_notion_id ON objectives(notion_id);
CREATE INDEX IF NOT EXISTS idx_key_results_notion_id ON key_results(notion_id);
CREATE INDEX IF NOT EXISTS idx_key_results_objective_id ON key_results(objective_id);
