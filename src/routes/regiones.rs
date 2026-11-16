use crate::{data::Estado, schema::RegionResumen};
use axum::{Json, extract::State};

pub async fn listar(State(d): State<Estado>) -> Json<Vec<RegionResumen>> {
    Json(d.regiones.iter().map(RegionResumen::from).collect())
}
