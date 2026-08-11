ALTER TABLE radnici ADD COLUMN IF NOT EXISTS aktivan BOOLEAN NOT NULL DEFAULT TRUE;

-- Lozinka: admin (bcrypt; generirano hash_password('admin') za bcrypt 4.x)
UPDATE radnici
SET lozinka_hash = '$2b$12$l/.XI419QRrytNIzaBKck.p1BiK0eet0xAacvoEk/Qgsb38C0fiQu',
    aktivan = TRUE
WHERE email = 'admin@eronet.ba';
