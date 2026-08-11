-- Adresa korisnika na MSISDN
ALTER TABLE msisdn ADD COLUMN IF NOT EXISTS adresa TEXT;
ALTER TABLE msisdn ADD COLUMN IF NOT EXISTS grad VARCHAR(100);
ALTER TABLE msisdn ADD COLUMN IF NOT EXISTS postanski_broj VARCHAR(10);

-- Plaćanja (kartica / gotovina)
CREATE TABLE IF NOT EXISTS placanja (
  id SERIAL PRIMARY KEY,
  msisdn_id INT NOT NULL REFERENCES msisdn(id) ON DELETE CASCADE,
  nacin VARCHAR(20) NOT NULL CHECK (nacin IN ('gotovina', 'kartica')),
  broj_kartice_hash VARCHAR(128),
  datum_isteka VARCHAR(7),
  cvv_hash VARCHAR(128),
  ime_vlasnika VARCHAR(255),
  iznos NUMERIC(10, 2) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'izvrseno' CHECK (status IN ('izvrseno', 'cekanje', 'greska')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_placanja_msisdn_id ON placanja(msisdn_id);
