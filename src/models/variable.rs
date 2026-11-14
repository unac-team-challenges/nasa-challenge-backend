//! Variables que ve el producto (contrato del Drive, `07-stack-decidido`).
use serde::Serialize;

#[derive(Clone, Copy, Debug, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Variable {
    Lluvia,
    Temperatura,
}

impl Variable {
    pub const TODAS: [Variable; 2] = [Variable::Lluvia, Variable::Temperatura];

    pub fn parse(s: &str) -> Option<Self> {
        Self::TODAS.into_iter().find(|v| v.id() == s.trim().to_lowercase())
    }
    pub fn id(self) -> &'static str {
        match self {
            Variable::Lluvia => "lluvia",
            Variable::Temperatura => "temperatura",
        }
    }
    pub fn unidad(self) -> &'static str {
        match self {
            Variable::Lluvia => "mm/día",
            Variable::Temperatura => "°C",
        }
    }
    pub fn fuente(self) -> &'static str {
        match self {
            Variable::Lluvia => "GPM IMERG v07 (NASA)",
            Variable::Temperatura => "MERRA-2 vía NASA POWER (T2M)",
        }
    }
    pub fn descripcion(self) -> &'static str {
        match self {
            Variable::Lluvia => "Lluvia: promedio diario de cada año",
            Variable::Temperatura => "Temperatura del aire a 2 m: promedio de cada año",
        }
    }
}
