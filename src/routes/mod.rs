use crate::data::Estado;
use axum::{routing::get, Json, Router};
use serde_json::{json, Value};

mod gpm;
mod power;
mod regiones;

async fn health() -> Json<Value> {
    Json(json!({"status": "ok"}))
}

pub fn router() -> Router<Estado> {
    Router::new()
        .route("/health", get(health))
        .route("/regiones", get(regiones::listar))
        .route("/power/{region}", get(power::obtener))
        .route("/gpm/{region}", get(gpm::obtener))
}
