use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::get,
    Json, Router,
};
use serde_json::{json, Value};
use std::sync::Arc;
use tower_http::cors::{AllowOrigin, CorsLayer};

// JSON ya procesado por pipeline/power.py. La API nunca calcula en vivo.
const POWER: &str = include_str!("../data/power.json");

// CORS solo para localhost. Añadir aquí la URL de Vercel cuando exista.
fn origen_permitido(o: &str) -> bool {
    ["http://localhost", "http://127.0.0.1"]
        .iter()
        .any(|h| o.strip_prefix(h).is_some_and(|r| r.is_empty() || r.starts_with(':')))
}

type Datos = Arc<Vec<Value>>;

async fn regiones(State(d): State<Datos>) -> Json<Value> {
    Json(d.iter().map(|r| json!({"region": r["region"], "lat": r["lat"], "lon": r["lon"]})).collect())
}

async fn power(State(d): State<Datos>, Path(region): Path<String>) -> Result<Json<Value>, StatusCode> {
    let region = region.to_lowercase();
    d.iter()
        .find(|r| r["region"].as_str().is_some_and(|n| n.to_lowercase() == region))
        .map(|r| Json(r.clone()))
        .ok_or(StatusCode::NOT_FOUND)
}

#[tokio::main]
async fn main() {
    let datos: Datos = Arc::new(serde_json::from_str(POWER).expect("data/power.json inválido"));
    let app = Router::new()
        .route("/regiones", get(regiones))
        .route("/power/{region}", get(power))
        .layer(CorsLayer::new().allow_origin(AllowOrigin::predicate(|o, _| {
            o.to_str().is_ok_and(origen_permitido)
        })))
        .with_state(datos);
    let addr = format!("0.0.0.0:{}", std::env::var("PORT").unwrap_or("3000".into()));
    let l = tokio::net::TcpListener::bind(&addr).await.unwrap();
    println!("http://{addr}");
    axum::serve(l, app).await.unwrap();
}
