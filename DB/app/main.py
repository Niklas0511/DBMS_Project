import os
import secrets
from datetime import date
from typing import Any

from contextlib import asynccontextmanager
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from fastapi import Depends, Header, HTTPException, Query, Response, status
from psycopg import sql
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row
from pydantic import BaseModel, Field, model_validator, field_validator

DATABASE_URL = os.environ["DATABASE_URL"]
pool = AsyncConnectionPool(DATABASE_URL, open=False)

API_KEY = os.environ["API_KEY"]

@asynccontextmanager
async def lifespan(_: FastAPI):
    await pool.open()
    await pool.wait()
    yield
    await pool.close()


app = FastAPI(
    title="Wartungsmanagement API",
    version="1.0.0",
    lifespan=lifespan,
)


class StandortCreate(BaseModel):
    plz: str = Field(min_length=1, max_length=10)
    stadt: str = Field(min_length=1, max_length=100)
    strasse: str = Field(min_length=1, max_length=100)
    hausnummer: str = Field(min_length=1, max_length=20)


class GeraetCreate(BaseModel):
    seriennummer: str = Field(min_length=1, max_length=100)
    hersteller: str = Field(min_length=1, max_length=100)
    typ: str = Field(min_length=1, max_length=100)
    wartungsintervall: int = Field(gt=0)
    standort_id: int

class TechnikerEingabe(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    standort_ids: list[int] = Field(default_factory=list)
    geraetetypen: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_pruefen(cls, wert):
        wert = wert.strip()

        if not wert:
            raise ValueError("Name darf nicht leer sein")

        return wert

    @field_validator("standort_ids")
    @classmethod
    def standorte_pruefen(cls, werte):
        if any(wert <= 0 for wert in werte):
            raise ValueError("Standort-IDs müssen positiv sein")

        return sorted(set(werte))

    @field_validator("geraetetypen")
    @classmethod
    def typen_pruefen(cls, werte):
        ergebnis = set()

        for wert in werte:
            wert = wert.strip()

            if not wert or len(wert) > 100:
                raise ValueError(
                    "Gerätetypen müssen zwischen 1 und 100 Zeichen haben"
                )

            ergebnis.add(wert)

        return sorted(ergebnis)




@app.get("/health")
async def health():
    async with pool.connection() as connection:
        await connection.execute("SELECT 1")
    return {"status": "ok"}


class WartungCreate(BaseModel):
    datum: date
    ersatzgeraet: str | None = Field(default=None, max_length=100)
    geraet_seriennummer: str = Field(min_length=1, max_length=100)
    techniker_id: int = Field(gt=0)
    wartungsplan_id: int | None = Field(default=None, gt=0)


class GeraetCreate(BaseModel):
    seriennummer: str = Field(min_length=1, max_length=100)
    hersteller: str = Field(min_length=1, max_length=100)
    typ: str = Field(min_length=1, max_length=100)
    wartungsintervall: int = Field(gt=0)
    standort_id: int = Field(gt=0)


class GeraetPatch(BaseModel):
    hersteller: str | None = Field(default=None, min_length=1, max_length=100)
    typ: str | None = Field(default=None, min_length=1, max_length=100)
    wartungsintervall: int | None = Field(default=None, gt=0)
    standort_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def mindestens_ein_feld(self):
        if not self.model_fields_set:
            raise ValueError("Mindestens ein Feld muss angegeben werden")
        return self


class WartungsplanCreate(BaseModel):
    datum: date
    geraet_seriennummer: str = Field(min_length=1, max_length=100)
    techniker_id: int = Field(gt=0)    


class WartungsplanUpdate(BaseModel):
    datum: date
    techniker_id: int = Field(gt=0)


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if x_api_key is None or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder fehlender API-Key",
        )


def pruefe_zeitraum(von: date, bis: date) -> None:
    if von > bis:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'von' darf nicht nach 'bis' liegen",
        )

