//! Forma de `data/gpm.json` (lluvia GPM IMERG). Si el JSON no encaja, la API no arranca.
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Medidas {
    /// Lluvia IMERG, mm/día.
    pub lluvia_mm_dia: f64,
}

pub type Region = super::Region<Medidas>;
