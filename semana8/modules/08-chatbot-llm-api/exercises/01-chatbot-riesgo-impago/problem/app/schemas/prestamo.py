from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# TODO: clase PrestamoEntrada (BaseModel) con las 6 variables del modelo, con sus rangos (ver enunciado).
#       Debe rechazar campos que no existan.
class PrestamoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edad: int = Field(ge=18, le=75, description='Edad del solicitante en anios')
    ingresos_mensuales: float = Field(gt=0, description='Ingresos netos mensuales')
    importe_prestamo: float = Field(gt=0, description='Import solicitado en Euros')
    plazo_meses: int = Field(ge=6, le=84, description='Plazo de devolucion en meses')
    antiguedad_laboral_anios: int = Field(ge=0, le=50, description='Antiguedad laboral en anios del solicitante')
    impagos_previos: int = Field(ge=0, le=20, description='Cantidad de impagos previos por el solicitante')

    # TODO: field_validator (con classmethod) para antiguedad_laboral_anios: no puede ser incoherente con la edad.
    @field_validator("antiguedad_laboral_anios", mode="before")
    @classmethod
    def validar_antiguedad_laboral(cls, valor, info):
        print(info)
        edad = info.data.get("edad")
        if edad is not None and valor > (edad - 16):
            raise ValueError("La antigüedad laboral no es coherente con la edad.")
        return valor


# TODO: clase PrediccionSalida con probabilidad_impago (entre 0 y 1) y decision (aprobar, revisar o rechazar).
class PrediccionSalida(BaseModel):
    model_config =  ConfigDict(extra="forbid")

    probabilidad_impago: float = Field(ge=0, le=1)
    decision: Literal['aprobar','revisar','rechazar']