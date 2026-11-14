pub mod gpm;
pub mod power;
pub mod variable;

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Forma común de todos los `data/*.json`: una región con sus años.
/// `M` son las medidas de cada año (varía según la fuente).
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Region<M> {
    pub region: String,
    pub lat: f64,
    pub lon: f64,
    /// Promedio anual por año ("2015", ...).
    pub anios: BTreeMap<String, M>,
}
