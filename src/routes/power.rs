use crate::{data::Estado, error::ApiError, models::power::Region};
use axum::{
    extract::{Path, State},
    Json,
};

pub async fn obtener(
    State(d): State<Estado>,
    Path(nombre): Path<String>,
) -> Result<Json<Region>, ApiError> {
    d.buscar(&nombre)
        .cloned()
        .map(Json)
        .ok_or(ApiError::NoEncontrada(nombre))
}
