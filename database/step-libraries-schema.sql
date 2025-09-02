-- Step Libraries Database Schema
-- Modular step library management system for OpsConductor

-- STEP LIBRARIES TABLE
-- Stores metadata and information about installed step libraries
CREATE TABLE IF NOT EXISTS step_libraries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,                    -- Library identifier (e.g., 'file-operations')
    version VARCHAR(20) NOT NULL,                  -- Semantic version (e.g., '1.2.3')
    display_name VARCHAR(200) NOT NULL,            -- Human-readable name
    description TEXT,                              -- Library description
    author VARCHAR(100) NOT NULL,                  -- Library author
    author_email VARCHAR(255),                     -- Author contact email
    homepage TEXT,                                 -- Library homepage URL
    repository TEXT,                               -- Source repository URL
    license VARCHAR(50) DEFAULT 'MIT',             -- License type
    categories TEXT[] DEFAULT '{}',                -- Library categories
    tags TEXT[] DEFAULT '{}',                      -- Search tags
    dependencies TEXT[] DEFAULT '{}',              -- Required dependencies
    min_opsconductor_version VARCHAR(20) DEFAULT '1.0.0', -- Minimum OpsConductor version
    
    -- Premium/Commercial Support
    is_premium BOOLEAN DEFAULT false,              -- Whether library requires premium license
    price DECIMAL(10,2),                          -- Library price (if premium)
    trial_days INTEGER,                           -- Trial period in days
    license_key_hash VARCHAR(255),                -- Hashed license key for validation
    
    -- Installation & Status
    file_path TEXT NOT NULL,                      -- Path to library files
    file_hash VARCHAR(64) NOT NULL,               -- SHA-256 hash of library file
    file_size BIGINT,                            -- File size in bytes
    is_enabled BOOLEAN DEFAULT true,              -- Whether library is active
    installation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ,                     -- Last update timestamp
    last_used TIMESTAMPTZ,                       -- Last time library was used
    usage_count INTEGER DEFAULT 0,               -- Number of times library steps were executed
    
    -- Status and Health
    status VARCHAR(20) DEFAULT 'installed' CHECK (status IN ('installed', 'enabled', 'disabled', 'error', 'updating', 'deprecated')),
    error_message TEXT,                          -- Error details if status is 'error'
    health_check_date TIMESTAMPTZ,              -- Last health check
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(name, version),                       -- Prevent duplicate library versions
    CHECK (version ~ '^[0-9]+\.[0-9]+\.[0-9]+'), -- Semantic versioning validation
    CHECK (is_premium = false OR (is_premium = true AND price > 0)) -- Premium libraries must have price
);

-- LIBRARY STEPS TABLE
-- Stores individual step definitions within libraries
CREATE TABLE IF NOT EXISTS library_steps (
    id SERIAL PRIMARY KEY,
    library_id INTEGER NOT NULL REFERENCES step_libraries(id) ON DELETE CASCADE,
    
    -- Step Identity
    name VARCHAR(100) NOT NULL,                   -- Step identifier (e.g., 'file.create')
    display_name VARCHAR(200) NOT NULL,           -- Human-readable step name
    category VARCHAR(50) NOT NULL,                -- Step category (file, network, logic, etc.)
    description TEXT,                             -- Step description
    
    -- Visual Properties
    icon VARCHAR(10) DEFAULT '📄',                -- Step icon (emoji or icon class)
    color VARCHAR(7) DEFAULT '#007bff',           -- Step color (hex)
    
    -- Flow Properties
    inputs INTEGER DEFAULT 1,                     -- Number of input ports
    outputs INTEGER DEFAULT 1,                    -- Number of output ports
    
    -- Configuration
    parameters JSONB DEFAULT '{}',                -- Step parameters schema
    platform_support TEXT[] DEFAULT ARRAY['windows', 'linux', 'macos'], -- Supported platforms
    required_permissions TEXT[] DEFAULT '{}',     -- Required permissions
    examples JSONB DEFAULT '[]',                  -- Usage examples
    tags TEXT[] DEFAULT '{}',                     -- Search tags
    
    -- Performance & Usage
    execution_count INTEGER DEFAULT 0,            -- Number of times step was executed
    avg_execution_time_ms INTEGER,               -- Average execution time
    last_executed TIMESTAMPTZ,                   -- Last execution timestamp
    
    -- Status
    is_deprecated BOOLEAN DEFAULT false,          -- Whether step is deprecated
    deprecation_message TEXT,                    -- Deprecation notice
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(library_id, name),                    -- Prevent duplicate steps within library
    CHECK (inputs >= 0 AND inputs <= 10),       -- Reasonable input port limits
    CHECK (outputs >= 0 AND outputs <= 10),     -- Reasonable output port limits
    CHECK (color ~ '^#[0-9A-Fa-f]{6}$')        -- Valid hex color
);

