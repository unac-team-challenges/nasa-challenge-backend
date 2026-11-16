use crate::{
    models::{
        Region,
        celdas::Malla,
        cobertura::ZonaCobertura,
        gpm, ndvi, power,
        recuadro::Comunes,
        variable::{Variable, VariableInfo},
        vegetacion::ZonaVegetacion,
        zona::Zona,
    },
    schema::Punto,
    ubigeo::UBIGEOS,
};
use axum::body::Bytes;
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
const ZONAS_LLUVIA_IMERG: &str = include_str!("../data/zonas/lluvia_imerg.json");
const NDVI: &str = include_str!("../data/ndvi.json");
const COBERTURA: &str = include_str!("../data/cobertura_arboles.json");
const ZONAS_VEGETACION: &str = include_str!("../data/zonas/vegetacion.json");
const NDVI_DEPARTAMENTOS: &str = include_str!("../data/ndvi_departamentos.json");
const CELDAS_LLUVIA: &str = include_str!("../data/celdas/lluvia.json");
const CELDAS_TEMPERATURA: &str = include_str!("../data/celdas/temperatura.json");
const CELDAS_VEGETACION: &str = include_str!("../data/celdas/vegetacion.json");

pub type Estado = Arc<Datos>;

/// Los JSON de entrada. En los tests: `Fuentes { gpm: otro, ..Fuentes::EMBEBIDAS }`.
#[derive(Clone, Copy)]
pub struct Fuentes<'a> {
    pub power: &'a str,
    pub gpm: &'a str,
    pub variables: &'a str,
    /// `data/zonas/{variable}.json`, en el orden de `Variable::TODAS`.
    pub zonas: [&'a str; 4],
    /// `data/ndvi_departamentos.json`: NDVI anual por departamento (fuente de `zonas/vegetacion.json`).
    pub ndvi_departamentos: &'a str,
    /// `data/ndvi.json`: vegetación de los valles irrigados (Caso 2).
    pub ndvi: &'a str,
    /// `data/cobertura_arboles.json`: cobertura de árboles de la selva.
    pub cobertura: &'a str,
    /// `data/celdas/{variable}.json` en el orden de `Variable::TODAS`; `None` = sin malla (IMERG).
    pub celdas: [Option<&'a str>; 4],
}

impl Fuentes<'static> {
    pub const EMBEBIDAS: Self = Self {
        power: POWER,
        gpm: GPM,
        variables: VARIABLES,
        zonas: [
            ZONAS_LLUVIA,
            ZONAS_TEMPERATURA,
            ZONAS_LLUVIA_IMERG,
            ZONAS_VEGETACION,
        ],
        ndvi_departamentos: NDVI_DEPARTAMENTOS,
        ndvi: NDVI,
        cobertura: COBERTURA,
        celdas: [
            Some(CELDAS_LLUVIA),
            Some(CELDAS_TEMPERATURA),
            None,
            Some(CELDAS_VEGETACION),
        ],
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
    pub ndvi: Vec<ndvi::Region>,
    indice_ndvi: HashMap<String, usize>,
    /// En el orden de `Variable::TODAS`.
    pub variables: Vec<VariableInfo>,
    /// Por variable; ids "01"–"25" en orden.
    fichas: [Vec<Ficha>; 4],
    /// `data/ndvi.json` tal cual, ya validado.
    pub vegetacion: Vec<ZonaVegetacion>,
    /// `data/cobertura_arboles.json` tal cual, ya validado.
    pub cobertura: Vec<ZonaCobertura>,
    /// Mallas ya validadas, en el orden de `Variable::TODAS` (vacía = sin malla); se sirven tal
    /// cual (clonar `Bytes` no copia).
    celdas: [Bytes; 4],
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
        let ndvi: Vec<ndvi::Region> = serde_json::from_str(f.ndvi_departamentos)?;
        let (indice, indice_gpm, indice_ndvi) = (indexar(&regiones), indexar(&gpm), indexar(&ndvi));
        let nombres = indice.keys().collect::<BTreeSet<_>>();
        if nombres != indice_gpm.keys().collect::<BTreeSet<_>>()
            || nombres != indice_ndvi.keys().collect::<BTreeSet<_>>()
        {
            return Err(error(
                "power.json, gpm.json y ndvi_departamentos.json no tienen las mismas regiones",
            ));
        }
        let variables: Vec<VariableInfo> = serde_json::from_str(f.variables)?;
        if !variables
            .iter()
            .map(|v| v.id.as_str())
            .eq(Variable::TODAS.map(Variable::id))
        {
            return Err(error(
                "variables.json debe tener exactamente: lluvia, temperatura, lluvia_imerg, vegetacion",
            ));
        }
        let mut d = Self {
            indice,
            indice_gpm,
            indice_ndvi,
            regiones,
            gpm,
            ndvi,
            variables,
            fichas: Default::default(),
            vegetacion: recuadros(f.ndvi)?,
            cobertura: recuadros(f.cobertura)?,
            celdas: Default::default(),
        };
        d.fichas = [
            d.fichas_de(Variable::Lluvia, f.zonas[0])?,
            d.fichas_de(Variable::Temperatura, f.zonas[1])?,
            d.fichas_de(Variable::LluviaImerg, f.zonas[2])?,
            d.fichas_de(Variable::Vegetacion, f.zonas[3])?,
        ];
        for (v, json) in Variable::TODAS.into_iter().zip(f.celdas) {
            if let Some(json) = json {
                d.validar_celdas(v, json)?;
                d.celdas[v as usize] = Bytes::copy_from_slice(json.as_bytes());
            }
        }
        Ok(d)
    }

    /// La malla de una variable, tal cual (`None` si no tiene).
    pub fn celdas(&self, v: Variable) -> Option<Bytes> {
        let b = &self.celdas[v as usize];
        (!b.is_empty()).then(|| b.clone())
    }

    /// La malla debe caber en Perú, en el periodo de su variable y con valores físicos de esa variable.
    fn validar_celdas(&self, v: Variable, json: &str) -> Result<(), serde_json::Error> {
        // (unidad, campo, rango físico): la temperatura conserva `t2m`; las demás usan `valor`.
        let (unidad, con_t2m, rango) = match v {
            Variable::Temperatura => ("°C", true, -40.0..=50.0),
            Variable::Lluvia => ("mm/año", false, 0.0..=12_000.0),
            Variable::Vegetacion => ("NDVI", false, -0.2..=1.0),
            Variable::LluviaImerg => return Err(error("lluvia_imerg no tiene malla por celdas")),
        };
        let m: Malla = serde_json::from_str(json)?;
        let info = &self.variables[v as usize];
        let anios = usize::from(m.anio_fin.saturating_sub(m.anio_inicio)) + 1;
        let falla = |msg: String| Err(error(format_args!("celdas/{}.json: {msg}", v.id())));
        if m.celdas.is_empty() {
            return falla("sin celdas".into());
        }
        if m.anio_inicio > m.anio_fin
            || m.anio_inicio < info.anio_inicio
            || m.anio_fin > info.anio_fin
        {
            return falla(format!(
                "{}–{} se sale del periodo de variables.json",
                m.anio_inicio, m.anio_fin
            ));
        }
        if m.unidad != unidad || m.fuente.trim().is_empty() {
            return falla(format!("falta la fuente o la unidad no es {unidad}"));
        }
        if !(m.dlat > 0.0 && m.dlon > 0.0) {
            return falla("dlat y dlon deben ser > 0".into());
        }
        let campo = if con_t2m { "t2m" } else { "valor" };
        for c in &m.celdas {
            let donde = format!("celda ({}, {})", c.lat, c.lon);
            // Caja de Perú con margen de media celda
            if !(-18.6..=0.1).contains(&c.lat) || !(-81.7..=-68.4).contains(&c.lon) {
                return falla(format!("{donde} fuera de Perú"));
            }
            let (propio, ajeno) = if con_t2m {
                (&c.t2m, &c.valor)
            } else {
                (&c.valor, &c.t2m)
            };
            let Some(valores) = propio.as_ref().filter(|_| ajeno.is_none()) else {
                return falla(format!("{donde}: debe traer solo `{campo}`"));
            };
            if valores.len() != anios {
                return falla(format!(
                    "{donde}: {} valores, se esperaban {anios}",
                    valores.len()
                ));
            }
            if valores.iter().all(Option::is_none) {
                return falla(format!("{donde}: sin ningún año con valor"));
            }
            if valores.iter().flatten().any(|x| !rango.contains(x)) {
                return falla(format!(
                    "{donde}: valor fuera de {}..{} {unidad}",
                    rango.start(),
                    rango.end()
                ));
            }
        }
        Ok(())
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
                    Variable::Lluvia => self.buscar(nombre).map(|r| serie_de(&zona, r, |m| m.prectotcorr)),
                    Variable::LluviaImerg => self.buscar_gpm(nombre).map(|r| serie_de(&zona, r, |m| m.lluvia_mm_dia)),
                    Variable::Temperatura => self.buscar(nombre).map(|r| serie_de(&zona, r, |m| m.t2m)),
                    Variable::Vegetacion => self.buscar_ndvi(nombre).map(|r| serie_de(&zona, r, |m| m.ndvi)),
                };
                let serie = serie
                    .ok_or_else(|| error(format_args!("{}: no está en su fuente (power.json, gpm.json o ndvi_departamentos.json)", donde())))?
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

    pub fn buscar_ndvi(&self, nombre: &str) -> Option<&ndvi::Region> {
        self.indice_ndvi.get(&clave(nombre)).map(|&i| &self.ndvi[i])
    }
}

