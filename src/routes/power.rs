use crate::{data::Estado, error::ApiError};
use axum::{
    extract::{Path, State},
    response::{IntoResponse, Response},
    Json,
};

/// Serializa la región prestada del estado: sin copiar sus años.
pub async fn obtener(
    State(d): State<Estado>,
    Path(nombre): Path<String>,
) -> Result<Response, ApiError> {
    d.buscar(&nombre)
        .map(|r| Json(r).into_response())
        .ok_or(ApiError::NoEncontrada(nombre))
}
