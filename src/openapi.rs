//! Contrato OpenAPI de `/api/*`. El frontend lo copia a `src/api/openapi.json` y genera sus tipos (`pnpm gen`).
use crate::{
    models::{
        cobertura::{AnioCobertura, ZonaCobertura},
        variable::{Variable, VariableInfo},
        vegetacion::{AnioVegetacion, ZonaVegetacion},
        zona::{Stats, Status, Zona},
    },
    routes::api,
    schema,
};
use utoipa::OpenApi;

#[derive(OpenApi)]
#[openapi(
    info(
        title = "Detective del Perú",
        description = "API de solo lectura: sirve resultados ya calculados."
    ),
    paths(api::variables, api::zonas, api::zona, api::vegetacion, api::cobertura),
    components(schemas(
        Variable,
        VariableInfo,
        Zona,
        Stats,
        Status,
        ZonaVegetacion,
        AnioVegetacion,
        ZonaCobertura,
        AnioCobertura,
        schema::ZonaDetalle,
        schema::Punto,
        schema::ErrorRespuesta
    ))
)]
pub struct ApiDoc;

pub fn json() -> String {
    ApiDoc::openapi()
        .to_pretty_json()
        .expect("OpenAPI serializable")
        + "\n"
}
