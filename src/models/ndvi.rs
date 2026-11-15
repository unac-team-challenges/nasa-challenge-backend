//! Forma de `data/ndvi_departamentos.json` (NDVI anual por departamento, de la malla de vegetación).
//! Si el JSON no encaja, la API no arranca.
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Medidas {
    /// NDVI anual (MODIS MOD13A3), promedio de las celdas de 0,25° del departamento.
    pub ndvi: f64,
}

pub type Region = super::Region<Medidas>;