@app.get("/techniker/{techniker_id}/wartungsplan")
async def wartungsplan_eines_technikers(techniker_id: int):
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    wp.id AS wartungsplan_id,
                    wp.datum,
                    t.id AS techniker_id,
                    t.name AS techniker_name,
                    g.seriennummer,
                    g.hersteller,
                    g.typ,
                    g.wartungsintervall,
                    s.id AS standort_id,
                    s.plz,
                    s.stadt,
                    s.strasse,
                    s.hausnummer
                FROM wartungsplan AS wp
                JOIN techniker AS t
                    ON t.id = wp.techniker_id
                JOIN geraet AS g
                    ON g.seriennummer = wp.geraet_seriennummer
                JOIN standort AS s
                    ON s.id = g.standort_id
                WHERE wp.techniker_id = %s
                ORDER BY wp.datum, wp.id
                """,
                (techniker_id,),
            )

            wartungsplaene = await cursor.fetchall()

            if not wartungsplaene:
                await cursor.execute(
                    "SELECT id FROM techniker WHERE id = %s",
                    (techniker_id,),
                )
                if await cursor.fetchone() is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Techniker nicht gefunden",
                    )

            return wartungsplaene

@app.get("/geraete/{seriennummer}/wartungen")
async def wartungshistorie_eines_geraets(seriennummer: str):
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    w.id AS wartung_id,
                    w.datum,
                    w.ersatzgeraet,
                    w.wartungsplan_id,
                    g.seriennummer,
                    g.hersteller,
                    g.typ,
                    t.id AS techniker_id,
                    t.name AS techniker_name
                FROM wartung AS w
                JOIN geraet AS g
                    ON g.seriennummer = w.geraet_seriennummer
                JOIN techniker AS t
                    ON t.id = w.techniker_id
                WHERE w.geraet_seriennummer = %s
                ORDER BY w.datum DESC, w.id DESC
                """,
                (seriennummer,),
            )

            wartungen = await cursor.fetchall()

            if not wartungen:
                await cursor.execute(
                    "SELECT seriennummer FROM geraet WHERE seriennummer = %s",
                    (seriennummer,),
                )
                if await cursor.fetchone() is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Gerät nicht gefunden",
                    )

            return wartungen

@app.get("/geraete/{seriennummer}")
async def geraet_lesen(seriennummer: str):
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    g.seriennummer,
                    g.hersteller,
                    g.typ,
                    g.wartungsintervall,
                    s.id AS standort_id,
                    s.plz,
                    s.stadt,
                    s.strasse,
                    s.hausnummer,
                    nw.id AS naechste_wartung_id,
                    nw.datum AS naechste_wartung_datum,
                    nw.techniker_id,
                    nw.techniker_name
                FROM geraet AS g
                JOIN standort AS s
                    ON s.id = g.standort_id
                LEFT JOIN LATERAL (
                    SELECT
                        wp.id,
                        wp.datum,
                        t.id AS techniker_id,
                        t.name AS techniker_name
                    FROM wartungsplan AS wp
                    JOIN techniker AS t
                        ON t.id = wp.techniker_id
                    WHERE wp.geraet_seriennummer = g.seriennummer
                      AND wp.datum >= CURRENT_DATE
                      AND NOT EXISTS (
                          SELECT 1
                          FROM wartung AS w
                          WHERE w.wartungsplan_id = wp.id
                      )
                    ORDER BY wp.datum, wp.id
                    LIMIT 1
                ) AS nw ON TRUE
                WHERE g.seriennummer = %s
                """,
                (seriennummer,),
            )

            geraet = await cursor.fetchone()

            if geraet is None:
                raise HTTPException(
                    status_code=404,
                    detail="Gerät nicht gefunden",
                )

            return geraet
@app.get("/standorte")
async def standorte_lesen():
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    id,
                    plz,
                    stadt,
                    strasse,
                    hausnummer
                FROM standort
                ORDER BY stadt, strasse, hausnummer
                """
            )

            return await cursor.fetchall()
@app.get("/standorte/{standort_id}/geraete")
async def geraete_eines_standorts(standort_id: int):
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    g.seriennummer,
                    g.hersteller,
                    g.typ,
                    g.wartungsintervall,
                    g.standort_id
                FROM geraet AS g
                WHERE g.standort_id = %s
                ORDER BY g.hersteller, g.typ, g.seriennummer
                """,
                (standort_id,),
            )

            geraete = await cursor.fetchall()

            if not geraete:
                await cursor.execute(
                    "SELECT id FROM standort WHERE id = %s",
                    (standort_id,),
                )
                if await cursor.fetchone() is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Standort nicht gefunden",
                    )

            return geraete

@app.get("/wartungsplan")
async def wartungsplan_im_zeitraum(
    von: date = Query(alias="von"),
    bis: date = Query(alias="bis"),
):
    pruefe_zeitraum(von, bis)

    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    wp.id AS wartungsplan_id,
                    wp.datum,
                    g.seriennummer,
                    g.hersteller,
                    g.typ,
                    t.id AS techniker_id,
                    t.name AS techniker_name,
                    s.id AS standort_id,
                    s.plz,
                    s.stadt,
                    s.strasse,
                    s.hausnummer,
                    EXISTS (
                        SELECT 1
                        FROM wartung AS w
                        WHERE w.wartungsplan_id = wp.id
                    ) AS durchgefuehrt
                FROM wartungsplan AS wp
                JOIN geraet AS g
                    ON g.seriennummer = wp.geraet_seriennummer
                JOIN techniker AS t
                    ON t.id = wp.techniker_id
                JOIN standort AS s
                    ON s.id = g.standort_id
                WHERE wp.datum BETWEEN %s AND %s
                ORDER BY wp.datum, wp.id
                """,
                (von, bis),
            )

            return await cursor.fetchall()

