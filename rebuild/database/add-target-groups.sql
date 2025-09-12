-- Target Groups Migration
-- Add hierarchical target grouping with materialized path

-- Target groups table with materialized path for efficient hierarchy queries
CREATE TABLE assets.target_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_group_id INTEGER REFERENCES assets.target_groups(id) ON DELETE CASCADE,
    path VARCHAR(500) NOT NULL, -- Materialized path like '/1/2/4/'
    level INTEGER CHECK (level >= 1 AND level <= 3) NOT NULL,
    color VARCHAR(7), -- Hex color like '#FF5733'
    icon VARCHAR(50), -- Icon name/class for UI
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_name_per_parent UNIQUE (name, parent_group_id),
    CONSTRAINT valid_path_format CHECK (path ~ '^(/\d+)+/$')
);

-- Target group memberships (many-to-many relationship)
CREATE TABLE assets.target_group_memberships (
    id SERIAL PRIMARY KEY,
    target_id INTEGER REFERENCES assets.enhanced_targets(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES assets.target_groups(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER, -- Could reference identity.users(id) if needed
    
    -- Prevent duplicate memberships
    UNIQUE(target_id, group_id)
);

-- Indexes for performance
CREATE INDEX idx_target_groups_path ON assets.target_groups(path);
CREATE INDEX idx_target_groups_parent ON assets.target_groups(parent_group_id);
CREATE INDEX idx_target_groups_level ON assets.target_groups(level);
CREATE INDEX idx_target_groups_name ON assets.target_groups(name);

CREATE INDEX idx_target_group_memberships_target ON assets.target_group_memberships(target_id);
CREATE INDEX idx_target_group_memberships_group ON assets.target_group_memberships(group_id);

-- Function to automatically update path when parent changes
CREATE OR REPLACE FUNCTION assets.update_target_group_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path VARCHAR(500) := '';
    new_path VARCHAR(500);
BEGIN
    -- If this is a root group (no parent)
    IF NEW.parent_group_id IS NULL THEN
        NEW.path := '/' || NEW.id || '/';
        NEW.level := 1;
    ELSE
        -- Get parent's path and level
        SELECT path, level INTO parent_path, NEW.level 
        FROM assets.target_groups 
        WHERE id = NEW.parent_group_id;
        
        -- Increment level
        NEW.level := NEW.level + 1;
        
        -- Build new path
        NEW.path := parent_path || NEW.id || '/';
        
        -- Enforce 3-level limit
        IF NEW.level > 3 THEN
            RAISE EXCEPTION 'Target groups cannot exceed 3 levels deep';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically maintain path and level
CREATE TRIGGER trigger_update_target_group_path
    BEFORE INSERT OR UPDATE OF parent_group_id ON assets.target_groups
    FOR EACH ROW
    EXECUTE FUNCTION assets.update_target_group_path();

-- Function to prevent circular references
CREATE OR REPLACE FUNCTION assets.prevent_circular_group_reference()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the new parent would create a circular reference
    IF NEW.parent_group_id IS NOT NULL THEN
        -- Check if the new parent is a descendant of this group
        IF EXISTS (
            SELECT 1 FROM assets.target_groups 
            WHERE id = NEW.parent_group_id 
            AND path LIKE (SELECT path || '%' FROM assets.target_groups WHERE id = NEW.id)
        ) THEN
            RAISE EXCEPTION 'Cannot create circular reference: group cannot be its own ancestor';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent circular references
CREATE TRIGGER trigger_prevent_circular_group_reference
    BEFORE UPDATE OF parent_group_id ON assets.target_groups
    FOR EACH ROW
    EXECUTE FUNCTION assets.prevent_circular_group_reference();

-- Function to update all descendant paths when a group is moved
CREATE OR REPLACE FUNCTION assets.update_descendant_paths()
RETURNS TRIGGER AS $$
DECLARE
    old_path VARCHAR(500);
    new_path VARCHAR(500);
    descendant RECORD;
BEGIN
    -- Only process if path actually changed
    IF OLD.path != NEW.path THEN
        old_path := OLD.path;
        new_path := NEW.path;
        
        -- Update all descendants
        FOR descendant IN 
            SELECT id, path FROM assets.target_groups 
            WHERE path LIKE old_path || '%' AND id != NEW.id
        LOOP
            UPDATE assets.target_groups 
            SET path = new_path || substring(descendant.path from length(old_path) + 1),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = descendant.id;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update descendant paths
CREATE TRIGGER trigger_update_descendant_paths
    AFTER UPDATE OF path ON assets.target_groups
    FOR EACH ROW
    EXECUTE FUNCTION assets.update_descendant_paths();

-- Add some sample data for testing
INSERT INTO assets.target_groups (name, description, parent_group_id) VALUES
('Production', 'Production environment systems', NULL),
('Development', 'Development environment systems', NULL),
('Testing', 'Testing environment systems', NULL);

-- Add some nested groups (will be created after the parent groups get their IDs)
-- These will be added via the API once we have the backend endpoints