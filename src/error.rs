use axum::{http::StatusCode, response::{IntoResponse, Response}, Json};
use serde_json::json;

pub enum ApiError {
    NoEncontrada(String),
    ZonaNoEncontrada(String),
    VariableInvalida(Option<String>),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        match self {
            ApiError::ZonaNoEncontrada(z) => {
                (StatusCode::NOT_FOUND, Json(json!({"error": format!("zona '{z}' no encontrada")}))).into_response()
            }
            ApiError::VariableInvalida(v) => {
                let msg = match v {
                    Some(v) => format!("variable '{v}' no existe; usa: lluvia | temperatura"),
                    None => "falta ?variable=; usa: lluvia | temperatura".to_string(),
                };
                (StatusCode::BAD_REQUEST, Json(json!({"error": msg}))).into_response()
            }
            ApiError::NoEncontrada(r) => {
                (StatusCode::NOT_FOUND, Json(json!({"error": format!("región '{r}' no encontrada")}))).into_response()
            }
        }
    }
}
