CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION valid_jmbg(jmbg TEXT) RETURNS BOOLEAN AS $$
DECLARE
  w INT[] := ARRAY[7,6,5,4,3,2,7,6,5,4,3,2];
  s INT := 0;
  i INT;
  r INT;
  k INT;
BEGIN
  IF jmbg IS NULL OR length(jmbg) <> 13 OR jmbg ~ '[^0-9]' THEN
    RETURN FALSE;
  END IF;
  FOR i IN 1..12 LOOP
    s := s + (substring(jmbg, i, 1)::INT * w[i]);
  END LOOP;
  r := s % 11;
  k := 11 - r;
  IF k = 10 OR k = 11 THEN k := 0; END IF;
  RETURN k = substring(jmbg, 13, 1)::INT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE TABLE IF NOT EXISTS zupanije (
  id SERIAL PRIMARY KEY,
  naziv VARCHAR(255) NOT NULL UNIQUE,
  oznaka VARCHAR(20) NOT NULL UNIQUE,
  sjediste VARCHAR(255) NOT NULL,
  entitet VARCHAR(10) NOT NULL DEFAULT 'FBiH' CHECK (entitet IN ('FBiH', 'RS', 'Brčko')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS opcine (
  id SERIAL PRIMARY KEY,
  naziv VARCHAR(255) NOT NULL,
  zupanija_id INT NOT NULL REFERENCES zupanije(id) ON DELETE RESTRICT,
  entitet VARCHAR(10) NOT NULL CHECK (entitet IN ('FBiH', 'RS', 'Brčko')),
  tip_jedinice VARCHAR(20) CHECK (tip_jedinice IS NULL OR tip_jedinice IN ('grad', 'opcina')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (naziv, zupanija_id)
);

CREATE TABLE IF NOT EXISTS lokacije (
  id SERIAL PRIMARY KEY,
  opcina_id INT NOT NULL REFERENCES opcine(id) ON DELETE RESTRICT,
  naziv VARCHAR(255) NOT NULL,
  tip VARCHAR(30) NOT NULL CHECK (tip IN ('postanski_ured', 'prodajno_mjesto')),
  adresa VARCHAR(500),
  postanski_broj VARCHAR(10),
  posta_operater VARCHAR(3) CHECK (posta_operater IS NULL OR posta_operater IN ('HP', 'BHP', 'PS')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_lokacije_postanski_broj_unique
  ON lokacije (postanski_broj) WHERE postanski_broj IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_lokacije_opcina_id ON lokacije(opcina_id);
CREATE INDEX IF NOT EXISTS idx_lokacije_tip ON lokacije(tip);
CREATE INDEX IF NOT EXISTS idx_lokacije_postanski_broj ON lokacije(postanski_broj);

CREATE TABLE IF NOT EXISTS uredjaji (
  id SERIAL PRIMARY KEY,
  lokacija_id INT NOT NULL REFERENCES lokacije(id) ON DELETE RESTRICT,
  tip VARCHAR(10) NOT NULL CHECK (tip IN ('MSAN', 'OLT')),
  oznaka VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (lokacija_id, oznaka)
);

CREATE INDEX IF NOT EXISTS idx_uredjaji_lokacija_id ON uredjaji(lokacija_id);
CREATE INDEX IF NOT EXISTS idx_uredjaji_tip ON uredjaji(tip);

CREATE TABLE IF NOT EXISTS rasponi (
  id SERIAL PRIMARY KEY,
  uredjaj_id INT NOT NULL REFERENCES uredjaji(id) ON DELETE RESTRICT,
  pocetak VARCHAR(15) NOT NULL,
  kraj VARCHAR(15) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (pocetak ~ '^[0-9]+$' AND kraj ~ '^[0-9]+$' AND pocetak <= kraj)
);

CREATE INDEX IF NOT EXISTS idx_rasponi_uredjaj_id ON rasponi(uredjaj_id);
CREATE INDEX IF NOT EXISTS idx_rasponi_pocetak_kraj ON rasponi(pocetak, kraj);

CREATE TABLE IF NOT EXISTS kvaliteta (
  id SERIAL PRIMARY KEY,
  naziv VARCHAR(20) NOT NULL UNIQUE CHECK (naziv IN ('silver', 'gold', 'platinum', 'diamond')),
  cijena NUMERIC(10, 2) NOT NULL CHECK (cijena >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS msisdn (
  id SERIAL PRIMARY KEY,
  broj VARCHAR(15) NOT NULL UNIQUE,
  status VARCHAR(20) NOT NULL DEFAULT 'slobodan'
    CHECK (status IN ('slobodan', 'zauzet', 'karantena')),
  raspon_id INT REFERENCES rasponi(id) ON DELETE SET NULL,
  kvaliteta_id INT REFERENCES kvaliteta(id) ON DELETE SET NULL,
  jmbg VARCHAR(13) CHECK (jmbg IS NULL OR (length(jmbg) = 13 AND jmbg ~ '^[0-9]+$')),
  rezerviran_do TIMESTAMPTZ,
  datum_karantene TIMESTAMPTZ,
  karantena_dana INT NOT NULL DEFAULT 60 CHECK (karantena_dana > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (broj ~ '^[0-9]+$')
);

CREATE INDEX IF NOT EXISTS idx_msisdn_broj ON msisdn(broj);
CREATE INDEX IF NOT EXISTS idx_msisdn_status ON msisdn(status);
CREATE INDEX IF NOT EXISTS idx_msisdn_jmbg ON msisdn(jmbg);
CREATE INDEX IF NOT EXISTS idx_msisdn_raspon_id ON msisdn(raspon_id);
CREATE INDEX IF NOT EXISTS idx_msisdn_kvaliteta_id ON msisdn(kvaliteta_id);
CREATE INDEX IF NOT EXISTS idx_msisdn_rezerviran_do ON msisdn(rezerviran_do) WHERE rezerviran_do IS NOT NULL;

CREATE TABLE IF NOT EXISTS msisdn_history (
  id SERIAL PRIMARY KEY,
  msisdn_id INT NOT NULL REFERENCES msisdn(id) ON DELETE CASCADE,
  radnik_id INT,
  stari_status VARCHAR(20),
  novi_status VARCHAR(20) NOT NULL,
  napomena TEXT,
  promijenjeno_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_msisdn_history_msisdn_id ON msisdn_history(msisdn_id);
CREATE INDEX IF NOT EXISTS idx_msisdn_history_radnik_id ON msisdn_history(radnik_id);
CREATE INDEX IF NOT EXISTS idx_msisdn_history_promijenjeno_at ON msisdn_history(promijenjeno_at);

CREATE TABLE IF NOT EXISTS radnici (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  ime VARCHAR(100) NOT NULL,
  prezime VARCHAR(100) NOT NULL,
  lozinka_hash VARCHAR(255) NOT NULL,
  uloga VARCHAR(20) NOT NULL CHECK (uloga IN ('admin', 'prodaja', 'promet')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_radnici_email ON radnici(email);
CREATE INDEX IF NOT EXISTS idx_radnici_uloga ON radnici(uloga);

CREATE TABLE IF NOT EXISTS notifikacije (
  id SERIAL PRIMARY KEY,
  email_primatelj VARCHAR(255) NOT NULL,
  predmet VARCHAR(500) NOT NULL,
  sadrzaj TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ceka'
    CHECK (status IN ('ceka', 'poslano', 'greska')),
  radnik_id INT REFERENCES radnici(id) ON DELETE SET NULL,
  msisdn_id INT REFERENCES msisdn(id) ON DELETE SET NULL,
  poslano_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifikacije_status ON notifikacije(status);
CREATE INDEX IF NOT EXISTS idx_notifikacije_email ON notifikacije(email_primatelj);

-- FK za msisdn_history.radnik_id (nakon radnici)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'msisdn_history_radnik_id_fkey'
  ) THEN
    ALTER TABLE msisdn_history
      ADD CONSTRAINT msisdn_history_radnik_id_fkey
      FOREIGN KEY (radnik_id) REFERENCES radnici(id) ON DELETE SET NULL;
  END IF;
END $$;

-- Županije FBiH + regije RS + Brčko
INSERT INTO zupanije (naziv, oznaka, sjediste, entitet) VALUES
  ('Unsko-sanska županija', 'USŽ', 'Bihać', 'FBiH'),
  ('Posavska županija', 'ŽP', 'Orašje', 'FBiH'),
  ('Tuzlanska županija', 'TK', 'Tuzla', 'FBiH'),
  ('Zeničko-dobojska županija', 'ZDŽ', 'Zenica', 'FBiH'),
  ('Bosansko-podrinjska županija Goražde', 'BPŽ', 'Goražde', 'FBiH'),
  ('Srednjobosanska županija', 'SBŽ', 'Travnik', 'FBiH'),
  ('Hercegovačko-neretvanska županija', 'HNŽ', 'Mostar', 'FBiH'),
  ('Zapadnohercegovačka županija', 'ZHŽ', 'Široki Brijeg', 'FBiH'),
  ('Sarajevska županija', 'KS', 'Sarajevo', 'FBiH'),
  ('Kanton 10 (Hercegbosanska županija)', 'HBŽ', 'Livno', 'FBiH'),
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
ON CONFLICT (naziv) DO NOTHING;

INSERT INTO opcine (naziv, zupanija_id, entitet)
SELECT 'Mostar', z.id, 'FBiH'
FROM zupanije z
WHERE z.oznaka = 'HNŽ'
ON CONFLICT (naziv, zupanija_id) DO NOTHING;

INSERT INTO kvaliteta (naziv, cijena) VALUES
  ('silver', 10.00),
  ('gold', 25.00),
  ('platinum', 50.00),
  ('diamond', 100.00)
ON CONFLICT (naziv) DO NOTHING;

INSERT INTO radnici (email, ime, prezime, lozinka_hash, uloga)
VALUES (
  'admin@eronet.ba',
  'Admin',
  'Eronet',
  crypt('admin123', gen_salt('bf', 12)),
  'admin'
)
ON CONFLICT (email) DO UPDATE SET
  lozinka_hash = EXCLUDED.lozinka_hash,
  uloga = EXCLUDED.uloga,
  updated_at = NOW();