@app.get("/wartungsplan/ueberfaellig")
async def ueberfaellige_wartungen():
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    wp.id AS wartungsplan_id,
                    wp.datum,
                    CURRENT_DATE - wp.datum AS tage_ueberfaellig,
                    g.seriennummer,
                    g.hersteller,
                    g.typ,
                    t.id AS techniker_id,
                    t.name AS techniker_name,
                    s.id AS standort_id,
                    s.plz,
                    s.stadt,
                    s.strasse,
                    s.hausnummer
                FROM wartungsplan AS wp
                JOIN geraet AS g
                    ON g.seriennummer = wp.geraet_seriennummer
                JOIN techniker AS t
                    ON t.id = wp.techniker_id
                JOIN standort AS s
                    ON s.id = g.standort_id
                WHERE wp.datum < CURRENT_DATE
                  AND NOT EXISTS (
                      SELECT 1
                      FROM wartung AS w
                      WHERE w.wartungsplan_id = wp.id
                  )
                ORDER BY wp.datum, wp.id
                """
            )

            return await cursor.fetchall()
@app.get("/techniker")
async def techniker_lesen():
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    t.id,
                    t.name,
                    ARRAY(
                        SELECT st.standort_id
                        FROM standort_techniker AS st
                        WHERE st.techniker_id = t.id
                        ORDER BY st.standort_id
                    ) AS standort_ids,
                    ARRAY(
                        SELECT tt.geraetetyp
                        FROM typ_techniker AS tt
                        WHERE tt.techniker_id = t.id
                        ORDER BY tt.geraetetyp
                    ) AS geraetetypen
                FROM techniker AS t
                ORDER BY t.name, t.id
                """
            )

            return await cursor.fetchall()


async def zuständigkeiten_speichern(cursor, techniker_id, daten):
    # Wird innerhalb derselben Transaktion wie INSERT/UPDATE ausgeführt.
    await cursor.execute(
        "DELETE FROM standort_techniker WHERE techniker_id = %s",
        (techniker_id,),
    )

    await cursor.execute(
        "DELETE FROM typ_techniker WHERE techniker_id = %s",
        (techniker_id,),
    )

    for standort_id in daten.standort_ids:
        await cursor.execute(
            """
            INSERT INTO standort_techniker (standort_id, techniker_id)
            VALUES (%s, %s)
            """,
            (standort_id, techniker_id),
        )

    for geraetetyp in daten.geraetetypen:
        await cursor.execute(
            """
            INSERT INTO typ_techniker (geraetetyp, techniker_id)
            VALUES (%s, %s)
            """,
            (geraetetyp, techniker_id),
        )