-- LIBRARY DEPENDENCIES TABLE
-- Manages dependencies between libraries
CREATE TABLE IF NOT EXISTS library_dependencies (
    id SERIAL PRIMARY KEY,
    library_id INTEGER NOT NULL REFERENCES step_libraries(id) ON DELETE CASCADE,
    dependency_name VARCHAR(100) NOT NULL,       -- Name of required library
    dependency_version VARCHAR(20),              -- Required version (or version range)
    is_optional BOOLEAN DEFAULT false,           -- Whether dependency is optional
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(library_id, dependency_name)
);

-- LIBRARY USAGE ANALYTICS TABLE
-- Tracks library and step usage for analytics and optimization
CREATE TABLE IF NOT EXISTS library_usage_analytics (
    id SERIAL PRIMARY KEY,
    library_id INTEGER REFERENCES step_libraries(id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES library_steps(id) ON DELETE CASCADE,
    
    -- Usage Context
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    job_run_id BIGINT REFERENCES job_runs(id) ON DELETE SET NULL,
    
    -- Execution Details
    execution_time_ms INTEGER,                   -- Execution time in milliseconds
    memory_usage_mb INTEGER,                     -- Memory usage in MB
    success BOOLEAN,                             -- Whether execution was successful
    error_message TEXT,                          -- Error details if failed
    
    -- Metadata
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    platform VARCHAR(20),                        -- Execution platform
    opsconductor_version VARCHAR(20),            -- OpsConductor version
    
    -- Indexes will be created below for performance
    CHECK (execution_time_ms >= 0),
    CHECK (memory_usage_mb >= 0)
);

-- LIBRARY LICENSES TABLE
-- Manages premium library licenses and validation
CREATE TABLE IF NOT EXISTS library_licenses (
    id SERIAL PRIMARY KEY,
    library_id INTEGER NOT NULL REFERENCES step_libraries(id) ON DELETE CASCADE,
    
    -- License Details
    license_key VARCHAR(255) NOT NULL UNIQUE,    -- License key
    license_key_hash VARCHAR(255) NOT NULL,      -- Hashed license key
    license_type VARCHAR(50) DEFAULT 'premium',  -- License type
    
    -- Validity
    issued_to_email VARCHAR(255),                -- Licensed user email
    issued_to_organization VARCHAR(255),         -- Licensed organization
    issued_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_date TIMESTAMPTZ,                    -- License expiration
    is_active BOOLEAN DEFAULT true,              -- Whether license is active
    
    -- Usage Limits
    max_installations INTEGER,                   -- Maximum installations allowed
    current_installations INTEGER DEFAULT 0,     -- Current active installations
    max_executions_per_month INTEGER,           -- Monthly execution limit
    current_month_executions INTEGER DEFAULT 0, -- Current month usage
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (expires_date IS NULL OR expires_date > issued_date),
    CHECK (max_installations IS NULL OR max_installations > 0),
    CHECK (current_installations >= 0),
    CHECK (max_executions_per_month IS NULL OR max_executions_per_month > 0),
    CHECK (current_month_executions >= 0)
);

-- LIBRARY MARKETPLACE TABLE
-- Stores information about available libraries in marketplace
CREATE TABLE IF NOT EXISTS library_marketplace (
    id SERIAL PRIMARY KEY,
    
    -- Library Identity
    name VARCHAR(100) NOT NULL,
    latest_version VARCHAR(20) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    author VARCHAR(100) NOT NULL,
    
    -- Marketplace Info
    download_url TEXT NOT NULL,                  -- Download URL
    documentation_url TEXT,                      -- Documentation URL
    demo_url TEXT,                              -- Demo/preview URL
    screenshots JSONB DEFAULT '[]',             -- Screenshot URLs
    
    -- Ratings & Reviews
    rating DECIMAL(3,2) DEFAULT 0.0,           -- Average rating (0.0-5.0)
    review_count INTEGER DEFAULT 0,             -- Number of reviews
    download_count INTEGER DEFAULT 0,           -- Number of downloads
    
    -- Categories & Tags
    categories TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    
    -- Pricing
    is_free BOOLEAN DEFAULT true,
    price DECIMAL(10,2),
    has_trial BOOLEAN DEFAULT false,
    trial_days INTEGER,
    
    -- Status
    is_featured BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,          -- Verified by OpsConductor team
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'removed')),
    
    -- Metadata
    published_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(name),
    CHECK (rating >= 0.0 AND rating <= 5.0),
    CHECK (review_count >= 0),
    CHECK (download_count >= 0),
    CHECK (is_free = true OR (is_free = false AND price > 0))
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Step Libraries Indexes
CREATE INDEX IF NOT EXISTS idx_step_libraries_name ON step_libraries(name);
CREATE INDEX IF NOT EXISTS idx_step_libraries_enabled ON step_libraries(is_enabled);
CREATE INDEX IF NOT EXISTS idx_step_libraries_premium ON step_libraries(is_premium);
CREATE INDEX IF NOT EXISTS idx_step_libraries_status ON step_libraries(status);
CREATE INDEX IF NOT EXISTS idx_step_libraries_categories_gin ON step_libraries USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_step_libraries_tags_gin ON step_libraries USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_step_libraries_installation_date ON step_libraries(installation_date);
CREATE INDEX IF NOT EXISTS idx_step_libraries_last_used ON step_libraries(last_used);

