//! `GET /api/celdas`: el valor anual de cada celda dentro de Perú (mapa de color), sin promediar por
//! departamento: el promedio mezcla costa, Andes y selva.
//!
//! Hay tres mallas: temperatura (`t2m`, NASA POWER), lluvia (`valor`, NASA POWER) y vegetación
//! (`valor`, NDVI de MODIS a 0,25°). La temperatura conserva `t2m` para no romper el contrato.
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// `data/celdas/{variable}.json`, tal cual lo dejan `pipeline/power.py` y `pipeline/vegetacion_malla.py`.
#[derive(Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct Malla {
    #[schema(example = "MERRA-2 vía NASA POWER (T2M)")]
    pub fuente: String,
    /// `°C` (temperatura), `mm/año` (lluvia) o `NDVI` (vegetación).
    #[schema(example = "°C")]
    pub unidad: String,
    /// Cómo leer la malla (solo vegetación: el NDVI se satura en la selva).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub nota: Option<String>,
    /// Alto de la celda en grados de latitud.
    #[schema(example = 0.5)]
    pub dlat: f64,
    /// Ancho de la celda en grados de longitud.
    #[schema(example = 0.625)]
    pub dlon: f64,
    pub anio_inicio: u16,
    pub anio_fin: u16,
    pub celdas: Vec<Celda>,
}

/// Una celda trae `t2m` (temperatura) o `valor` (lluvia y vegetación), nunca los dos.
#[derive(Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct Celda {
    /// Centro de la celda.
    pub lat: f64,
    pub lon: f64,
    /// Solo temperatura: media anual en °C, una por año de `anio_inicio` a `anio_fin`; null si el
    /// año no está completo.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub t2m: Option<Vec<Option<f64>>>,
    /// Lluvia (mm/año) y vegetación (NDVI): un valor por año de `anio_inicio` a `anio_fin`; null si
    /// falta el año.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub valor: Option<Vec<Option<f64>>>,
}
