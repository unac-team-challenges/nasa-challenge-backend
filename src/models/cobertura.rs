//! Forma de `data/cobertura_arboles.json` (lo escribe `pipeline/cobertura.py`): cobertura de árboles
//! de la selva (MODIS MOD44B), donde el NDVI se satura. El mismo struct se lee del archivo y se
//! devuelve en `/api/cobertura-arboles`: la API no recalcula ni redondea ningún valor.
use crate::models::zona::Stats;
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// Medidas de un año (MOD44B es un producto anual).
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct AnioCobertura {
    pub anio: u16,
    /// Cobertura de árboles media del recuadro, en % (0–100).
    pub arboles_pct: f64,
    /// Área con cobertura de árboles mayor o igual que `umbral_bosque_pct`, en km².
    pub area_bosque_km2: f64,
}

/// `GET /api/cobertura-arboles`: una zona (recuadro de selva) con su serie anual y su tendencia.
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct ZonaCobertura {
    /// Identificador del recuadro, p. ej. "la-pampa".
    pub id: String,
    pub nombre: String,
    /// Departamento donde está el recuadro.
    pub departamento: String,
    /// Ubigeo del departamento, como texto ("01"–"25").
    pub ubigeo: String,
    /// P. ej. "selva con minería de oro".
    pub tipo: String,
    /// Qué área se promedia: un recuadro, **no** el departamento. La ficha debe mostrarlo.
    pub unidad_geografica: String,
    /// `[oeste, sur, este, norte]` en grados.
    pub bbox: [f64; 4],
    pub lat: f64,
    pub lon: f64,
    /// Píxeles MODIS (~250 m) de tierra del recuadro.
    pub pixeles: u32,
    pub fuente: String,
    /// % de cobertura de árboles desde el que un píxel cuenta como bosque.
    pub umbral_bosque_pct: f64,
    /// Sobre qué campo de `serie` se calcula `stats` (hoy, "arboles_pct").
    pub tendencia_de: String,
    /// Un punto por año, de menor a mayor (como `serie` de `/api/zonas/{id}`).
    pub serie: Vec<AnioCobertura>,
    pub stats: Stats,
}
