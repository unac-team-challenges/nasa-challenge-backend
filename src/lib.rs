pub mod config;
pub mod data;
pub mod error;
pub mod models;
pub mod openapi;
pub mod routes;
pub mod schema;
pub mod ubigeo;

use axum::{
    http::{header, HeaderValue},
    Router,
};
use data::Estado;
use tower_http::{
    cors::{AllowOrigin, CorsLayer},
    set_header::SetResponseHeaderLayer,
};

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
    routes::router().layer(cache).layer(cors).with_state(datos)
}
