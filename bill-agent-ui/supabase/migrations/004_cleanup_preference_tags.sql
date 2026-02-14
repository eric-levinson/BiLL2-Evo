-- Migration: Clean up incorrectly saved Sleeper username from preference_tags
-- Description: Removes "Sleeper Username: ..." entries from preference_tags array
--              These should have been saved to user_onboarding.sleeper_username instead

-- Remove Sleeper username entries from preference_tags
UPDATE public.user_preferences
SET preference_tags = (
  SELECT array_agg(tag)
  FROM unnest(preference_tags) AS tag
  WHERE tag NOT LIKE 'Sleeper Username:%'
  AND tag NOT LIKE 'Sleeper username:%'
  AND tag NOT LIKE 'sleeper username:%'
)
WHERE EXISTS (
  SELECT 1
  FROM unnest(preference_tags) AS tag
  WHERE tag LIKE 'Sleeper Username:%'
  OR tag LIKE 'Sleeper username:%'
  OR tag LIKE 'sleeper username:%'
);

-- Log how many rows were affected
DO $$
DECLARE
  affected_count INTEGER;
BEGIN
  GET DIAGNOSTICS affected_count = ROW_COUNT;
  RAISE NOTICE 'Cleaned up % user preference records', affected_count;
END $$;
