//! Rutas del contrato del Drive (`07-stack-decidido`): `/api/variables`, `/api/zonas`, `/api/zonas/{id}`.
//! Los campos de tendencia (`stats`) se añaden cuando el pipeline los calcule.
use crate::{
    data::Estado,
    error::ApiError,
    models::variable::Variable,
    schema::{ErrorRespuesta, Punto, VariableInfo, Zona, ZonaDetalle},
    ubigeo,
};
use axum::{extract::{Path, Query, State}, Json};
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

/// Variables del producto con unidad, fuente y rango de años.
#[utoipa::path(get, path = "/api/variables", tag = "api",
    responses((status = 200, body = Vec<VariableInfo>)))]
pub async fn variables(State(d): State<Estado>) -> Json<Vec<VariableInfo>> {
    Json(
        Variable::TODAS
            .into_iter()
            .map(|v| {
                let anios: Vec<u16> = d
                    .regiones
                    .iter()
                    .filter_map(|r| d.serie(v, &r.region))
                    .flat_map(|s| s.into_iter().map(|(a, _)| a))
                    .collect();
                VariableInfo {
                    id: v.id(),
                    unidad: v.unidad(),
                    fuente: v.fuente(),
                    descripcion: v.descripcion(),
                    anio_inicio: anios.iter().min().copied(),
                    anio_fin: anios.iter().max().copied(),
                }
            })
            .collect(),
    )
}

/// Las 25 zonas (departamentos) sin series.
#[utoipa::path(get, path = "/api/zonas", tag = "api",
    params(("variable" = Variable, Query, description = "Obligatoria: el plan B estático la necesita en la ruta")),
    responses((status = 200, body = Vec<Zona>), (status = 400, body = ErrorRespuesta)))]
pub async fn zonas(State(d): State<Estado>, Query(p): Query<Params>) -> Result<Json<Vec<Zona>>, ApiError> {
    variable(p)?;
    Ok(Json(
        d.regiones
            .iter()
            .filter_map(|r| {
                Some(Zona { id: ubigeo::de_nombre(&r.region)?, nombre: r.region.clone(), lat: r.lat, lon: r.lon })
            })
            .collect(),
    ))
}

/// Serie anual de una zona (`id` = ubigeo como texto, "01"–"25").
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
) -> Result<Json<ZonaDetalle>, ApiError> {
    let v = variable(p)?;
    let nombre = ubigeo::nombre(&id).ok_or_else(|| ApiError::ZonaNoEncontrada(id.clone()))?;
    let r = d.buscar(nombre).ok_or(ApiError::ZonaNoEncontrada(id))?;
    let serie = d.serie(v, nombre).unwrap_or_default();
    Ok(Json(ZonaDetalle {
        id: ubigeo::de_nombre(nombre).unwrap_or_default(),
        nombre: r.region.clone(),
        lat: r.lat,
        lon: r.lon,
        variable: v.id(),
        unidad: v.unidad(),
        fuente: v.fuente(),
        nota: d.nota(v, nombre).map(String::from),
        serie: serie.into_iter().map(|(anio, valor)| Punto { anio, valor }).collect(),
    }))
}
