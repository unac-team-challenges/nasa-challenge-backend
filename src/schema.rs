//! Lo que la API devuelve cuando no es un modelo completo.
use crate::models::power::Region;
use serde::Serialize;

#[derive(Serialize)]
pub struct RegionResumen {
    pub region: String,
    pub lat: f64,
    pub lon: f64,
}

impl From<&Region> for RegionResumen {
    fn from(r: &Region) -> Self {
        Self { region: r.region.clone(), lat: r.lat, lon: r.lon }
    }
}
