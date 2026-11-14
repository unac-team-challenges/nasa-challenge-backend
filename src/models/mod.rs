pub mod gpm;
pub mod power;
pub mod variable;

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Forma común de todos los `data/*.json`: una región con sus años.
/// `M` son las medidas de cada año (varía según la fuente).
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Region<M> {
    pub region: String,
    pub lat: f64,
    pub lon: f64,
    /// Celdas de la malla que entran en el promedio del departamento.
    pub celdas: u32,
    /// Aviso cuando el promedio es poco fiable (menos de 4 celdas).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub nota: Option<String>,
    /// Promedio anual por año ("2015", ...).
    pub anios: BTreeMap<String, M>,
}
