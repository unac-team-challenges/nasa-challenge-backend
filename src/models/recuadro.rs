//! Los campos que comparten `ZonaVegetacion` (`ndvi.json`) y `ZonaCobertura` (`cobertura_arboles.json`),
//! declarados una sola vez. Un campo común nuevo se añade aquí y aparece en los dos modelos.
//!
//! No es un struct genérico `ZonaRecuadro<A>` a propósito: el umbral se llama distinto en cada JSON,
//! los tests exigen rechazar campos desconocidos (serde no lo hace con `#[serde(flatten)]`) y OpenAPI
//! seguiría publicando `ZonaVegetacion` y `ZonaCobertura` con esos nombres para el front.
use crate::models::zona::Stats;

/// Lo común de una zona-recuadro que `data.rs` valida igual en los dos archivos.
pub struct Comun<'a> {
    pub id: &'a str,
    pub ubigeo: &'a str,
    pub departamento: &'a str,
    pub unidad_geografica: &'a str,
    pub bbox: [f64; 4],
    pub lat_lon: (f64, f64),
    pub tendencia_de: &'a str,
    pub stats: &'a Stats,
}

pub trait Comunes {
    fn comun(&self) -> Comun<'_>;
}

/// Define una zona-recuadro. Lo propio de cada archivo se pasa como parámetro: el nombre del struct,
/// el tipo de su año, el nombre del umbral y el texto de los campos cuya explicación cambia. El orden
/// de los campos es el del JSON y el de OpenAPI.
macro_rules! zona_recuadro {
    (
        $(#[$meta:meta])*
        $zona:ident, $anio:ty, $umbral:ident;
        id: $id:literal, tipo: $tipo:literal, pixeles: $pixeles:literal,
        umbral: $doc_umbral:literal, tendencia_de: $tendencia:literal, serie: $serie:literal $(,)?
    ) => {
        $(#[$meta])*
        #[derive(Clone, Debug, serde::Deserialize, serde::Serialize, utoipa::ToSchema)]
        #[serde(deny_unknown_fields)]
        pub struct $zona {
            #[doc = $id]
            pub id: String,
            pub nombre: String,
            /// Departamento donde está el recuadro.
            pub departamento: String,
            /// Ubigeo del departamento, como texto ("01"–"25").
            pub ubigeo: String,
            #[doc = $tipo]
            pub tipo: String,
            /// Qué área se promedia: un recuadro, **no** el departamento. La ficha debe mostrarlo.
            pub unidad_geografica: String,
            /// `[oeste, sur, este, norte]` en grados.
            pub bbox: [f64; 4],
            pub lat: f64,
            pub lon: f64,
            #[doc = $pixeles]
            pub pixeles: u32,
            pub fuente: String,
            #[doc = $doc_umbral]
            pub $umbral: f64,
            #[doc = $tendencia]
            pub tendencia_de: String,
            #[doc = $serie]
            pub serie: Vec<$anio>,
            pub stats: crate::models::zona::Stats,
        }

        impl crate::models::recuadro::Comunes for $zona {
            fn comun(&self) -> crate::models::recuadro::Comun<'_> {
                crate::models::recuadro::Comun {
                    id: &self.id,
                    ubigeo: &self.ubigeo,
                    departamento: &self.departamento,
                    unidad_geografica: &self.unidad_geografica,
                    bbox: self.bbox,
                    lat_lon: (self.lat, self.lon),
                    tendencia_de: &self.tendencia_de,
                    stats: &self.stats,
                }
            }
        }
    };
}
pub(crate) use zona_recuadro;
