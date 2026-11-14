use crate::models::{gpm, power};
use std::{collections::HashMap, sync::Arc};

// JSON ya procesados por pipeline/. La API nunca calcula en vivo.
const POWER: &str = include_str!("../data/power.json");
const GPM: &str = include_str!("../data/gpm.json");

pub type Estado = Arc<Datos>;

pub struct Datos {
    pub regiones: Vec<power::Region>,
    pub gpm: Vec<gpm::Region>,
    indice: HashMap<String, usize>,
    indice_gpm: HashMap<String, usize>,
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

fn indexar<M>(regiones: &[crate::models::Region<M>]) -> HashMap<String, usize> {
    regiones.iter().enumerate().map(|(i, r)| (clave(&r.region), i)).collect()
}

impl Datos {
    pub fn cargar() -> Result<Self, serde_json::Error> {
        Self::desde_json(POWER, GPM)
    }

    pub fn desde_json(power: &str, gpm: &str) -> Result<Self, serde_json::Error> {
        let regiones: Vec<power::Region> = serde_json::from_str(power)?;
        let gpm: Vec<gpm::Region> = serde_json::from_str(gpm)?;
        Ok(Self { indice: indexar(&regiones), indice_gpm: indexar(&gpm), regiones, gpm })
    }

    pub fn buscar(&self, nombre: &str) -> Option<&power::Region> {
        self.indice.get(&clave(nombre)).map(|&i| &self.regiones[i])
    }

    pub fn buscar_gpm(&self, nombre: &str) -> Option<&gpm::Region> {
        self.indice_gpm.get(&clave(nombre)).map(|&i| &self.gpm[i])
    }
}
