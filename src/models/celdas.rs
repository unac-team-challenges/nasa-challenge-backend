//! `GET /api/celdas`: la T2M anual de cada celda de NASA POWER dentro de Perú (mapa de calor).
//! Sin promediar por departamento: el promedio mezcla costa, Andes y selva.
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// `data/celdas/temperatura.json`, tal cual lo deja `pipeline/power.py`.
#[derive(Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct Malla {
    #[schema(example = "MERRA-2 vía NASA POWER (T2M)")]
    pub fuente: String,
    #[schema(example = "°C")]
    pub unidad: String,
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

#[derive(Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct Celda {
    /// Centro de la celda.
    pub lat: f64,
    pub lon: f64,
    /// Media anual en °C, una por año de `anio_inicio` a `anio_fin`; null si el año no está completo.
    pub t2m: Vec<Option<f64>>,
}