@app.post(
    "/wartungen",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def wartung_anlegen(wartung: WartungCreate):
    try:
        async with pool.connection() as connection:
            async with connection.cursor(row_factory=dict_row) as cursor:
                if wartung.wartungsplan_id is not None:
                    await cursor.execute(
                        """
                        SELECT id
                        FROM wartungsplan
                        WHERE id = %s
                          AND geraet_seriennummer = %s
                          AND techniker_id = %s
                        """,
                        (
                            wartung.wartungsplan_id,
                            wartung.geraet_seriennummer,
                            wartung.techniker_id,
                        ),
                    )

                    if await cursor.fetchone() is None:
                        raise HTTPException(
                            status_code=422,
                            detail=(
                                "Wartungsplan passt nicht zu Gerät "
                                "und Techniker"
                            ),
                        )

                    await cursor.execute(
                        """
                        SELECT id
                        FROM wartung
                        WHERE wartungsplan_id = %s
                        """,
                        (wartung.wartungsplan_id,),
                    )

                    if await cursor.fetchone() is not None:
                        raise HTTPException(
                            status_code=409,
                            detail="Diese geplante Wartung wurde bereits durchgeführt",
                        )

                await cursor.execute(
                    """
                    INSERT INTO wartung (
                        datum,
                        ersatzgeraet,
                        geraet_seriennummer,
                        techniker_id,
                        wartungsplan_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        wartung.datum,
                        wartung.ersatzgeraet,
                        wartung.geraet_seriennummer,
                        wartung.techniker_id,
                        wartung.wartungsplan_id,
                    ),
                )

                return await cursor.fetchone()

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Gerät, Techniker oder Wartungsplan existiert nicht",
        ) from error

@app.post(
    "/geraete",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def geraet_anlegen(geraet: GeraetCreate):
    try:
        async with pool.connection() as connection:
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(
                    """
                    INSERT INTO geraet (
                        seriennummer,
                        hersteller,
                        typ,
                        wartungsintervall,
                        standort_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        geraet.seriennummer,
                        geraet.hersteller,
                        geraet.typ,
                        geraet.wartungsintervall,
                        geraet.standort_id,
                    ),
                )

                return await cursor.fetchone()

    except UniqueViolation as error:
        raise HTTPException(
            status_code=409,
            detail="Ein Gerät mit dieser Seriennummer existiert bereits",
        ) from error

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Der angegebene Standort existiert nicht",
        ) from error

@app.post(
    "/wartungsplan",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def wartung_planen(wartungsplan: WartungsplanCreate):
    try:
        async with pool.connection() as connection:
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(
                    """
                    INSERT INTO wartungsplan (
                        datum,
                        geraet_seriennummer,
                        techniker_id
                    )
                    VALUES (%s, %s, %s)
                    RETURNING *
                    """,
                    (
                        wartungsplan.datum,
                        wartungsplan.geraet_seriennummer,
                        wartungsplan.techniker_id,
                    ),
                )

                return await cursor.fetchone()

    except UniqueViolation as error:
        raise HTTPException(
            status_code=409,
            detail="Für dieses Gerät ist an diesem Datum bereits eine Wartung geplant",
        ) from error

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Gerät oder Techniker existiert nicht",
        ) from error

@app.post(
    "/standorte",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def standort_anlegen(standort: StandortCreate):
    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                INSERT INTO standort (
                    plz,
                    stadt,
                    strasse,
                    hausnummer
                )
                VALUES (%s, %s, %s, %s)
                RETURNING
                    id,
                    plz,
                    stadt,
                    strasse,
                    hausnummer
                """,
                (
                    standort.plz,
                    standort.stadt,
                    standort.strasse,
                    standort.hausnummer,
                ),
            )

            return await cursor.fetchone()

@app.post(
    "/techniker",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def techniker_anlegen(daten: TechnikerEingabe):
    try:
        async with pool.connection() as connection:
            async with connection.transaction():
                async with connection.cursor(row_factory=dict_row) as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO techniker (name)
                        VALUES (%s)
                        RETURNING id
                        """,
                        (daten.name,),
                    )

                    techniker = await cursor.fetchone()
                    techniker_id = techniker["id"]

                    await zuständigkeiten_speichern(
                        cursor, techniker_id, daten
                    )

        return {"id": techniker_id, **daten.model_dump()}

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Mindestens ein ausgewählter Standort existiert nicht",
        ) from error


@app.put(
    "/techniker/{techniker_id}",
    dependencies=[Depends(require_api_key)],
)
async def techniker_aendern(
    techniker_id: int,
    daten: TechnikerEingabe,
):
    try:
        async with pool.connection() as connection:
            async with connection.transaction():
                async with connection.cursor(row_factory=dict_row) as cursor:
                    # UPDATE sperrt den Techniker für gleichzeitige Änderungen.
                    await cursor.execute(
                        """
                        UPDATE techniker
                        SET name = %s
                        WHERE id = %s
                        RETURNING id
                        """,
                        (daten.name, techniker_id),
                    )

                    if await cursor.fetchone() is None:
                        raise HTTPException(
                            status_code=404,
                            detail="Techniker nicht gefunden",
                        )

                    await zuständigkeiten_speichern(
                        cursor, techniker_id, daten
                    )

        return {"id": techniker_id, **daten.model_dump()}

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Mindestens ein ausgewählter Standort existiert nicht",
        ) from error
