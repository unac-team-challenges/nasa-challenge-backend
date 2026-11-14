use crate::models::{gpm, power, variable::Variable};
use serde::de::Error as _;
use std::{
    collections::{BTreeSet, HashMap},
    sync::Arc,
};

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
        let (indice, indice_gpm) = (indexar(&regiones), indexar(&gpm));
        if indice.keys().collect::<BTreeSet<_>>() != indice_gpm.keys().collect::<BTreeSet<_>>() {
            return Err(serde_json::Error::custom("power.json y gpm.json no tienen las mismas regiones"));
        }
        Ok(Self { indice, indice_gpm, regiones, gpm })
    }

    pub fn buscar(&self, nombre: &str) -> Option<&power::Region> {
        self.indice.get(&clave(nombre)).map(|&i| &self.regiones[i])
    }

    pub fn buscar_gpm(&self, nombre: &str) -> Option<&gpm::Region> {
        self.indice_gpm.get(&clave(nombre)).map(|&i| &self.gpm[i])
    }

    /// Aviso de la fuente de la variable (menos de 4 celdas); `None` si no hay.
    pub fn nota(&self, v: Variable, region: &str) -> Option<&str> {
        match v {
            Variable::Lluvia => self.buscar_gpm(region)?.nota.as_deref(),
            Variable::Temperatura => self.buscar(region)?.nota.as_deref(),
        }
    }

    /// Serie anual (año, valor) de una variable en una región; `None` si la región no existe.
    pub fn serie(&self, v: Variable, region: &str) -> Option<Vec<(u16, f64)>> {
        fn anios<M>(r: &crate::models::Region<M>, f: impl Fn(&M) -> f64) -> Vec<(u16, f64)> {
            r.anios.iter().filter_map(|(a, m)| Some((a.parse().ok()?, f(m)))).collect()
        }
        match v {
            Variable::Lluvia => self.buscar_gpm(region).map(|r| anios(r, |m| m.lluvia_mm_dia)),
            Variable::Temperatura => self.buscar(region).map(|r| anios(r, |m| m.t2m)),
        }
    }
}
