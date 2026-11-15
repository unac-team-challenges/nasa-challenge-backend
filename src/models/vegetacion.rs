//! Forma de `data/ndvi.json` (lo escribe `pipeline/ndvi.py`): vegetación de los valles irrigados
//! de la costa (Caso 2). El mismo struct se lee del archivo y se devuelve en `/api/vegetacion`:
//! la API no recalcula ni redondea ningún valor.
use crate::models::zona::Stats;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use utoipa::ToSchema;

/// Medidas de un año completo (12 meses válidos).
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct AnioVegetacion {
    /// NDVI medio del año en el recuadro (−1 a 1).
    pub ndvi_anual: f64,
    /// Área con NDVI medio del año mayor que `umbral_verde_ndvi`, en km².
    pub area_verde_km2: f64,
}

/// `GET /api/vegetacion`: una zona (recuadro sobre un valle) con su serie anual y su tendencia.
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct ZonaVegetacion {
    /// Identificador del recuadro, p. ej. "chavimochic".
    pub id: String,
    pub nombre: String,
    /// Departamento donde está el recuadro.
    pub departamento: String,
    /// Ubigeo del departamento, como texto ("01"–"25").
    pub ubigeo: String,
    /// P. ej. "valle irrigado".
    pub tipo: String,
    /// Qué área se promedia: un recuadro, **no** el departamento. La ficha debe mostrarlo.
    pub unidad_geografica: String,
    /// `[oeste, sur, este, norte]` en grados.
    pub bbox: [f64; 4],
    pub lat: f64,
    pub lon: f64,
    /// Píxeles MODIS (~1 km) del recuadro.
    pub pixeles: u32,
    pub fuente: String,
    /// NDVI desde el que un píxel cuenta como área verde.
    pub umbral_verde_ndvi: f64,
    /// Sobre qué campo de `anios` se calcula `stats` (hoy, "ndvi_anual").
    pub tendencia_de: String,
    /// Por año ("2001", ...): solo años completos.
    #[schema(value_type = BTreeMap<String, AnioVegetacion>)]
    pub anios: BTreeMap<String, AnioVegetacion>,
    pub stats: Stats,
}
