
-- added pupa_id column
ALTER TABLE candidate ADD COLUMN pupa_id VARCHAR(255);
CREATE INDEX ix_candidate_pupa_id ON candidate (pupa_id);