//! Forma de `data/ndvi.json` (lo escribe `pipeline/ndvi.py`): vegetación de los valles irrigados
//! de la costa (Caso 2). El mismo struct se lee del archivo y se devuelve en `/api/vegetacion`:
//! la API no recalcula ni redondea ningún valor.
use crate::models::recuadro::zona_recuadro;
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// Medidas de un año completo (12 meses válidos).
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct AnioVegetacion {
    pub anio: u16,
    /// NDVI medio del año en el recuadro (−1 a 1).
    pub ndvi_anual: f64,
    /// Área con NDVI medio del año mayor que `umbral_verde_ndvi`, en km².
    pub area_verde_km2: f64,
}

zona_recuadro! {
    /// `GET /api/vegetacion`: una zona (recuadro sobre un valle) con su serie anual y su tendencia.
    ZonaVegetacion, AnioVegetacion, umbral_verde_ndvi;
    id: "Identificador del recuadro, p. ej. \"chavimochic\".",
    tipo: "P. ej. \"valle irrigado\" o, en Olmos, \"riego nuevo y bosque seco\".",
    pixeles: "Píxeles MODIS (~1 km) del recuadro.",
    umbral: "NDVI desde el que un píxel cuenta como área verde.",
    tendencia_de: "Sobre qué campo de `serie` se calcula `stats` (hoy, \"ndvi_anual\").",
    serie: "Un punto por año, de menor a mayor (como `serie` de `/api/zonas/{id}`): solo años completos.",
}
