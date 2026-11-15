use crate::data::Estado;
use axum::{
    http::{header, StatusCode, Uri},
    routing::get,
    Json, Router,
};
use serde_json::{json, Value};

pub mod api;
mod gpm;
mod power;
mod regiones;

async fn openapi() -> ([(&'static str, &'static str); 1], String) {
    (
        [("content-type", "application/json")],
        crate::openapi::json(),
    )
}

/// El health check nunca se cachea.
async fn health() -> ([(header::HeaderName, &'static str); 1], Json<Value>) {
    (
        [(header::CACHE_CONTROL, "no-store")],
        Json(json!({"status": "ok"})),
    )
}

/// Cualquier ruta que no existe responde JSON, igual que el resto de errores.
async fn no_existe(uri: Uri) -> (StatusCode, Json<Value>) {
    let ruta: String = uri.path().chars().take(60).collect();
    (
        StatusCode::NOT_FOUND,
        Json(json!({"error": format!("ruta '{ruta}' no existe")})),
    )
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
        .route("/api/vegetacion", get(api::vegetacion))
        .fallback(no_existe)
}
