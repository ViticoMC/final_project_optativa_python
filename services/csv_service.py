import csv
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from app.config import DELIMITER, ENCODING
from app.exceptions import CsvFormatError, ExportError


class CsvService:
    def __init__(self, encoding: str = ENCODING, delimiter: str = DELIMITER) -> None:
        if len(delimiter) != 1:
            raise ValueError("El delimitador debe ser un único carácter.")
        self.encoding = encoding
        self.delimiter = delimiter

    def leer(
        self,
        ruta: str | Path,
        columnas_requeridas: Iterable[str] = (),
        columna_id: str | None = None,
    ) -> list[dict[str, str]]:
        archivo = Path(ruta)
        if not archivo.is_file():
            raise CsvFormatError(
                "El archivo no existe o no es un archivo de texto.", archivo
            )

        try:
            with archivo.open(encoding=self.encoding, newline="") as fh:
                return self._leer_fichero(
                    fh, archivo, list(columnas_requeridas), columna_id
                )
        except CsvFormatError:
            raise
        except UnicodeDecodeError as exc:
            raise CsvFormatError(
                f"No se pudo decodificar el archivo con la codificación {self.encoding}.",
                archivo,
            ) from exc
        except csv.Error as exc:
            raise CsvFormatError(
                f"El archivo contiene un CSV mal formado: {exc}.", archivo
            ) from exc
        except OSError as exc:
            raise CsvFormatError(
                f"No se pudo leer el archivo: {exc}.", archivo
            ) from exc

    def _leer_fichero(
        self,
        fh,
        archivo: Path,
        columnas_requeridas: Sequence[str],
        columna_id: str | None,
    ) -> list[dict[str, str]]:
        lector = csv.reader(fh, delimiter=self.delimiter)
        cabecera_cruda = next(lector, None)
        if cabecera_cruda is None:
            raise CsvFormatError("El archivo está vacío.", archivo)

        cabecera = [self._limpiar_cabecera(columna) for columna in cabecera_cruda]
        requeridas = list(dict.fromkeys(columnas_requeridas))
        if columna_id is not None and columna_id not in requeridas:
            requeridas.append(columna_id)
        self._validar_cabecera(cabecera, requeridas, archivo)

        registros: list[dict[str, str]] = []
        lineas_por_id: dict[str, int] = {}

        for fila in lector:
            linea = lector.line_num
            if not fila or all(not (valor or "").strip() for valor in fila):
                continue
            if len(fila) != len(cabecera):
                raise CsvFormatError(
                    f"La fila tiene {len(fila)} columnas y se esperaban "
                    f"{len(cabecera)}.",
                    archivo,
                    linea,
                )

            registro = {
                columna: self._limpiar(valor)
                for columna, valor in zip(cabecera, fila)
            }

            if columna_id is not None:
                identificador = registro[columna_id]
                if not identificador:
                    raise CsvFormatError(
                        f"El campo '{columna_id}' no puede estar vacío.",
                        archivo,
                        linea,
                    )
                if identificador in lineas_por_id:
                    raise CsvFormatError(
                        f"Identificador duplicado '{identificador}'; ya apareció "
                        f"en la línea {lineas_por_id[identificador]}.",
                        archivo,
                        linea,
                    )
                lineas_por_id[identificador] = linea

            registros.append(registro)

        return registros

    @staticmethod
    def _validar_cabecera(
        cabecera: Sequence[str],
        requeridas: Sequence[str],
        archivo: Path,
    ) -> None:
        if not cabecera or not any(cabecera):
            raise CsvFormatError("El encabezado está vacío.", archivo)
        if any(not columna for columna in cabecera):
            raise CsvFormatError(
                "El encabezado contiene columnas sin nombre.", archivo
            )
        if len(cabecera) != len(set(cabecera)):
            raise CsvFormatError(
                "El encabezado contiene columnas duplicadas.", archivo
            )

        faltantes = [columna for columna in requeridas if columna not in cabecera]
        if faltantes:
            raise CsvFormatError(
                "Faltan columnas obligatorias: " + ", ".join(faltantes) + ".",
                archivo,
            )

    @staticmethod
    def _limpiar(valor: str | None) -> str:
        return "" if valor is None else valor.strip()

    @staticmethod
    def _limpiar_cabecera(valor: str | None) -> str:
        if valor is None:
            return ""
        return valor.lstrip("\ufeff").strip()

    def escribir(
        self,
        ruta: str | Path,
        columnas: Sequence[str],
        filas: Iterable[Mapping[str, object]],
    ) -> Path:
        archivo = Path(ruta)
        columnas_limpias = [str(columna).strip() for columna in columnas]

        if not columnas_limpias:
            raise ExportError("Debe indicar al menos una columna para exportar.")
        if any(not columna for columna in columnas_limpias):
            raise ExportError("Las columnas de exportación no pueden estar vacías.")
        if len(columnas_limpias) != len(set(columnas_limpias)):
            raise ExportError("Las columnas de exportación están duplicadas.")

        registros = list(filas)
        for numero, fila in enumerate(registros, start=1):
            if not isinstance(fila, Mapping):
                raise ExportError(
                    f"La fila {numero} no es un diccionario de columnas."
                )
            faltantes = [
                columna for columna in columnas_limpias if columna not in fila
            ]
            if faltantes:
                raise ExportError(
                    f"La fila {numero} no contiene las columnas: "
                    + ", ".join(faltantes)
                    + "."
                )

        temporal: Path | None = None
        try:
            archivo.parent.mkdir(parents=True, exist_ok=True)
            modo = (
                archivo.stat().st_mode & 0o777
                if archivo.exists()
                else 0o644
            )
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding=self.encoding,
                newline="",
                dir=archivo.parent,
                prefix=f".{archivo.name}.",
                suffix=".tmp",
                delete=False,
            ) as fh:
                temporal = Path(fh.name)
                escritor = csv.DictWriter(
                    fh,
                    fieldnames=columnas_limpias,
                    delimiter=self.delimiter,
                    lineterminator="\n",
                    quoting=csv.QUOTE_MINIMAL,
                    extrasaction="raise",
                )
                escritor.writeheader()
                for fila in registros:
                    escritor.writerow(
                        {
                            columna: self._serializar(fila[columna])
                            for columna in columnas_limpias
                        }
                    )
            os.chmod(temporal, modo)
            os.replace(temporal, archivo)
            temporal = None
        except (OSError, csv.Error) as exc:
            raise ExportError(
                f"No se pudo escribir el archivo '{archivo}': {exc}."
            ) from exc
        finally:
            if temporal is not None and temporal.exists():
                temporal.unlink(missing_ok=True)

        return archivo

    @staticmethod
    def _serializar(valor: object) -> str:
        if valor is None:
            return ""
        if isinstance(valor, (list, tuple)):
            return "; ".join(str(elemento) for elemento in valor)
        return str(valor)
