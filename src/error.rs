use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use serde_json::json;

/// Recorta lo que el usuario escribió antes de devolverlo en el mensaje de error.
fn corto(s: &str) -> String {
    s.chars().take(60).collect()
}

pub enum ApiError {
    NoEncontrada(String),
    ZonaNoEncontrada(String),
    VariableInvalida(Option<String>),
    /// La variable existe pero no tiene malla por celdas.
    SinCeldas(&'static str),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        match self {
            ApiError::ZonaNoEncontrada(z) => (
                StatusCode::NOT_FOUND,
                Json(json!({"error": format!("zona '{}' no encontrada", corto(&z))})),
            )
                .into_response(),
            ApiError::VariableInvalida(v) => {
                let msg = match v {
                    Some(v) => format!(
                        "variable '{}' no existe; usa: lluvia | temperatura | lluvia_imerg | vegetacion",
                        corto(&v)
                    ),
                    None => {
                        "falta ?variable=; usa: lluvia | temperatura | lluvia_imerg | vegetacion".to_string()
                    }
                };
                (StatusCode::BAD_REQUEST, Json(json!({"error": msg}))).into_response()
            }
            ApiError::SinCeldas(v) => (
                StatusCode::BAD_REQUEST,
                Json(
                    json!({"error": format!("'{v}' no tiene malla por celdas; usa: lluvia, temperatura o vegetacion")}),
                ),
            )
                .into_response(),
            ApiError::NoEncontrada(r) => (
                StatusCode::NOT_FOUND,
                Json(json!({"error": format!("región '{}' no encontrada", corto(&r))})),
            )
                .into_response(),
        }
    }
}