@app.put(
    "/wartungsplan/{wartungsplan_id}",
    dependencies=[Depends(require_api_key)],
)
async def wartungsplan_aendern(
    wartungsplan_id: int,
    aenderung: WartungsplanUpdate,
):
    try:
        async with pool.connection() as connection:
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(
                    """
                    UPDATE wartungsplan
                    SET datum = %s,
                        techniker_id = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        aenderung.datum,
                        aenderung.techniker_id,
                        wartungsplan_id,
                    ),
                )

                ergebnis = await cursor.fetchone()

                if ergebnis is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Wartungsplan nicht gefunden",
                    )

                return ergebnis

    except UniqueViolation as error:
        raise HTTPException(
            status_code=409,
            detail="Für dieses Gerät ist an diesem Datum bereits eine Wartung geplant",
        ) from error

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Techniker existiert nicht",
        ) from error

@app.patch(
    "/geraete/{seriennummer}",
    dependencies=[Depends(require_api_key)],
)
async def geraet_aendern(
    seriennummer: str,
    aenderung: GeraetPatch,
):
    werte = aenderung.model_dump(exclude_unset=True)

    erlaubte_spalten = {
        "hersteller",
        "typ",
        "wartungsintervall",
        "standort_id",
    }

    unbekannte_spalten = set(werte) - erlaubte_spalten
    if unbekannte_spalten:
        raise HTTPException(
            status_code=422,
            detail="Ungültige Felder angegeben",
        )

    zuweisungen = [
        sql.SQL("{} = %s").format(sql.Identifier(spalte))
        for spalte in werte
    ]

    anweisung = sql.SQL(
        """
        UPDATE geraet
        SET {zuweisungen}
        WHERE seriennummer = %s
        RETURNING *
        """
    ).format(
        zuweisungen=sql.SQL(", ").join(zuweisungen)
    )

    parameter: list[Any] = list(werte.values())
    parameter.append(seriennummer)

    try:
        async with pool.connection() as connection:
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(anweisung, parameter)
                ergebnis = await cursor.fetchone()

                if ergebnis is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Gerät nicht gefunden",
                    )

                return ergebnis

    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=422,
            detail="Der angegebene Standort existiert nicht",
        ) from error

@app.delete(
    "/wartungsplan/{wartungsplan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def wartungsplan_loeschen(wartungsplan_id: int):
    async with pool.connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM wartungsplan
                WHERE id = %s
                RETURNING id
                """,
                (wartungsplan_id,),
            )

            if await cursor.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Wartungsplan nicht gefunden",
                )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/statistik/wartungen-pro-techniker")
async def wartungen_pro_techniker(
    von: date = Query(alias="von"),
    bis: date = Query(alias="bis"),
):
    pruefe_zeitraum(von, bis)

    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    t.id AS techniker_id,
                    t.name AS techniker_name,
                    COUNT(w.id) AS anzahl_wartungen
                FROM techniker AS t
                LEFT JOIN wartung AS w
                    ON w.techniker_id = t.id
                   AND w.datum BETWEEN %s AND %s
                GROUP BY t.id, t.name
                ORDER BY anzahl_wartungen DESC, t.name
                """,
                (von, bis),
            )

            return await cursor.fetchall()

@app.get("/statistik/wartungen-pro-standort")
async def wartungen_pro_standort(
    von: date = Query(alias="von"),
    bis: date = Query(alias="bis"),
):
    pruefe_zeitraum(von, bis)

    async with pool.connection() as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                SELECT
                    s.id AS standort_id,
                    s.plz,
                    s.stadt,
                    s.strasse,
                    s.hausnummer,

                    COUNT(DISTINCT w.id) AS durchgefuehrte_wartungen,

                    COUNT(DISTINCT wp.id) FILTER (
                        WHERE w_plan.id IS NULL
                    ) AS geplante_offene_wartungen

                FROM standort AS s

                LEFT JOIN geraet AS g
                    ON g.standort_id = s.id

                LEFT JOIN wartung AS w
                    ON w.geraet_seriennummer = g.seriennummer
                   AND w.datum BETWEEN %s AND %s

                LEFT JOIN wartungsplan AS wp
                    ON wp.geraet_seriennummer = g.seriennummer
                   AND wp.datum BETWEEN %s AND %s

                LEFT JOIN wartung AS w_plan
                    ON w_plan.wartungsplan_id = wp.id

                GROUP BY
                    s.id,
                    s.plz,
                    s.stadt,
                    s.strasse,
                    s.hausnummer

                ORDER BY
                    durchgefuehrte_wartungen DESC,
                    geplante_offene_wartungen DESC,
                    s.stadt
                """,
                (von, bis, von, bis),
            )

            return await cursor.fetchall()

