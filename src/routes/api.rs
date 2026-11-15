//! Rutas del contrato del Drive (`07-stack-decidido`): `/api/variables`, `/api/zonas`, `/api/zonas/{id}`,
//! más `/api/vegetacion` (Caso 2, costa) y `/api/cobertura-arboles` (selva).
//! Solo devuelven lo que dejó `pipeline/` (validado al arrancar en `data.rs`): nunca calculan.
use crate::{
    data::Estado,
    error::ApiError,
    models::{
        celdas::Malla,
        cobertura::ZonaCobertura,
        variable::{Variable, VariableInfo},
        vegetacion::ZonaVegetacion,
        zona::Zona,
    },
    schema::{ErrorRespuesta, ZonaDetalle},
};
use axum::{
    extract::{Path, Query, State},
    http::header,
    response::{IntoResponse, Response},
    Json,
};
use serde::Deserialize;

#[derive(Deserialize)]
pub struct Params {
    variable: Option<String>,
}

/// `variable` es obligatoria (el plan B estático la necesita en la ruta).
fn variable(p: Params) -> Result<Variable, ApiError> {
    match p.variable {
        Some(v) => Variable::parse(&v).ok_or(ApiError::VariableInvalida(Some(v))),
        None => Err(ApiError::VariableInvalida(None)),
    }
}

/// Variables del producto con unidad, fuente y rango de años (`data/variables.json`).
#[utoipa::path(get, path = "/api/variables", tag = "api",
    responses((status = 200, body = Vec<VariableInfo>)))]
pub async fn variables(State(d): State<Estado>) -> Response {
    Json(&d.variables).into_response()
}

/// Las 25 zonas (departamentos) con su tendencia, sin series.
#[utoipa::path(get, path = "/api/zonas", tag = "api",
    params(("variable" = Variable, Query, description = "Obligatoria: el plan B estático la necesita en la ruta")),
    responses((status = 200, body = Vec<Zona>), (status = 400, body = ErrorRespuesta)))]
pub async fn zonas(State(d): State<Estado>, Query(p): Query<Params>) -> Result<Response, ApiError> {
    let v = variable(p)?;
    Ok(Json(d.zonas(v).collect::<Vec<_>>()).into_response())
}

/// Serie anual y tendencia de una zona (`id` = ubigeo como texto, "01"–"25").
#[utoipa::path(get, path = "/api/zonas/{id}", tag = "api",
    params(
        ("id" = String, Path, description = "Ubigeo del departamento, como texto", example = "15"),
        ("variable" = Variable, Query, description = "Obligatoria"),
    ),
    responses((status = 200, body = ZonaDetalle), (status = 400, body = ErrorRespuesta), (status = 404, body = ErrorRespuesta)))]
pub async fn zona(
    State(d): State<Estado>,
    Path(id): Path<String>,
    Query(p): Query<Params>,
) -> Result<Response, ApiError> {
    let v = variable(p)?;
    let f = d.ficha(v, &id).ok_or(ApiError::ZonaNoEncontrada(id))?;
    let info = d.variable(v);
    Ok(Json(ZonaDetalle::new(
        &f.zona,
        v.id(),
        &info.unidad,
        &info.fuente,
        &f.serie,
    ))
    .into_response())
}

/// Vegetación (NDVI de MODIS) de los valles irrigados de la costa, para el Caso 2: cada zona con su
/// serie anual (`ndvi_anual`, `area_verde_km2`), su tendencia y su `unidad_geografica` (un recuadro
/// sobre el valle, **no** el promedio del departamento).
#[utoipa::path(get, path = "/api/vegetacion", tag = "api",
    responses((status = 200, body = Vec<ZonaVegetacion>)))]
pub async fn vegetacion(State(d): State<Estado>) -> Response {
    Json(&d.vegetacion).into_response()
}

/// Cobertura de árboles (MODIS MOD44B) de recuadros de selva, donde el NDVI se satura: cada zona con
/// su serie anual (`arboles_pct`, `area_bosque_km2`), su tendencia y su `unidad_geografica`
/// (un recuadro, **no** el promedio del departamento).
#[utoipa::path(get, path = "/api/cobertura-arboles", tag = "api",
    responses((status = 200, body = Vec<ZonaCobertura>)))]
pub async fn cobertura(State(d): State<Estado>) -> Response {
    Json(&d.cobertura).into_response()
}

/// T2M anual de cada celda de NASA POWER (~0,5° × 0,625°) dentro de Perú, para el mapa de calor.
/// Solo existe para `temperatura`.
#[utoipa::path(get, path = "/api/celdas", tag = "api",
    params(("variable" = Variable, Query, description = "Obligatoria; solo temperatura")),
    responses((status = 200, body = Malla), (status = 400, body = ErrorRespuesta)))]
pub async fn celdas(
    State(d): State<Estado>,
    Query(p): Query<Params>,
) -> Result<Response, ApiError> {
    match variable(p)? {
        Variable::Temperatura => Ok((
            [(header::CONTENT_TYPE, "application/json")],
            d.celdas.clone(),
        )
            .into_response()),
        v => Err(ApiError::SinCeldas(v.id())),
    }
}
