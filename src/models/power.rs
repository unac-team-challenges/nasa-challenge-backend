//! Forma de `data/power.json`. Si el JSON no encaja, la API no arranca.
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Medidas {
    /// Lluvia corregida, mm/día.
    #[serde(rename = "PRECTOTCORR")]
    pub prectotcorr: f64,
    /// Temperatura a 2 m, °C.
    #[serde(rename = "T2M")]
    pub t2m: f64,
    /// Temperatura máxima a 2 m, °C.
    #[serde(rename = "T2M_MAX")]
    pub t2m_max: f64,
    /// Temperatura mínima a 2 m, °C.
    #[serde(rename = "T2M_MIN")]
    pub t2m_min: f64,
}

pub type Region = super::Region<Medidas>;
