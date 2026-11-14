use axum::{body::{to_bytes, Body}, http::{Request, StatusCode}, Router};
use nasa_challenge_backend::{app, data::Datos};
use serde_json::Value;
use std::sync::Arc;
use tower::ServiceExt;

fn router() -> Router {
    app(Arc::new(Datos::cargar().unwrap()), vec!["https://demo.vercel.app".into()])
}

async fn get(ruta: &str, origen: Option<&str>) -> (StatusCode, Option<String>, Value) {
    let mut req = Request::get(ruta);
    if let Some(o) = origen {
        req = req.header("origin", o);
    }
    let res = router().oneshot(req.body(Body::empty()).unwrap()).await.unwrap();
    let status = res.status();
    let acao = res.headers().get("access-control-allow-origin").map(|v| v.to_str().unwrap().to_string());
    let body = to_bytes(res.into_body(), usize::MAX).await.unwrap();
    (status, acao, serde_json::from_slice(&body).unwrap_or(Value::Null))
}

#[tokio::test]
async fn health() {
    let (s, _, b) = get("/health", None).await;
    assert_eq!(s, StatusCode::OK);
    assert_eq!(b["status"], "ok");
}

#[tokio::test]
async fn regiones_son_25() {
    let (s, _, b) = get("/regiones", None).await;
    assert_eq!(s, StatusCode::OK);
    assert_eq!(b.as_array().unwrap().len(), 25);
}

#[tokio::test]
async fn power_lima_tiene_anios_y_medidas() {
    let (s, _, b) = get("/power/lima", None).await;
    assert_eq!(s, StatusCode::OK);
    let anios = b["anios"].as_object().unwrap();
    assert!(!anios.is_empty());
    assert!(anios.values().all(|m| ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN"].iter().all(|k| m[*k].is_number())));
}

#[tokio::test]
async fn gpm_lima_tiene_lluvia_por_anio() {
    let (s, _, b) = get("/gpm/lima", None).await;
    assert_eq!(s, StatusCode::OK);
    assert_eq!(b["region"], "Lima");
    let anios = b["anios"].as_object().unwrap();
    assert!(!anios.is_empty());
    assert!(anios.values().all(|m| m["lluvia_mm_dia"].is_number()));
    assert_eq!(get("/gpm/ANCASH", None).await.0, StatusCode::OK);
    assert_eq!(get("/gpm/noexiste", None).await.0, StatusCode::NOT_FOUND);
}

#[tokio::test]
async fn busqueda_ignora_tildes_y_mayusculas() {
    for ruta in ["/power/ancash", "/power/%C3%81ncash", "/power/ANCASH", "/power/san%20martin"] {
        let (s, _, _) = get(ruta, None).await;
        assert_eq!(s, StatusCode::OK, "{ruta}");
    }
    let (_, _, b) = get("/power/ancash", None).await;
    assert_eq!(b["region"], "Áncash");
}

#[tokio::test]
async fn region_inexistente_da_404_json() {
    let (s, _, b) = get("/power/noexiste", None).await;
    assert_eq!(s, StatusCode::NOT_FOUND);
    assert!(b["error"].as_str().unwrap().contains("noexiste"));
}

#[tokio::test]
async fn cors_permite_localhost_y_extra_pero_no_otros() {
    for o in ["http://localhost:5173", "http://127.0.0.1:3000", "https://demo.vercel.app"] {
        assert_eq!(get("/regiones", Some(o)).await.1.as_deref(), Some(o));
    }
    for o in ["http://localhost.evil.com", "https://otro.vercel.app"] {
        assert_eq!(get("/regiones", Some(o)).await.1, None, "{o}");
    }
}

#[test]
fn json_con_forma_incorrecta_se_rechaza() {
    assert!(Datos::desde_json(r#"[{"region":"X","lat":1,"lon":2,"anios":{"2020":{"T2M":null}}}]"#, "[]").is_err());
    assert!(Datos::desde_json("[]", r#"[{"region":"X","lat":1,"lon":2,"anios":{"2020":{"lluvia_mm_dia":null}}}]"#).is_err());
}
