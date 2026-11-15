use crate::data::Estado;
use axum::{
    http::{header, StatusCode, Uri},
    routing::get,
    Json, Router,
};
use serde_json::{json, Value};
use std::sync::LazyLock;

pub mod api;
mod gpm;
mod power;
mod regiones;

/// Se genera desde el código una sola vez (al montar el router): siempre cuadra con las rutas y
/// structs del binario, aunque `openapi.json` de la raíz se haya quedado sin regenerar.
static OPENAPI: LazyLock<String> = LazyLock::new(crate::openapi::json);

async fn openapi() -> ([(header::HeaderName, &'static str); 1], &'static str) {
    (
        [(header::CONTENT_TYPE, "application/json")],
        OPENAPI.as_str(),
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
    // Al arrancar, no en la primera petición: un fallo de utoipa se ve antes de servir nada.
    LazyLock::force(&OPENAPI);
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
