use crate::models::power::Region;
use std::{collections::HashMap, sync::Arc};

// JSON ya procesado por pipeline/power.py. La API nunca calcula en vivo.
const POWER: &str = include_str!("../data/power.json");

pub type Estado = Arc<Datos>;

pub struct Datos {
    pub regiones: Vec<Region>,
    indice: HashMap<String, usize>,
}

/// Minúsculas y sin tildes: "Áncash" == "ancash".
pub fn clave(s: &str) -> String {
    s.trim()
        .chars()
        .flat_map(char::to_lowercase)
        .map(|c| match c {
            'á' => 'a',
            'é' => 'e',
            'í' => 'i',
            'ó' => 'o',
            'ú' | 'ü' => 'u',
            'ñ' => 'n',
            c => c,
        })
        .collect()
}

impl Datos {
    pub fn cargar() -> Result<Self, serde_json::Error> {
        Self::desde_json(POWER)
    }

    pub fn desde_json(json: &str) -> Result<Self, serde_json::Error> {
        let regiones: Vec<Region> = serde_json::from_str(json)?;
        let indice = regiones.iter().enumerate().map(|(i, r)| (clave(&r.region), i)).collect();
        Ok(Self { regiones, indice })
    }

    pub fn buscar(&self, nombre: &str) -> Option<&Region> {
        self.indice.get(&clave(nombre)).map(|&i| &self.regiones[i])
    }
}
