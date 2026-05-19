from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Zupanija(Base):
    __tablename__ = "zupanije"

    id = Column(Integer, primary_key=True)
    naziv = Column(String(255), nullable=False)
    oznaka = Column(String(20), nullable=False)
    entitet = Column(String(10), nullable=False, default="FBiH")


class Opcina(Base):
    __tablename__ = "opcine"

    id = Column(Integer, primary_key=True)
    naziv = Column(String(255), nullable=False)
    zupanija_id = Column(Integer, ForeignKey("zupanije.id"), nullable=False)
    entitet = Column(String(10), nullable=False)
    tip_jedinice = Column(String(20), nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)


class Lokacija(Base):
    __tablename__ = "lokacije"

    id = Column(Integer, primary_key=True)
    opcina_id = Column(Integer, ForeignKey("opcine.id"), nullable=False)
    naziv = Column(String(255), nullable=False)
    tip = Column(String(30), nullable=False)
    postanski_broj = Column(String(10), nullable=True)
    posta_operater = Column(String(3), nullable=True)


class Uredjaj(Base):
    __tablename__ = "uredjaji"

    id = Column(Integer, primary_key=True)
    lokacija_id = Column(Integer, ForeignKey("lokacije.id"), nullable=False)
    tip = Column(String(10), nullable=False)
    oznaka = Column(String(100), nullable=False)


class Raspon(Base):
    __tablename__ = "rasponi"

    id = Column(Integer, primary_key=True)
    uredjaj_id = Column(Integer, ForeignKey("uredjaji.id"), nullable=False)
    pocetak = Column(String(15), nullable=False)
    kraj = Column(String(15), nullable=False)


class Kvaliteta(Base):
    __tablename__ = "kvaliteta"

    id = Column(Integer, primary_key=True)
    naziv = Column(String(20), nullable=False)
    cijena = Column(Numeric(10, 2), nullable=False)


class Msisdn(Base):
    __tablename__ = "msisdn"

    id = Column(Integer, primary_key=True)
    broj = Column(String(15), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="slobodan")
    raspon_id = Column(Integer, ForeignKey("rasponi.id"))
    kvaliteta_id = Column(Integer, ForeignKey("kvaliteta.id"))
    jmbg = Column(String(13))
    ime = Column(String(100))
    prezime = Column(String(100))
    email = Column(String(255))
    adresa = Column(Text)
    grad = Column(String(100))
    postanski_broj = Column(String(10))
    rezerviran_do = Column(DateTime(timezone=True))
    datum_karantene = Column(DateTime(timezone=True))
    karantena_dana = Column(Integer, nullable=False, default=60)
    karantena_razlog = Column(String(255), nullable=True)
    u_kvaru = Column(Boolean, nullable=False, default=False)
    datum_dodjele = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    raspon = relationship("Raspon")
    kvaliteta = relationship("Kvaliteta")


class Radnik(Base):
    """Korisnik sustava: radnik (admin/prodaja/promet) ili kupac (portal).

    Kupac dijeli istu tablicu jer ima email, lozinka i JMBG za povezivanje
    s dodijeljenim MSISDN brojevima (msisdn.jmbg = radnici.jmbg).
    """

    __tablename__ = "radnici"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    ime = Column(String(100), nullable=False)
    prezime = Column(String(100), nullable=False)
    lozinka_hash = Column(String(255), nullable=False)
    uloga = Column(String(20), nullable=False)
    aktivan = Column(Boolean, nullable=False, default=True)
    jmbg = Column(String(13), nullable=True)


class EmailLog(Base):
    __tablename__ = "email_log"

    id = Column(Integer, primary_key=True)
    msisdn_id = Column(Integer, ForeignKey("msisdn.id"), nullable=True)
    primatelj = Column(String(255), nullable=False)
    predmet = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)
    error_text = Column(Text, nullable=True)
    html_tijelo = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)


class KupacKontakt(Base):
    __tablename__ = "kupac_kontakt"

    id = Column(Integer, primary_key=True)
    kupac_id = Column(Integer, ForeignKey("radnici.id"), nullable=False)
    predmet = Column(String(255), nullable=False)
    poruka = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Placanje(Base):
    __tablename__ = "placanja"

    id = Column(Integer, primary_key=True)
    msisdn_id = Column(Integer, ForeignKey("msisdn.id"), nullable=False)
    nacin = Column(String(20), nullable=False)
    broj_kartice_hash = Column(String(128))
    datum_isteka = Column(String(7))
    cvv_hash = Column(String(128))
    ime_vlasnika = Column(String(255))
    iznos = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="izvrseno")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MsisdnHistory(Base):
    __tablename__ = "msisdn_history"

    id = Column(Integer, primary_key=True)
    msisdn_id = Column(Integer, ForeignKey("msisdn.id"), nullable=False)
    radnik_id = Column(Integer, ForeignKey("radnici.id"))
    stari_status = Column(String(20))
    novi_status = Column(String(20), nullable=False)
    akcija = Column(String(50))
    napomena = Column(Text)
    promijenjeno_at = Column(DateTime(timezone=True), server_default=func.now())


class Portabilnost(Base):
    __tablename__ = "portabilnost"

    id = Column(Integer, primary_key=True)
    msisdn_id = Column(Integer, ForeignKey("msisdn.id"), nullable=True)
    broj = Column(String(15), nullable=True)
    tip = Column(String(20), nullable=False)
    izvor_op = Column(String(100), nullable=False)
    ciljni_op = Column(String(100), nullable=False)
    datum_zahtjeva = Column(DateTime(timezone=True), server_default=func.now())
    datum_realizacije = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), nullable=False, default="zahtjev")
    napomena = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("radnici.id"), nullable=True)


class ServisniNalog(Base):
    __tablename__ = "servisni_nalog"

    id = Column(Integer, primary_key=True)
    uredjaj_id = Column(Integer, ForeignKey("uredjaji.id"), nullable=False)
    opis = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="otvoren")
    prioritet = Column(String(20), nullable=False, default="srednji")
    prijavio_id = Column(Integer, ForeignKey("radnici.id"), nullable=True)
    rijesio_id = Column(Integer, ForeignKey("radnici.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    rijeseno_at = Column(DateTime(timezone=True), nullable=True)
