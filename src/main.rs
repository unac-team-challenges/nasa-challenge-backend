use nasa_challenge_backend::{app, config::Config, data::Datos};
use std::sync::Arc;

/// Espera Ctrl+C (o SIGTERM en Linux) para cerrar sin cortar las peticiones en curso.
async fn apagar() {
    let ctrl_c = async {
        tokio::signal::ctrl_c().await.ok();
    };
    #[cfg(unix)]
    let terminar = async {
        match tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()) {
            Ok(mut s) => {
                s.recv().await;
            }
            Err(_) => std::future::pending::<()>().await,
        }
    };
    #[cfg(not(unix))]
    let terminar = std::future::pending::<()>();
    tokio::select! {
        _ = ctrl_c => {},
        _ = terminar => {},
    }
}

#[tokio::main]
async fn main() {
    let cfg = Config::desde_env();
    let datos = Arc::new(Datos::cargar().expect("data/*.json no encaja con src/models"));
    let addr = format!("0.0.0.0:{}", cfg.puerto);
    let l = tokio::net::TcpListener::bind(&addr)
        .await
        .unwrap_or_else(|e| panic!("no se pudo abrir {addr}: {e}"));
    println!("http://{addr}");
    axum::serve(l, app(datos, cfg.origenes))
        .with_graceful_shutdown(apagar())
        .await
        .unwrap();
}
