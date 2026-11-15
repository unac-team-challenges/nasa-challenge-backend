//! Variables que ve el producto (contrato del Drive, `07-stack-decidido`).
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

// El orden es el de `data/variables.json` y `TODAS`: `v as usize` es su índice en `Datos`.
#[derive(Clone, Copy, Debug, PartialEq, Serialize, ToSchema)]
#[serde(rename_all = "snake_case")]
pub enum Variable {
    /// Lluvia principal (NASA POWER).
    Lluvia,
    Temperatura,
    /// Lluvia de IMERG: segunda fuente, para comparar con `lluvia`. No va en el selector.
    LluviaImerg,
    /// Vegetación: NDVI anual de MODIS, promedio de las celdas de 0,25° del departamento.
    Vegetacion,
}

impl Variable {
    pub const TODAS: [Variable; 4] = [
        Variable::Lluvia,
        Variable::Temperatura,
        Variable::LluviaImerg,
        Variable::Vegetacion,
    ];

    pub fn parse(s: &str) -> Option<Self> {
        // Los ids son ASCII: comparar sin mayúsculas evita un `String` por variable.
        let s = s.trim();
        Self::TODAS
            .into_iter()
            .find(|v| v.id().eq_ignore_ascii_case(s))
    }
    pub fn id(self) -> &'static str {
        match self {
            Variable::Lluvia => "lluvia",
            Variable::Temperatura => "temperatura",
            Variable::LluviaImerg => "lluvia_imerg",
            Variable::Vegetacion => "vegetacion",
        }
    }
}

// `v as usize` indexa los arrays de `Datos` y `Fuentes`: si alguien reordena el enum o `TODAS`, no compila.
const _: () = {
    let mut i = 0;
    while i < Variable::TODAS.len() {
        assert!(Variable::TODAS[i] as usize == i);
        i += 1;
    }
};

/// `GET /api/variables`: una entrada de `data/variables.json`, tal cual.
#[derive(Clone, Debug, Deserialize, Serialize, ToSchema)]
#[serde(deny_unknown_fields)]
pub struct VariableInfo {
    pub id: String,
    pub unidad: String,
    pub fuente: String,
    pub descripcion: String,
    pub anio_inicio: u16,
    pub anio_fin: u16,
}
