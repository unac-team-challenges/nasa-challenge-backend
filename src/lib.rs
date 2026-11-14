pub mod config;
pub mod data;
pub mod error;
pub mod models;
pub mod openapi;
pub mod routes;
pub mod schema;
pub mod ubigeo;

use axum::Router;
use data::Estado;
use tower_http::cors::{AllowOrigin, CorsLayer};

pub fn app(datos: Estado, origenes: Vec<String>) -> Router {
    let cors = CorsLayer::new().allow_origin(AllowOrigin::predicate(move |o, _| {
        o.to_str().is_ok_and(|o| config::origen_permitido(o, &origenes))
    }));
    routes::router().layer(cors).with_state(datos)
}
