-- Ubrzanje pretrage slobodnih brojeva po kvaliteti i statusu
CREATE INDEX IF NOT EXISTS idx_msisdn_kvaliteta_status ON msisdn(kvaliteta_id, status);
