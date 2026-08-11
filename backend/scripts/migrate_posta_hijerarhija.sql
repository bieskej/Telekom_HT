-- Pošta + hijerarhija: tip općine, entitet Brčko, lokacije PB/operater

ALTER TABLE zupanije ADD COLUMN IF NOT EXISTS entitet VARCHAR(10) NOT NULL DEFAULT 'FBiH';
ALTER TABLE zupanije DROP CONSTRAINT IF EXISTS zupanije_entitet_check;
ALTER TABLE zupanije ADD CONSTRAINT zupanije_entitet_check
  CHECK (entitet IN ('FBiH', 'RS', 'Brčko'));

UPDATE zupanije SET entitet = 'FBiH' WHERE entitet IS NULL OR entitet = '';

ALTER TABLE opcine ADD COLUMN IF NOT EXISTS tip_jedinice VARCHAR(20);
ALTER TABLE opcine DROP CONSTRAINT IF EXISTS opcine_tip_jedinice_check;
ALTER TABLE opcine ADD CONSTRAINT opcine_tip_jedinice_check
  CHECK (tip_jedinice IS NULL OR tip_jedinice IN ('grad', 'opcina'));

ALTER TABLE opcine DROP CONSTRAINT IF EXISTS opcine_entitet_check;
ALTER TABLE opcine ADD CONSTRAINT opcine_entitet_check
  CHECK (entitet IN ('FBiH', 'RS', 'Brčko'));

ALTER TABLE lokacije ADD COLUMN IF NOT EXISTS postanski_broj VARCHAR(10);
ALTER TABLE lokacije ADD COLUMN IF NOT EXISTS posta_operater VARCHAR(3);

ALTER TABLE lokacije DROP CONSTRAINT IF EXISTS lokacije_posta_operater_check;
ALTER TABLE lokacije ADD CONSTRAINT lokacije_posta_operater_check
  CHECK (posta_operater IS NULL OR posta_operater IN ('HP', 'BHP', 'PS'));

CREATE UNIQUE INDEX IF NOT EXISTS idx_lokacije_postanski_broj_unique
  ON lokacije (postanski_broj) WHERE postanski_broj IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_lokacije_postanski_broj ON lokacije(postanski_broj);

-- RS regije (županije/regije)
INSERT INTO zupanije (naziv, oznaka, sjediste, entitet) VALUES
  ('Regija Banja Luka', 'RS-BL', 'Banja Luka', 'RS'),
  ('Regija Bijeljina', 'RS-BIJ', 'Bijeljina', 'RS'),
  ('Regija Doboj', 'RS-DOB', 'Doboj', 'RS'),
  ('Regija Istočno Sarajevo', 'RS-ISA', 'Istočno Sarajevo', 'RS'),
  ('Regija Trebinje', 'RS-TRE', 'Trebinje', 'RS'),
  ('Regija Foča', 'RS-FOC', 'Foča', 'RS'),
  ('Regija Prijedor', 'RS-PRI', 'Prijedor', 'RS'),
  ('Regija Zvornik', 'RS-ZV', 'Zvornik', 'RS'),
  ('Regija Gradiška', 'RS-GRA', 'Gradiška', 'RS'),
  ('Distrikt Brčko', 'BRC', 'Brčko', 'Brčko')
ON CONFLICT (naziv) DO UPDATE SET
  oznaka = EXCLUDED.oznaka,
  sjediste = EXCLUDED.sjediste,
  entitet = EXCLUDED.entitet,
  updated_at = NOW();

UPDATE zupanije SET entitet = 'FBiH' WHERE oznaka IN ('USŽ', 'ŽP', 'TK', 'ZDŽ', 'BPŽ', 'SBŽ', 'HNŽ', 'ZHŽ', 'KS', 'HBŽ');
