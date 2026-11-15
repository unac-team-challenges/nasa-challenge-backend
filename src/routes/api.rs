//! Rutas del contrato del Drive (`07-stack-decidido`): `/api/variables`, `/api/zonas`, `/api/zonas/{id}`.
//! Solo devuelven lo que dejó `pipeline/` (validado al arrancar en `data.rs`): nunca calculan.
use crate::{
    data::Estado,
    error::ApiError,
    models::{
        variable::{Variable, VariableInfo},
        zona::Zona,
    },
    schema::{ErrorRespuesta, ZonaDetalle},
};
use axum::{
    extract::{Path, Query, State},
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
