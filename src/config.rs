/// PORT (por defecto 3000) y CORS_ORIGINS (orígenes extra separados por coma,
/// p. ej. la URL de Vercel). localhost siempre está permitido.
pub struct Config {
    pub puerto: String,
    pub origenes: Vec<String>,
}

impl Config {
    pub fn desde_env() -> Self {
        Self {
            puerto: std::env::var("PORT").unwrap_or("3000".into()),
            origenes: std::env::var("CORS_ORIGINS")
                .unwrap_or_default()
                .split(',')
                .map(|o| o.trim().trim_end_matches('/').to_string())
                .filter(|o| !o.is_empty())
                .collect(),
        }
    }
}

pub fn origen_permitido(origen: &str, extra: &[String]) -> bool {
    let local = ["http://localhost", "http://127.0.0.1"].iter().any(|h| {
        origen
            .strip_prefix(h)
            .is_some_and(|r| r.is_empty() || r.starts_with(':'))
    });
    local || extra.iter().any(|e| e == origen)
}
