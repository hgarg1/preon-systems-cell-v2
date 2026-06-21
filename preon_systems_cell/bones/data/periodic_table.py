from __future__ import annotations

_ELEMENTS: dict[str, dict] = {
    "H":  {"symbol": "H",  "name": "Hydrogen",   "atomic_number": 1,  "atomic_mass": 1.008,   "group": 1,  "period": 1},
    "HE": {"symbol": "He", "name": "Helium",      "atomic_number": 2,  "atomic_mass": 4.003,   "group": 18, "period": 1},
    "LI": {"symbol": "Li", "name": "Lithium",     "atomic_number": 3,  "atomic_mass": 6.941,   "group": 1,  "period": 2},
    "BE": {"symbol": "Be", "name": "Beryllium",   "atomic_number": 4,  "atomic_mass": 9.012,   "group": 2,  "period": 2},
    "B":  {"symbol": "B",  "name": "Boron",       "atomic_number": 5,  "atomic_mass": 10.811,  "group": 13, "period": 2},
    "C":  {"symbol": "C",  "name": "Carbon",      "atomic_number": 6,  "atomic_mass": 12.011,  "group": 14, "period": 2},
    "N":  {"symbol": "N",  "name": "Nitrogen",    "atomic_number": 7,  "atomic_mass": 14.007,  "group": 15, "period": 2},
    "O":  {"symbol": "O",  "name": "Oxygen",      "atomic_number": 8,  "atomic_mass": 15.999,  "group": 16, "period": 2},
    "F":  {"symbol": "F",  "name": "Fluorine",    "atomic_number": 9,  "atomic_mass": 18.998,  "group": 17, "period": 2},
    "NE": {"symbol": "Ne", "name": "Neon",        "atomic_number": 10, "atomic_mass": 20.180,  "group": 18, "period": 2},
    "NA": {"symbol": "Na", "name": "Sodium",      "atomic_number": 11, "atomic_mass": 22.990,  "group": 1,  "period": 3},
    "MG": {"symbol": "Mg", "name": "Magnesium",   "atomic_number": 12, "atomic_mass": 24.305,  "group": 2,  "period": 3},
    "AL": {"symbol": "Al", "name": "Aluminum",    "atomic_number": 13, "atomic_mass": 26.982,  "group": 13, "period": 3},
    "SI": {"symbol": "Si", "name": "Silicon",     "atomic_number": 14, "atomic_mass": 28.086,  "group": 14, "period": 3},
    "P":  {"symbol": "P",  "name": "Phosphorus",  "atomic_number": 15, "atomic_mass": 30.974,  "group": 15, "period": 3},
    "S":  {"symbol": "S",  "name": "Sulfur",      "atomic_number": 16, "atomic_mass": 32.065,  "group": 16, "period": 3},
    "CL": {"symbol": "Cl", "name": "Chlorine",    "atomic_number": 17, "atomic_mass": 35.453,  "group": 17, "period": 3},
    "AR": {"symbol": "Ar", "name": "Argon",       "atomic_number": 18, "atomic_mass": 39.948,  "group": 18, "period": 3},
    "K":  {"symbol": "K",  "name": "Potassium",   "atomic_number": 19, "atomic_mass": 39.098,  "group": 1,  "period": 4},
    "CA": {"symbol": "Ca", "name": "Calcium",     "atomic_number": 20, "atomic_mass": 40.078,  "group": 2,  "period": 4},
    "SC": {"symbol": "Sc", "name": "Scandium",    "atomic_number": 21, "atomic_mass": 44.956,  "group": 3,  "period": 4},
    "TI": {"symbol": "Ti", "name": "Titanium",    "atomic_number": 22, "atomic_mass": 47.867,  "group": 4,  "period": 4},
    "V":  {"symbol": "V",  "name": "Vanadium",    "atomic_number": 23, "atomic_mass": 50.942,  "group": 5,  "period": 4},
    "CR": {"symbol": "Cr", "name": "Chromium",    "atomic_number": 24, "atomic_mass": 51.996,  "group": 6,  "period": 4},
    "MN": {"symbol": "Mn", "name": "Manganese",   "atomic_number": 25, "atomic_mass": 54.938,  "group": 7,  "period": 4},
    "FE": {"symbol": "Fe", "name": "Iron",        "atomic_number": 26, "atomic_mass": 55.845,  "group": 8,  "period": 4},
    "CO": {"symbol": "Co", "name": "Cobalt",      "atomic_number": 27, "atomic_mass": 58.933,  "group": 9,  "period": 4},
    "NI": {"symbol": "Ni", "name": "Nickel",      "atomic_number": 28, "atomic_mass": 58.693,  "group": 10, "period": 4},
    "CU": {"symbol": "Cu", "name": "Copper",      "atomic_number": 29, "atomic_mass": 63.546,  "group": 11, "period": 4},
    "ZN": {"symbol": "Zn", "name": "Zinc",        "atomic_number": 30, "atomic_mass": 65.38,   "group": 12, "period": 4},
    "GA": {"symbol": "Ga", "name": "Gallium",     "atomic_number": 31, "atomic_mass": 69.723,  "group": 13, "period": 4},
    "GE": {"symbol": "Ge", "name": "Germanium",   "atomic_number": 32, "atomic_mass": 72.630,  "group": 14, "period": 4},
    "AS": {"symbol": "As", "name": "Arsenic",     "atomic_number": 33, "atomic_mass": 74.922,  "group": 15, "period": 4},
    "SE": {"symbol": "Se", "name": "Selenium",    "atomic_number": 34, "atomic_mass": 78.971,  "group": 16, "period": 4},
    "BR": {"symbol": "Br", "name": "Bromine",     "atomic_number": 35, "atomic_mass": 79.904,  "group": 17, "period": 4},
    "KR": {"symbol": "Kr", "name": "Krypton",     "atomic_number": 36, "atomic_mass": 83.798,  "group": 18, "period": 4},
    "AG": {"symbol": "Ag", "name": "Silver",      "atomic_number": 47, "atomic_mass": 107.868, "group": 11, "period": 5},
    "SN": {"symbol": "Sn", "name": "Tin",         "atomic_number": 50, "atomic_mass": 118.710, "group": 14, "period": 5},
    "I":  {"symbol": "I",  "name": "Iodine",      "atomic_number": 53, "atomic_mass": 126.904, "group": 17, "period": 5},
    "XE": {"symbol": "Xe", "name": "Xenon",       "atomic_number": 54, "atomic_mass": 131.293, "group": 18, "period": 5},
    "PT": {"symbol": "Pt", "name": "Platinum",    "atomic_number": 78, "atomic_mass": 195.084, "group": 10, "period": 6},
    "AU": {"symbol": "Au", "name": "Gold",        "atomic_number": 79, "atomic_mass": 196.967, "group": 11, "period": 6},
    "HG": {"symbol": "Hg", "name": "Mercury",     "atomic_number": 80, "atomic_mass": 200.592, "group": 12, "period": 6},
    "PB": {"symbol": "Pb", "name": "Lead",        "atomic_number": 82, "atomic_mass": 207.200, "group": 14, "period": 6},
    "BI": {"symbol": "Bi", "name": "Bismuth",     "atomic_number": 83, "atomic_mass": 208.980, "group": 15, "period": 6},
    "U":  {"symbol": "U",  "name": "Uranium",     "atomic_number": 92, "atomic_mass": 238.029, "group": 3,  "period": 7},
}

_BY_NUMBER: dict[int, dict] = {d["atomic_number"]: d for d in _ELEMENTS.values()}
_BY_NAME: dict[str, dict] = {d["name"].upper(): d for d in _ELEMENTS.values()}


def lookup(payload: dict) -> dict:
    query = str(payload.get("element", "")).strip()
    try:
        data = _BY_NUMBER.get(int(query))
        if data:
            return dict(data)
        return {"error": f"no element with atomic number {query}"}
    except ValueError:
        pass
    key = query.upper()
    data = _ELEMENTS.get(key) or _BY_NAME.get(key)
    if data:
        return dict(data)
    return {"error": f"element not found: {query!r}"}
