use axum::{http::StatusCode, response::{IntoResponse, Response}, Json};
use serde_json::json;

pub enum ApiError {
    NoEncontrada(String),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        match self {
            ApiError::NoEncontrada(r) => {
                (StatusCode::NOT_FOUND, Json(json!({"error": format!("región '{r}' no encontrada")}))).into_response()
            }
        }
    }
}
