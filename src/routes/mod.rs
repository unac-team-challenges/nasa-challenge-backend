use crate::data::Estado;
use axum::{routing::get, Json, Router};
use serde_json::{json, Value};

pub mod api;
mod gpm;
mod power;
mod regiones;

async fn openapi() -> ([(&'static str, &'static str); 1], String) {
    ([("content-type", "application/json")], crate::openapi::json())
}

async fn health() -> Json<Value> {
    Json(json!({"status": "ok"}))
}

pub fn router() -> Router<Estado> {
    Router::new()
        .route("/health", get(health))
        .route("/regiones", get(regiones::listar))
        .route("/power/{region}", get(power::obtener))
        .route("/gpm/{region}", get(gpm::obtener))
        .route("/api/openapi.json", get(openapi))
        .route("/api/variables", get(api::variables))
        .route("/api/zonas", get(api::zonas))
        .route("/api/zonas/{id}", get(api::zona))
}