/// Una zona-recuadro con serie anual y tendencia (`ndvi.json`, `cobertura_arboles.json`): lo común
/// (`comun()`) se valida igual en los dos archivos; lo propio de cada uno, aquí.
trait Recuadro: Comunes + serde::de::DeserializeOwned {
    const ARCHIVO: &'static str;
    /// Campo de `anios` sobre el que se calcula `stats`.
    const TENDENCIA_DE: &'static str;
    /// Problema en los campos propios del archivo (umbral), si lo hay.
    fn revisar(&self) -> Option<&'static str>;
    /// Años de `serie`, en orden, cada uno con su problema de rango si lo tiene.
    fn anios(&self) -> Vec<(u16, Option<&'static str>)>;
}

impl Recuadro for ZonaVegetacion {
    const ARCHIVO: &'static str = "ndvi.json";
    const TENDENCIA_DE: &'static str = "ndvi_anual";
    fn revisar(&self) -> Option<&'static str> {
        (!(-1.0..=1.0).contains(&self.umbral_verde_ndvi))
            .then_some("umbral_verde_ndvi fuera de −1 a 1")
    }
    fn anios(&self) -> Vec<(u16, Option<&'static str>)> {
        self.serie
            .iter()
            .map(|m| {
                let mal = !(-1.0..=1.0).contains(&m.ndvi_anual) || m.area_verde_km2 < 0.0;
                (
                    m.anio,
                    mal.then_some("NDVI fuera de −1 a 1 o área verde negativa"),
                )
            })
            .collect()
    }
}

