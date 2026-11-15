//! Lo que la API devuelve cuando no es un modelo completo.
use crate::models::{
    power::Region,
    zona::{Stats, Zona},
};
use serde::Serialize;
use utoipa::ToSchema;

#[derive(Serialize)]
pub struct RegionResumen {
    pub region: String,
    pub lat: f64,
    pub lon: f64,
}

impl From<&Region> for RegionResumen {
    fn from(r: &Region) -> Self {
        Self {
            region: r.region.clone(),
            lat: r.lat,
            lon: r.lon,
        }
    }
}

#[derive(Serialize, ToSchema)]
pub struct Punto {
    pub anio: u16,
    pub valor: f64,
}

/// `GET /api/zonas/{id}`: los campos de `Zona` (con su `stats`) más la serie anual del mismo periodo.
/// Campos explícitos y no `flatten`: `Zona` lleva `additionalProperties: false` (por `deny_unknown_fields`)
/// y un `allOf` contradiría el contrato. Un test comprueba que no se desincronicen.
#[derive(Serialize, ToSchema)]
pub struct ZonaDetalle<'a> {
    pub id: &'a str,
    pub nombre: &'a str,
    pub lat: f64,
    pub lon: f64,
    pub celdas: u32,
    /// Aviso si el promedio es poco fiable (menos de 4 celdas): mostrarlo en la ficha.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub nota: Option<&'a str>,
    pub variable: &'static str,
    pub unidad: &'a str,
    pub fuente: &'a str,
    pub serie: &'a [Punto],
    pub stats: &'a Stats,
}

impl<'a> ZonaDetalle<'a> {
    pub fn new(
        z: &'a Zona,
        variable: &'static str,
        unidad: &'a str,
        fuente: &'a str,
        serie: &'a [Punto],
    ) -> Self {
        Self {
            id: &z.id,
            nombre: &z.nombre,
            lat: z.lat,
            lon: z.lon,
            celdas: z.celdas,
            nota: z.nota.as_deref(),
            variable,
            unidad,
            fuente,
            serie,
            stats: &z.stats,
        }
    }
}

/// Cuerpo de los errores 400 y 404.
#[derive(Serialize, ToSchema)]
pub struct ErrorRespuesta {
    pub error: String,
}
