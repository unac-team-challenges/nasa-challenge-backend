//! Forma de `data/cobertura_arboles.json` (lo escribe `pipeline/cobertura.py`): cobertura de árboles
//! de la selva (MODIS MOD44B), donde el NDVI se satura. El mismo struct se lee del archivo y se
//! devuelve en `/api/cobertura-arboles`: la API no recalcula ni redondea ningún valor.
use crate::models::recuadro::zona_recuadro;
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

zona_recuadro! {
    /// `GET /api/cobertura-arboles`: una zona (recuadro de selva) con su serie anual y su tendencia.
    ZonaCobertura, AnioCobertura, umbral_bosque_pct;
    id: "Identificador del recuadro, p. ej. \"la-pampa\".",
    tipo: "P. ej. \"selva con minería de oro\".",
    pixeles: "Píxeles MODIS (~250 m) de tierra del recuadro.",
    umbral: "% de cobertura de árboles desde el que un píxel cuenta como bosque.",
    tendencia_de: "Sobre qué campo de `serie` se calcula `stats` (hoy, \"arboles_pct\").",
    serie: "Un punto por año, de menor a mayor (como `serie` de `/api/zonas/{id}`).",
}
