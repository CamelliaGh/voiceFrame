-- Update background orientations based on visual analysis
-- This script assigns appropriate orientation values to existing backgrounds

-- Update specific backgrounds based on their visual characteristics
UPDATE admin_backgrounds
SET orientation = 'landscape'
WHERE file_path LIKE '%beautiful-roses-great-white-wooden-background-with-space-right.jpg%'
   OR name = 'roses-wooden';

-- Set abstract and pattern backgrounds to 'both' (suitable for any orientation)
UPDATE admin_backgrounds
SET orientation = 'both'
WHERE file_path LIKE '%237.jpg%'
   OR file_path LIKE '%copy-space-with-cute-hearts.jpg%'
   OR file_path LIKE '%flat-lay-small-cute-hearts.jpg%'
   OR name IN ('abstract-blurred', 'cute-hearts', 'flat-lay-hearts');

-- Set any remaining backgrounds without orientation to 'both' as a safe default
UPDATE admin_backgrounds
SET orientation = 'both'
WHERE orientation IS NULL OR orientation = '';

-- Verify the updates
SELECT name, display_name, orientation, file_path
FROM admin_backgrounds
ORDER BY orientation, name;
