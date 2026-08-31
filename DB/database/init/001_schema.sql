CREATE TABLE standort (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plz VARCHAR(10) NOT NULL,
    stadt VARCHAR(100) NOT NULL,
    strasse VARCHAR(100) NOT NULL,
    hausnummer VARCHAR(20) NOT NULL
);

CREATE TABLE techniker (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL
);

CREATE TABLE geraet (
    seriennummer VARCHAR(100) PRIMARY KEY,
    hersteller VARCHAR(100) NOT NULL,
    typ VARCHAR(100) NOT NULL,
    wartungsintervall INTEGER NOT NULL CHECK (wartungsintervall > 0),
    standort_id BIGINT NOT NULL REFERENCES standort(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE standort_techniker (
    standort_id BIGINT NOT NULL REFERENCES standort(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    techniker_id BIGINT NOT NULL REFERENCES techniker(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (standort_id, techniker_id)
);

CREATE TABLE typ_techniker (
    geraetetyp VARCHAR(100) NOT NULL,
    techniker_id BIGINT NOT NULL REFERENCES techniker(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (geraetetyp, techniker_id)
);

CREATE TABLE wartungsplan (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    datum DATE NOT NULL,
    geraet_seriennummer VARCHAR(100) NOT NULL REFERENCES geraet(seriennummer)
        ON UPDATE CASCADE ON DELETE CASCADE,
    techniker_id BIGINT NOT NULL REFERENCES techniker(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (datum, geraet_seriennummer)
);

CREATE TABLE wartung (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    datum DATE NOT NULL,
    ersatzgeraet VARCHAR(100),
    geraet_seriennummer VARCHAR(100) NOT NULL REFERENCES geraet(seriennummer)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    techniker_id BIGINT NOT NULL REFERENCES techniker(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    wartungsplan_id BIGINT REFERENCES wartungsplan(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX idx_geraet_standort ON geraet (standort_id);
CREATE INDEX idx_wartungsplan_datum ON wartungsplan (datum);
CREATE INDEX idx_wartung_geraet ON wartung (geraet_seriennummer);
