-- Proširi status notifikacija za SMTP koji nije konfiguriran
ALTER TABLE notifikacije DROP CONSTRAINT IF EXISTS notifikacije_status_check;
ALTER TABLE notifikacije ADD CONSTRAINT notifikacije_status_check
  CHECK (status IN ('ceka', 'poslano', 'greska', 'nedostaje_smtp'));

ALTER TABLE notifikacije ADD COLUMN IF NOT EXISTS tip VARCHAR(50);
