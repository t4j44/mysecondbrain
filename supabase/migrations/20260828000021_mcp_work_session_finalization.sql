-- 0021a: add the enum value ALONE. A new enum value cannot be USED until the
-- transaction that added it has committed, so nothing else may live in this file.
ALTER TYPE interaction_type ADD VALUE IF NOT EXISTS 'work_session';
