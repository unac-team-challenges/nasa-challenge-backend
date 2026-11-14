//! Lo que la API devuelve cuando no es un modelo completo.
use crate::models::power::Region;
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
        Self { region: r.region.clone(), lat: r.lat, lon: r.lon }
    }
}

/// `GET /api/variables`
#[derive(Serialize, ToSchema)]
pub struct VariableInfo {
    pub id: &'static str,
    pub unidad: &'static str,
    pub fuente: &'static str,
    pub descripcion: &'static str,
    pub anio_inicio: Option<u16>,
    pub anio_fin: Option<u16>,
}

/// `GET /api/zonas`: una zona del mapa (sin serie).
#[derive(Serialize, ToSchema)]
pub struct Zona {
    /// Ubigeo como texto: "01"–"25".
    pub id: &'static str,
    pub nombre: String,
    pub lat: f64,
    pub lon: f64,
}

#[derive(Serialize, ToSchema)]
pub struct Punto {
    pub anio: u16,
    pub valor: f64,
}

/// `GET /api/zonas/{id}`: serie anual de la zona. `stats` (tendencia) llega con el cálculo de Sebastian.
#[derive(Serialize, ToSchema)]
pub struct ZonaDetalle {
    pub id: &'static str,
    pub nombre: String,
    pub lat: f64,
    pub lon: f64,
    pub variable: &'static str,
    pub unidad: &'static str,
    pub fuente: &'static str,
    /// Aviso si el promedio es poco fiable (menos de 4 celdas): mostrarlo en la ficha.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub nota: Option<String>,
    pub serie: Vec<Punto>,
}

/// Cuerpo de los errores 400 y 404.
#[derive(Serialize, ToSchema)]
pub struct ErrorRespuesta {
    pub error: String,
}
