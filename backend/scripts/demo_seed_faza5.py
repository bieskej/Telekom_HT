"""
Demo seed za fazu 5: kupci, servisni nalozi, port-in, karantena.
Pokretanje: cd backend && python -m scripts.demo_seed_faza5
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.auth.security import hash_password
from app.database import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        admin_id = db.execute(
            text("SELECT id FROM radnici WHERE email = 'admin@eronet.ba' LIMIT 1")
        ).scalar()
        if not admin_id:
            print("Nema admin@eronet.ba — pokrenite osnovni seed prvo.")
            return

        uredjaj_id = db.execute(text("SELECT id FROM uredjaji ORDER BY id LIMIT 1")).scalar()
        if not uredjaj_id:
            print("Nema uređaja u bazi.")
            return

        kupci = [
            ("demo.kupac1@eronet.ba", "Demo", "Kupac1", "0101000500012"),
            ("demo.kupac2@eronet.ba", "Demo", "Kupac2", "0101000500013"),
            ("demo.kupac3@eronet.ba", "Demo", "Kupac3", "0101000500014"),
        ]
        lozinka = hash_password("kupac123")
        for email, ime, prezime, jmbg in kupci:
            db.execute(
                text(
                    """
                    INSERT INTO radnici (email, ime, prezime, lozinka_hash, uloga, aktivan, jmbg)
                    SELECT :email, :ime, :prezime, :hash, 'kupac', true, :jmbg
                    WHERE NOT EXISTS (SELECT 1 FROM radnici WHERE email = :email)
                    """
                ),
                {"email": email, "ime": ime, "prezime": prezime, "hash": lozinka, "jmbg": jmbg},
            )

        db.execute(
            text(
                """
                INSERT INTO servisni_nalog (uredjaj_id, opis, status, prioritet, prijavio_id)
                SELECT :uid, 'Demo: nestabilan MSAN port', 'otvoren', 'srednji', :aid
                WHERE NOT EXISTS (
                    SELECT 1 FROM servisni_nalog WHERE opis LIKE 'Demo: nestabilan%'
                )
                """
            ),
            {"uid": uredjaj_id, "aid": admin_id},
        )
        db.execute(
            text(
                """
                INSERT INTO servisni_nalog (uredjaj_id, opis, status, prioritet, prijavio_id)
                SELECT :uid, 'Demo: kritičan kvar napajanja', 'u_obradi', 'kritican', :aid
                WHERE NOT EXISTS (
                    SELECT 1 FROM servisni_nalog WHERE opis LIKE 'Demo: kritičan%'
                )
                """
            ),
            {"uid": uredjaj_id, "aid": admin_id},
        )

        db.execute(
            text(
                """
                INSERT INTO portabilnost (tip, izvor_op, ciljni_op, status, broj, created_by)
                SELECT 'port_in', 'Operator X', 'HT d.d. Mostar', 'zahtjev', '3999900001', :aid
                WHERE NOT EXISTS (SELECT 1 FROM portabilnost WHERE broj = '3999900001')
                """
            ),
            {"aid": admin_id},
        )

        db.execute(
            text(
                """
                UPDATE msisdn SET status = 'karantena', datum_karantene = NOW(),
                       karantena_dana = 45, karantena_razlog = 'Demo seed'
                WHERE id IN (
                    SELECT m.id FROM msisdn m
                    WHERE m.status = 'zauzet'
                    LIMIT 5
                )
                """
            )
        )

        db.commit()
        print("Demo seed faza 5: 3 kupca (lozinka kupac123), 2 servisna naloga, 1 port-in, 5 karantena.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