impl Recuadro for ZonaCobertura {
    const ARCHIVO: &'static str = "cobertura_arboles.json";
    const TENDENCIA_DE: &'static str = "arboles_pct";
    fn revisar(&self) -> Option<&'static str> {
        (!(0.0..=100.0).contains(&self.umbral_bosque_pct))
            .then_some("umbral_bosque_pct fuera de 0 a 100")
    }
    fn anios(&self) -> Vec<(u16, Option<&'static str>)> {
        self.serie
            .iter()
            .map(|m| {
                let mal = !(0.0..=100.0).contains(&m.arboles_pct) || m.area_bosque_km2 < 0.0;
                (
                    m.anio,
                    mal.then_some("cobertura de árboles fuera de 0 a 100 % o área negativa"),
                )
            })
            .collect()
    }
}

/// Lee y valida un archivo de recuadros. Si algo no cuadra, la API no arranca y el error dice qué
/// zona falla.
fn recuadros<Z: Recuadro>(json: &str) -> Result<Vec<Z>, serde_json::Error> {
    let zonas: Vec<Z> = serde_json::from_str(json)?;
    if zonas.is_empty() {
        return Err(error(format_args!("{}: no tiene zonas", Z::ARCHIVO)));
    }
    let mut ids = BTreeSet::new();
    for z in &zonas {
        let c = z.comun();
        let mal = |msg: &str| {
            Err(error(format_args!(
                "{}, zona '{}': {msg}",
                Z::ARCHIVO,
                c.id
            )))
        };
        if !ids.insert(c.id) {
            return mal("id repetido");
        }
        match UBIGEOS.iter().find(|(id, _)| *id == c.ubigeo) {
            Some((_, nombre)) if clave(nombre) == clave(c.departamento) => {}
            Some(_) => return mal("el departamento no es el de su ubigeo"),
            None => return mal("ubigeo inexistente"),
        }
        if c.unidad_geografica.trim().is_empty() {
            return mal("falta unidad_geografica");
        }
        let [o, s, e, n] = c.bbox;
        let (lat, lon) = c.lat_lon;
        if !(o < e && s < n && (o..=e).contains(&lon) && (s..=n).contains(&lat)) {
            return mal("bbox inválido o lat/lon fuera del recuadro");
        }
        if let Some(problema) = z.revisar() {
            return mal(problema);
        }
        if c.tendencia_de != Z::TENDENCIA_DE {
            return mal(&format!("tendencia_de debe ser '{}'", Z::TENDENCIA_DE));
        }
        let mut anios = Vec::new();
        for (a, problema) in z.anios() {
            if let Some(p) = problema {
                return mal(&format!("año {a} con {p}"));
            }
            anios.push(a);
        }
        if !anios.windows(2).all(|w| w[0] < w[1]) {
            return mal("serie con años repetidos o desordenados");
        }
        let st = c.stats;
        let en_periodo = anios
            .iter()
            .filter(|a| (st.year_start..=st.year_end).contains(a))
            .count();
        if anios.first() != Some(&st.year_start)
            || anios.last() != Some(&st.year_end)
            || en_periodo != usize::from(st.n_years)
        {
            return mal(&format!(
                "stats dice {}–{} ({} años) pero serie va de {:?} a {:?} ({} años)",
                st.year_start,
                st.year_end,
                st.n_years,
                anios.first(),
                anios.last(),
                anios.len()
            ));
        }
    }
    Ok(zonas)
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
