//! Códigos de departamento (INEI) como texto: "01" Amazonas … "25" Ucayali.
//! Siguen el orden alfabético de `pipeline/power.py::REGIONES`; "07" es Callao y "15" Lima.
use crate::data::clave;

const UBIGEOS: [(&str, &str); 25] = [
    ("01", "Amazonas"), ("02", "Áncash"), ("03", "Apurímac"), ("04", "Arequipa"),
    ("05", "Ayacucho"), ("06", "Cajamarca"), ("07", "Callao"), ("08", "Cusco"),
    ("09", "Huancavelica"), ("10", "Huánuco"), ("11", "Ica"), ("12", "Junín"),
    ("13", "La Libertad"), ("14", "Lambayeque"), ("15", "Lima"), ("16", "Loreto"),
    ("17", "Madre de Dios"), ("18", "Moquegua"), ("19", "Pasco"), ("20", "Piura"),
    ("21", "Puno"), ("22", "San Martín"), ("23", "Tacna"), ("24", "Tumbes"), ("25", "Ucayali"),
];

pub fn de_nombre(nombre: &str) -> Option<&'static str> {
    UBIGEOS.iter().find(|(_, n)| clave(n) == clave(nombre)).map(|(u, _)| *u)
}

pub fn nombre(ubigeo: &str) -> Option<&'static str> {
    UBIGEOS.iter().find(|(u, _)| *u == ubigeo).map(|(_, n)| *n)
}
