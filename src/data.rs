use crate::{
    models::{
        gpm, power,
        variable::{Variable, VariableInfo},
        zona::Zona,
        Region,
    },
    schema::Punto,
    ubigeo::UBIGEOS,
};
use serde::de::Error as _;
use std::{
    collections::{BTreeSet, HashMap},
    sync::Arc,
};

// JSON ya procesados por pipeline/. La API nunca calcula en vivo.
const POWER: &str = include_str!("../data/power.json");
const GPM: &str = include_str!("../data/gpm.json");
const VARIABLES: &str = include_str!("../data/variables.json");
const ZONAS_LLUVIA: &str = include_str!("../data/zonas/lluvia.json");
const ZONAS_TEMPERATURA: &str = include_str!("../data/zonas/temperatura.json");

pub type Estado = Arc<Datos>;

/// Los JSON de entrada. En los tests: `Fuentes { gpm: otro, ..Fuentes::EMBEBIDAS }`.
#[derive(Clone, Copy)]
pub struct Fuentes<'a> {
    pub power: &'a str,
    pub gpm: &'a str,
    pub variables: &'a str,
    /// `data/zonas/{variable}.json`, en el orden de `Variable::TODAS`.
    pub zonas: [&'a str; 2],
}

impl Fuentes<'static> {
    pub const EMBEBIDAS: Self = Self {
        power: POWER,
        gpm: GPM,
        variables: VARIABLES,
        zonas: [ZONAS_LLUVIA, ZONAS_TEMPERATURA],
    };
}

/// Una zona con su serie ya recortada al periodo de su `stats`.
pub struct Ficha {
    pub zona: Zona,
    pub serie: Vec<Punto>,
}

pub struct Datos {
    pub regiones: Vec<power::Region>,
    pub gpm: Vec<gpm::Region>,
    indice: HashMap<String, usize>,
    indice_gpm: HashMap<String, usize>,
    /// En el orden de `Variable::TODAS`.
    pub variables: Vec<VariableInfo>,
    /// Por variable; ids "01"–"25" en orden.
    fichas: [Vec<Ficha>; 2],
}

