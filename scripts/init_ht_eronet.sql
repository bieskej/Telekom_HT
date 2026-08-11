-- Kreiranje baze (izvršava se na postgres)
SELECT 'CREATE DATABASE ht_eronet ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'ht_eronet')\gexec
