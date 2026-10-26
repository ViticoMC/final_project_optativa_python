import re
import unicodedata

_PATRON_HORA = re.compile(r"^\s*(\d{1,2}):(\d{2})")


def normalizar_texto(texto: object) -> str:
    """Convierte a minúsculas, elimina tildes y normaliza espacios."""
    if texto is None:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    sin_tildes = "".join(
        caracter for caracter in descompuesto if not unicodedata.combining(caracter)
    )
    return " ".join(sin_tildes.casefold().split())


def contiene(texto: object, consulta: object) -> bool:
    """Búsqueda textual sin distinguir mayúsculas, tildes ni espacios extra."""
    consulta_normalizada = normalizar_texto(consulta)
    if not consulta_normalizada:
        return True
    return consulta_normalizada in normalizar_texto(texto)


def dividir_lista(campo: object, separador: str = ";") -> tuple[str, ...]:
    """Divide un campo separado por punto y coma, omitiendo elementos vacíos."""
    if campo is None:
        return ()
    return tuple(
        parte.strip()
        for parte in str(campo).split(separador)
        if parte.strip()
    )


def a_entero(valor: object, defecto: int = 0) -> int:
    """Convierte un valor a entero y devuelve ``defecto`` si no es posible."""
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return defecto


def clave_horario(valor: object) -> tuple[int, str]:
    """Clave de orden: primero horas válidas y después valores especiales."""
    texto = "" if valor is None else str(valor).strip()
    coincidencia = _PATRON_HORA.match(texto)
    if coincidencia:
        hora = int(coincidencia.group(1))
        minuto = int(coincidencia.group(2))
        if 0 <= hora <= 23 and 0 <= minuto <= 59:
            return (0, f"{hora:02d}:{minuto:02d}")
    return (1, normalizar_texto(texto))
