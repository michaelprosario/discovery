-- Update created_by field for all existing records
-- This script sets created_by to 'michael.p.rosario@gmail.com' for all tables

-- Update notebooks table
UPDATE notebooks
SET created_by = 'michael.p.rosario@gmail.com'
WHERE created_by = 'system@discovery.local' OR created_by IS NULL OR created_by = '';

-- Update sources table
UPDATE sources
SET created_by = 'michael.p.rosario@gmail.com'
WHERE created_by = 'system@discovery.local' OR created_by IS NULL OR created_by = '';

-- Update outputs table
UPDATE outputs
SET created_by = 'michael.p.rosario@gmail.com'
WHERE created_by = 'system@discovery.local' OR created_by IS NULL OR created_by = '';

-- Verify the updates
SELECT 'notebooks' as table_name, COUNT(*) as total_records, 
       COUNT(CASE WHEN created_by = 'michael.p.rosario@gmail.com' THEN 1 END) as updated_records
FROM notebooks
UNION ALL
SELECT 'sources' as table_name, COUNT(*) as total_records, 
       COUNT(CASE WHEN created_by = 'michael.p.rosario@gmail.com' THEN 1 END) as updated_records
FROM sources
UNION ALL
SELECT 'outputs' as table_name, COUNT(*) as total_records, 
       COUNT(CASE WHEN created_by = 'michael.p.rosario@gmail.com' THEN 1 END) as updated_records
FROM outputs;