fn error(msg: impl std::fmt::Display) -> serde_json::Error {
    serde_json::Error::custom(msg)
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

fn indexar<M>(regiones: &[Region<M>]) -> HashMap<String, usize> {
    regiones
        .iter()
        .enumerate()
        .map(|(i, r)| (clave(&r.region), i))
        .collect()
}

impl Datos {
    pub fn cargar() -> Result<Self, serde_json::Error> {
        Self::desde(Fuentes::EMBEBIDAS)
    }

    /// Lee y valida todo de una vez: si algo no encaja, la API no arranca.
    pub fn desde(f: Fuentes) -> Result<Self, serde_json::Error> {
        let regiones: Vec<power::Region> = serde_json::from_str(f.power)?;
        let gpm: Vec<gpm::Region> = serde_json::from_str(f.gpm)?;
        let (indice, indice_gpm) = (indexar(&regiones), indexar(&gpm));
        if indice.keys().collect::<BTreeSet<_>>() != indice_gpm.keys().collect::<BTreeSet<_>>() {
            return Err(error("power.json y gpm.json no tienen las mismas regiones"));
        }
        let variables: Vec<VariableInfo> = serde_json::from_str(f.variables)?;
        if !variables
            .iter()
            .map(|v| v.id.as_str())
            .eq(Variable::TODAS.map(Variable::id))
        {
            return Err(error(
                "variables.json debe tener exactamente: lluvia, temperatura",
            ));
        }
        let mut d = Self {
            indice,
            indice_gpm,
            regiones,
            gpm,
            variables,
            fichas: Default::default(),
        };
        d.fichas = [
            d.fichas_de(Variable::Lluvia, f.zonas[0])?,
            d.fichas_de(Variable::Temperatura, f.zonas[1])?,
        ];
        Ok(d)
    }

    /// Lee `zonas/{v}.json` y lo cruza con `variables.json`, los ubigeos y `power.json`/`gpm.json`.
    fn fichas_de(&self, v: Variable, json: &str) -> Result<Vec<Ficha>, serde_json::Error> {
        let zonas: Vec<Zona> = serde_json::from_str(json)?;
        if zonas.len() != UBIGEOS.len() {
            return Err(error(format_args!(
                "zonas/{}.json: {} zonas, se esperaban {}",
                v.id(),
                zonas.len(),
                UBIGEOS.len()
            )));
        }
        let info = &self.variables[v as usize];
        zonas
            .into_iter()
            .zip(UBIGEOS)
            .map(|(zona, (id, nombre))| {
                let donde = || format!("zonas/{}.json, zona '{}'", v.id(), zona.id);
                if zona.id != id || clave(&zona.nombre) != clave(nombre) {
                    return Err(error(format_args!("{}: se esperaba {id} ({nombre}) en ese orden", donde())));
                }
                let st = &zona.stats;
                // Cada zona tiene su periodo (años completos); variables.json guarda el más amplio.
                if st.year_start < info.anio_inicio || st.year_end > info.anio_fin {
                    return Err(error(format_args!("{}: el periodo de stats se sale del de variables.json", donde())));
                }
                let serie = match v {
                    Variable::Lluvia => self.buscar_gpm(nombre).map(|r| serie_de(&zona, r, |m| m.lluvia_mm_dia)),
                    Variable::Temperatura => self.buscar(nombre).map(|r| serie_de(&zona, r, |m| m.t2m)),
                };
                let serie = serie
                    .ok_or_else(|| error(format_args!("{}: no está en power.json/gpm.json", donde())))?
                    .ok_or_else(|| error(format_args!("{}: lat, lon, celdas o nota no coinciden con su fuente", donde())))?;
                let anios = (serie.first().map(|p| p.anio), serie.last().map(|p| p.anio));
                if serie.len() != usize::from(st.n_years) || anios != (Some(st.year_start), Some(st.year_end)) {
                    return Err(error(format_args!(
                        "{}: stats dice {}–{} ({} años) pero la serie de su fuente en ese periodo va de {:?} a {:?} ({} años)",
                        donde(), st.year_start, st.year_end, st.n_years, anios.0, anios.1, serie.len()
                    )));
                }
                Ok(Ficha { zona, serie })
            })
            .collect()
    }

    /// Las 25 zonas de una variable, en orden de ubigeo.
    pub fn zonas(&self, v: Variable) -> impl Iterator<Item = &Zona> {
        self.fichas[v as usize].iter().map(|f| &f.zona)
    }

    /// Zona por ubigeo exacto ("07", no "7").
    pub fn ficha(&self, v: Variable, id: &str) -> Option<&Ficha> {
        self.fichas[v as usize].iter().find(|f| f.zona.id == id)
    }

    /// Unidad, fuente y periodo de una variable.
    pub fn variable(&self, v: Variable) -> &VariableInfo {
        &self.variables[v as usize]
    }

    pub fn buscar(&self, nombre: &str) -> Option<&power::Region> {
        self.indice.get(&clave(nombre)).map(|&i| &self.regiones[i])
    }

    pub fn buscar_gpm(&self, nombre: &str) -> Option<&gpm::Region> {
        self.indice_gpm.get(&clave(nombre)).map(|&i| &self.gpm[i])
    }
}

/// Serie de la fuente recortada al periodo de `stats`; `None` si la zona no describe la misma región
/// (otra `lat`, `lon`, `celdas` o `nota`): una sola verdad para `/api/*` y `/power`, `/gpm`.
fn serie_de<M>(zona: &Zona, r: &Region<M>, valor: impl Fn(&M) -> f64) -> Option<Vec<Punto>> {
    if (zona.lat, zona.lon, zona.celdas, &zona.nota) != (r.lat, r.lon, r.celdas, &r.nota) {
        return None;
    }
    let periodo = zona.stats.year_start..=zona.stats.year_end;
    Some(
        r.anios
            .iter()
            .filter_map(|(a, m)| {
                Some(Punto {
                    anio: a.parse().ok()?,
                    valor: valor(m),
                })
            })
            .filter(|p| periodo.contains(&p.anio))
            .collect(),
    )
}