-- Library Steps Indexes
CREATE INDEX IF NOT EXISTS idx_library_steps_library_id ON library_steps(library_id);
CREATE INDEX IF NOT EXISTS idx_library_steps_category ON library_steps(category);
CREATE INDEX IF NOT EXISTS idx_library_steps_name ON library_steps(name);
CREATE INDEX IF NOT EXISTS idx_library_steps_platform_gin ON library_steps USING GIN(platform_support);
CREATE INDEX IF NOT EXISTS idx_library_steps_tags_gin ON library_steps USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_library_steps_deprecated ON library_steps(is_deprecated);

-- Library Dependencies Indexes
CREATE INDEX IF NOT EXISTS idx_library_dependencies_library_id ON library_dependencies(library_id);
CREATE INDEX IF NOT EXISTS idx_library_dependencies_name ON library_dependencies(dependency_name);

-- Usage Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_usage_analytics_library_id ON library_usage_analytics(library_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_step_id ON library_usage_analytics(step_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_executed_at ON library_usage_analytics(executed_at);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON library_usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_success ON library_usage_analytics(success);

-- Library Licenses Indexes
CREATE INDEX IF NOT EXISTS idx_library_licenses_library_id ON library_licenses(library_id);
CREATE INDEX IF NOT EXISTS idx_library_licenses_active ON library_licenses(is_active);
CREATE INDEX IF NOT EXISTS idx_library_licenses_expires ON library_licenses(expires_date);
CREATE INDEX IF NOT EXISTS idx_library_licenses_email ON library_licenses(issued_to_email);

-- Marketplace Indexes
CREATE INDEX IF NOT EXISTS idx_marketplace_name ON library_marketplace(name);
CREATE INDEX IF NOT EXISTS idx_marketplace_featured ON library_marketplace(is_featured);
CREATE INDEX IF NOT EXISTS idx_marketplace_verified ON library_marketplace(is_verified);
CREATE INDEX IF NOT EXISTS idx_marketplace_free ON library_marketplace(is_free);
CREATE INDEX IF NOT EXISTS idx_marketplace_rating ON library_marketplace(rating);
CREATE INDEX IF NOT EXISTS idx_marketplace_categories_gin ON library_marketplace USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_marketplace_tags_gin ON library_marketplace USING GIN(tags);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_step_libraries_updated_at 
    BEFORE UPDATE ON step_libraries 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_library_steps_updated_at 
    BEFORE UPDATE ON library_steps 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_library_licenses_updated_at 
    BEFORE UPDATE ON library_licenses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment usage counters
CREATE OR REPLACE FUNCTION increment_step_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Update step execution count
    UPDATE library_steps 
    SET execution_count = execution_count + 1,
        last_executed = CURRENT_TIMESTAMP
    WHERE id = NEW.step_id;
    
    -- Update library usage count
    UPDATE step_libraries 
    SET usage_count = usage_count + 1,
        last_used = CURRENT_TIMESTAMP
    WHERE id = (SELECT library_id FROM library_steps WHERE id = NEW.step_id);
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update usage counters
CREATE TRIGGER increment_usage_on_analytics_insert
    AFTER INSERT ON library_usage_analytics
    FOR EACH ROW EXECUTE FUNCTION increment_step_usage();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert core system library (built-in steps)
INSERT INTO step_libraries (
    name, version, display_name, description, author, 
    file_path, file_hash, is_enabled, status
) VALUES (
    'core', '1.0.0', 'Core System Library', 
    'Built-in core steps for flow control and basic operations',
    'OpsConductor Team', '/app/core', 'builtin', true, 'installed'
) ON CONFLICT (name, version) DO NOTHING;

-- Get the core library ID for inserting steps
DO $$
DECLARE
    core_lib_id INTEGER;
BEGIN
    SELECT id INTO core_lib_id FROM step_libraries WHERE name = 'core' AND version = '1.0.0';
    
    -- Insert core steps
    INSERT INTO library_steps (library_id, name, display_name, category, description, icon, color, inputs, outputs) VALUES
    (core_lib_id, 'flow.start', 'Start', 'flow', 'Job start point', '▶️', '#28a745', 0, 1),
    (core_lib_id, 'flow.end', 'End', 'flow', 'Job end point', '⏹️', '#dc3545', 1, 0),
    (core_lib_id, 'target.assign', 'Target Assignment', 'targets', 'Assign job execution to specific target', '🎯', '#28a745', 1, 1)
    ON CONFLICT (library_id, name) DO NOTHING;
END $$;

-- Insert sample marketplace entries
INSERT INTO library_marketplace (
    name, latest_version, display_name, description, author,
    download_url, is_free, categories, tags, is_featured
) VALUES 
(
    'file-operations', '1.2.0', 'File Operations Library',
    'Comprehensive file and directory operations with 25+ commands',
    'OpsConductor Team', 'https://marketplace.opsconductor.com/libraries/file-operations-1.2.0.zip',
    true, ARRAY['file', 'directory'], ARRAY['file', 'copy', 'move', 'delete'], true
),
(
    'network-tools', '2.1.0', 'Network Tools Library',
    'Network diagnostics, monitoring, and connectivity tools',
    'OpsConductor Team', 'https://marketplace.opsconductor.com/libraries/network-tools-2.1.0.zip',
    true, ARRAY['network', 'monitoring'], ARRAY['ping', 'traceroute', 'port-scan'], true
),
(
    'database-operations', '1.5.0', 'Database Operations Library',
    'Database connectivity, queries, and management operations',
    'OpsConductor Team', 'https://marketplace.opsconductor.com/libraries/database-operations-1.5.0.zip',
    false, ARRAY['database', 'sql'], ARRAY['mysql', 'postgresql', 'mongodb'], false
)
ON CONFLICT (name) DO NOTHING;