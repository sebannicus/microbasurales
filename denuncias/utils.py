import requests


def obtener_zona_por_coordenadas(lat, lon):
    """
    Devuelve la zona usando principalmente el 'suburb' del reverse geocoding.
    Si no existe suburb, usa un fallback básico.
    """
    try:
        url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?format=json&lat={lat}&lon={lon}&addressdetails=1"
        )
        headers = {"User-Agent": "microbasurales-app/1.0"}
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code != 200:
            return "Zona desconocida"

        data = res.json()
        address = data.get("address", {})

        # Prioridad máxima: suburb
        suburb = address.get("suburb")
        if suburb and suburb.strip():
            return suburb.strip()

        # Fallback
        posibles = [
            address.get("neighbourhood"),
            address.get("city"),
            address.get("town"),
            address.get("village"),
            address.get("municipality"),
            address.get("state"),
        ]

        for zona in posibles:
            if zona and zona.strip():
                return zona.strip()

        return "Zona desconocida"

    except Exception:
        return "Zona desconocida"
