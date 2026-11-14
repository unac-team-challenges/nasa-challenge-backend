use nasa_challenge_backend::{app, config::Config, data::Datos};
use std::sync::Arc;

#[tokio::main]
async fn main() {
    let cfg = Config::desde_env();
    let datos = Arc::new(Datos::cargar().expect("data/power.json inválido"));
    let addr = format!("0.0.0.0:{}", cfg.puerto);
    let l = tokio::net::TcpListener::bind(&addr).await.unwrap();
    println!("http://{addr}");
    axum::serve(l, app(datos, cfg.origenes)).await.unwrap();
}
