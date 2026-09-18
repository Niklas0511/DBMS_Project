import os
from datetime import date

import requests


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")


def set_api_key(api_key: str):
    global API_KEY
    API_KEY = api_key.strip()


def _headers():
    if not API_KEY:
        return {}
    return {"X-API-Key": API_KEY}


def _datum_wert(wert: date | str) -> str:
    if isinstance(wert, date):
        return wert.isoformat()
    return wert


# ---------------------------------------------------------
# GET-Endpunkte
# ---------------------------------------------------------

def get_Wartungsplan_Techniker(techniker_id: int):
    response = requests.get(
        f"{BASE_URL}/techniker/{techniker_id}/wartungsplan",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_GeraetWartungen(seriennummer: str):
    response = requests.get(
        f"{BASE_URL}/geraete/{seriennummer}/wartungen",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_Geraet(seriennummer: str):
    response = requests.get(
        f"{BASE_URL}/geraete/{seriennummer}",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_StandortGeraete(standort_id: int):
    response = requests.get(
        f"{BASE_URL}/standorte/{standort_id}/geraete",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_Wartungsplan(von: date | str, bis: date | str):
    response = requests.get(
        f"{BASE_URL}/wartungsplan",
        params={
            "von": _datum_wert(von),
            "bis": _datum_wert(bis),
        },
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_WartungsplanUeberfaellige():
    response = requests.get(
        f"{BASE_URL}/wartungsplan/ueberfaellig",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_Statistik_Wartungen_pro_Techniker(
    von: date | str,
    bis: date | str,
):
    response = requests.get(
        f"{BASE_URL}/statistik/wartungen-pro-techniker",
        params={
            "von": _datum_wert(von),
            "bis": _datum_wert(bis),
        },
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_Statistik_Wartungen_pro_Standort(
    von: date | str,
    bis: date | str,
):
    response = requests.get(
        f"{BASE_URL}/statistik/wartungen-pro-standort",
        params={
            "von": _datum_wert(von),
            "bis": _datum_wert(bis),
        },
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

def get_Standorte():
    response = requests.get(
        f"{BASE_URL}/standorte",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

def get_Techniker():
    response = requests.get(
        f"{BASE_URL}/techniker",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

# ---------------------------------------------------------
# POST-Endpunkte
# ---------------------------------------------------------

def post_Wartung(
    datum: date | str,
    ersatzgeraet: str | None,
    geraet_seriennummer: str,
    techniker_id: int,
    wartungsplan_id: int | None,
):
    payload = {
        "datum": _datum_wert(datum),
        "ersatzgeraet": ersatzgeraet or None,
        "geraet_seriennummer": geraet_seriennummer,
        "techniker_id": techniker_id,
        "wartungsplan_id": wartungsplan_id,
    }

    response = requests.post(
        f"{BASE_URL}/wartungen",
        json=payload,
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def post_Geraet(
    seriennummer: str,
    hersteller: str,
    typ: str,
    wartungsintervall: int,
    standort_id: int,
):
    payload = {
        "seriennummer": seriennummer,
        "hersteller": hersteller,
        "typ": typ,
        "wartungsintervall": wartungsintervall,
        "standort_id": standort_id,
    }

    response = requests.post(
        f"{BASE_URL}/geraete",
        json=payload,
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def post_Wartungsplan(
    datum: date | str,
    geraet_seriennummer: str,
    techniker_id: int,
):
    payload = {
        "datum": _datum_wert(datum),
        "geraet_seriennummer": geraet_seriennummer,
        "techniker_id": techniker_id,
    }

    response = requests.post(
        f"{BASE_URL}/wartungsplan",
        json=payload,
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()



def post_Standort(
    plz: str,
    stadt: str,
    strasse: str,
    hausnummer: str,
):
    payload = {
        "plz": plz,
        "stadt": stadt,
        "strasse": strasse,
        "hausnummer": hausnummer,
    }

    response = requests.post(
        f"{BASE_URL}/standorte",
        json=payload,
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

def post_Techniker(
    name: str,
    standort_ids: list[int],
    geraetetypen: list[str],
):
    response = requests.post(
        f"{BASE_URL}/techniker",
        json={
            "name": name,
            "standort_ids": standort_ids,
            "geraetetypen": geraetetypen,
        },
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()
# ---------------------------------------------------------
# PUT / PATCH / DELETE
# ---------------------------------------------------------

def put_Wartungsplan(
    wartungsplan_id: int,
    datum: date | str,
    techniker_id: int,
):
    payload = {
        "datum": _datum_wert(datum),
        "techniker_id": techniker_id,
    }

    response = requests.put(
        f"{BASE_URL}/wartungsplan/{wartungsplan_id}",
        json=payload,
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()

def put_Techniker(
    techniker_id: int,
    name: str,
    standort_ids: list[int],
    geraetetypen: list[str],
):
    response = requests.put(
        f"{BASE_URL}/techniker/{techniker_id}",
        json={
            "name": name,
            "standort_ids": standort_ids,
            "geraetetypen": geraetetypen,
        },
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def patch_Geraet(
    seriennummer: str,
    *,
    hersteller: str | None = None,
    typ: str | None = None,
    wartungsintervall: int | None = None,
    standort_id: int | None = None,
):
    payload = {}

    if hersteller is not None:
        payload["hersteller"] = hersteller
    if typ is not None:
        payload["typ"] = typ
    if wartungsintervall is not None:
        payload["wartungsintervall"] = wartungsintervall
    if standort_id is not None:
        payload["standort_id"] = standort_id

    response = requests.patch(
        f"{BASE_URL}/geraete/{seriennummer}",
        json=payload,
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def delete_Wartungsplan(wartungsplan_id: int):
    response = requests.delete(
        f"{BASE_URL}/wartungsplan/{wartungsplan_id}",
        headers=_headers(),
        timeout=5,
    )
    response.raise_for_status()