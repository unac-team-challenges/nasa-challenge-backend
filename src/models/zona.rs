//! Forma de `data/zonas/{variable}.json` (lo escribe `pipeline/tendencias.py`).
//! El mismo struct se lee del archivo y se devuelve en `/api/zonas`: la API no cambia ningún valor.
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// Semáforo de la tendencia.
#[derive(Clone, Copy, Debug, PartialEq, Deserialize, Serialize, ToSchema)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Real,
    PosibleCasualidad,
    PocosDatos,
}

/// Tendencia lineal del periodo `year_start`–`year_end`, ya calculada por el pipeline.
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct Stats {
    pub year_start: u16,
    pub year_end: u16,
    pub n_years: u16,
    /// Unidad de la variable por década.
    pub slope_per_decade: f64,
    /// En años calendario: `valor ≈ intercept + slope_per_decade / 10 × año`.
    pub intercept: f64,
    /// Intervalo del 95 % de la pendiente, por década.
    pub ci_low: f64,
    pub ci_high: f64,
    /// Antes de Benjamini-Hochberg.
    pub p_value: f64,
    /// Después de Benjamini-Hochberg.
    pub q_value: f64,
    /// Autocorrelación de orden 1.
    pub lag1: f64,
    /// Solo lluvia.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pct_change_per_decade: Option<f64>,
    pub status: Status,
    /// Cuidado al interpretar la tendencia: siempre en `lluvia_imerg` (salto de 2014) y si `lag1 > 0.5`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub aviso: Option<String>,
}

/// `GET /api/zonas`: una zona del mapa con su tendencia (sin serie).
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct Zona {
    /// Ubigeo como texto: "01"–"25".
    pub id: String,
    pub nombre: String,
    pub lat: f64,
    pub lon: f64,
    /// Celdas de la malla de la fuente que entran en el promedio.
    pub celdas: u32,
    /// Aviso si el promedio es poco fiable (menos de 4 celdas): mostrarlo en la ficha.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub nota: Option<String>,
    pub stats: Stats,
}
