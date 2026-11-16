pub mod config;
pub mod data;
pub mod error;
pub mod models;
pub mod openapi;
pub mod routes;
pub mod schema;
pub mod ubigeo;

use axum::{
    Router,
    http::{HeaderValue, header},
};
use data::Estado;
use tower_http::{
    cors::{AllowOrigin, CorsLayer},
    set_header::SetResponseHeaderLayer,
    trace::{DefaultMakeSpan, DefaultOnResponse, TraceLayer},
};
use tracing::Level;

pub fn app(datos: Estado, origenes: Vec<String>) -> Router {
    let cors = CorsLayer::new().allow_origin(AllowOrigin::predicate(move |o, _| {
        o.to_str()
            .is_ok_and(|o| config::origen_permitido(o, &origenes))
    }));
    // Los datos se embeben al compilar y no cambian mientras el binario vive:
    // 1 h en el navegador, 1 día en el CDN (se invalida al desplegar).
    let cache = SetResponseHeaderLayer::if_not_present(
        header::CACHE_CONTROL,
        HeaderValue::from_static("public, max-age=3600, s-maxage=86400"),
    );
    // Una línea por petición (método, ruta, estado, ms) a nivel INFO; RUST_LOG la sube o la apaga.
    let logs = TraceLayer::new_for_http()
        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
        .on_response(DefaultOnResponse::new().level(Level::INFO));
    routes::router()
        .layer(cache)
        .layer(cors)
        .layer(logs)
        .with_state(datos)
}
