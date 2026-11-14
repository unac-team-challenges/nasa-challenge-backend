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

#[tokio::test]
async fn api_variables_lista_lluvia_y_temperatura() {
    let (s, _, b) = get("/api/variables", None).await;
    assert_eq!(s, StatusCode::OK);
    let ids: Vec<_> = b.as_array().unwrap().iter().map(|v| v["id"].as_str().unwrap()).collect();
    assert_eq!(ids, ["lluvia", "temperatura"]);
    assert!(b[0]["anio_inicio"].is_number() && b[0]["unidad"] == "mm/día");
}

#[tokio::test]
async fn api_zonas_son_25_con_ubigeo_texto() {
    let (s, _, b) = get("/api/zonas?variable=lluvia", None).await;
    assert_eq!(s, StatusCode::OK);
    let zonas = b.as_array().unwrap();
    assert_eq!(zonas.len(), 25);
    let mut ids: Vec<_> = zonas.iter().map(|z| z["id"].as_str().unwrap().to_string()).collect();
    ids.sort();
    ids.dedup();
    assert_eq!(ids.len(), 25);
    assert_eq!(ids[0], "01");
    assert_eq!(ids[24], "25");
    let nombre = |id: &str| zonas.iter().find(|z| z["id"] == id).unwrap()["nombre"].clone();
    assert_eq!(nombre("07"), "Callao");
    assert_eq!(nombre("15"), "Lima");
}

#[tokio::test]
async fn api_zona_devuelve_serie_por_variable() {
    for (var, unidad) in [("lluvia", "mm/día"), ("temperatura", "°C")] {
        let (s, _, b) = get(&format!("/api/zonas/15?variable={var}"), None).await;
        assert_eq!(s, StatusCode::OK);
        assert_eq!((b["id"].as_str(), b["nombre"].as_str(), b["unidad"].as_str()), (Some("15"), Some("Lima"), Some(unidad)));
        let serie = b["serie"].as_array().unwrap();
        assert!(!serie.is_empty());
        assert!(serie.iter().all(|p| p["anio"].is_number() && p["valor"].is_number()));
    }
}

#[tokio::test]
async fn api_variable_es_obligatoria_y_valida() {
    for ruta in ["/api/zonas", "/api/zonas/15", "/api/zonas?variable=viento", "/api/zonas/15?variable="] {
        let (s, _, b) = get(ruta, None).await;
        assert_eq!(s, StatusCode::BAD_REQUEST, "{ruta}");
        assert!(b["error"].as_str().unwrap().contains("lluvia"));
    }
}

#[tokio::test]
async fn api_zona_inexistente_da_404() {
    for id in ["00", "26", "99", "lima"] {
        assert_eq!(get(&format!("/api/zonas/{id}?variable=lluvia"), None).await.0, StatusCode::NOT_FOUND, "{id}");
    }
}

#[tokio::test]
async fn ruta_inexistente_responde_json() {
    for ruta in ["/noexiste", "/power/lima/"] {
        let (s, _, b) = get(ruta, None).await;
        assert_eq!(s, StatusCode::NOT_FOUND, "{ruta}");
        assert!(b["error"].is_string(), "{ruta}");
    }
    let larga = "a".repeat(5000);
    let (_, _, b) = get(&format!("/power/{larga}"), None).await;
    assert!(b["error"].as_str().unwrap().len() < 200, "el error no debe reflejar toda la entrada");
}

#[tokio::test]
async fn datos_se_cachean_pero_health_no() {
    let cabecera = |ruta: &'static str| async move {
        let res = router().oneshot(Request::get(ruta).body(Body::empty()).unwrap()).await.unwrap();
        res.headers().get("cache-control").map(|v| v.to_str().unwrap().to_string())
    };
    assert!(cabecera("/gpm/lima").await.unwrap().contains("s-maxage"));
    assert_eq!(cabecera("/health").await.as_deref(), Some("no-store"));
}

#[test]
fn campos_desconocidos_y_regiones_distintas_se_rechazan() {
    let medida_ok = r#"{"PRECTOTCORR":1,"T2M":2,"T2M_MAX":3,"T2M_MIN":0}"#;
    let region = |m: &str| format!(r#"[{{"region":"X","lat":1,"lon":2,"celdas":4,"anios":{{"2020":{m}}}}}]"#);
    let gpm_ok = region(r#"{"lluvia_mm_dia":1}"#);
    assert!(Datos::desde_json(&region(medida_ok), &gpm_ok).is_ok());
    // un campo de más en las medidas
    let power_extra = region(r#"{"PRECTOTCORR":1,"T2M":2,"T2M_MAX":3,"T2M_MIN":0,"nuevo":1}"#);
    assert!(Datos::desde_json(&power_extra, &gpm_ok).is_err());
    // un campo de más en la región
    let region_extra = r#"[{"region":"X","lat":1,"lon":2,"celdas":4,"nuevo":"x","anios":{}}]"#;
    assert!(Datos::desde_json(region_extra, "[]").is_err());
    // power.json y gpm.json con regiones distintas
    let otra = gpm_ok.replace("\"X\"", "\"Y\"");
    assert!(Datos::desde_json(&region(medida_ok), &otra).is_err());
    // `celdas` es obligatorio; `nota` es opcional
    assert!(Datos::desde_json(r#"[{"region":"X","lat":1,"lon":2,"anios":{}}]"#, "[]").is_err());
    let con_nota = r#"[{"region":"X","lat":1,"lon":2,"celdas":1,"nota":"x","anios":{}}]"#;
    assert!(Datos::desde_json(con_nota, con_nota).is_ok());
}

#[tokio::test]
async fn callao_lleva_celdas_y_nota_y_lima_no_lleva_nota() {
    let (_, _, callao) = get("/power/callao", None).await;
    assert_eq!(callao["celdas"], 0);
    assert!(callao["nota"].is_string());
    let (_, _, lima) = get("/power/lima", None).await;
    assert!(lima["celdas"].as_u64().unwrap() >= 4);
    assert!(lima.get("nota").is_none());
}

#[test]
fn json_con_forma_incorrecta_se_rechaza() {
    assert!(Datos::desde_json(r#"[{"region":"X","lat":1,"lon":2,"celdas":4,"anios":{"2020":{"T2M":null}}}]"#, "[]").is_err());
    assert!(Datos::desde_json("[]", r#"[{"region":"X","lat":1,"lon":2,"celdas":4,"anios":{"2020":{"lluvia_mm_dia":null}}}]"#).is_err());
}

/// `openapi.json` (raíz del repo) es el contrato que copia el frontend: no puede quedar viejo.
/// Si cambias rutas o structs: `UPDATE_OPENAPI=1 cargo test openapi`.
#[test]
fn openapi_json_esta_al_dia() {
    let actual = nasa_challenge_backend::openapi::json();
    if std::env::var("UPDATE_OPENAPI").is_ok() {
        std::fs::write("openapi.json", &actual).unwrap();
    }
    let guardado = std::fs::read_to_string("openapi.json").unwrap_or_default();
    assert_eq!(guardado, actual, "openapi.json desactualizado: corre UPDATE_OPENAPI=1 cargo test openapi");
}

#[tokio::test]
async fn openapi_se_sirve_con_las_3_rutas() {
    let (s, _, b) = get("/api/openapi.json", None).await;
    assert_eq!(s, StatusCode::OK);
    let rutas = b["paths"].as_object().unwrap();
    assert!(rutas.contains_key("/api/variables") && rutas.contains_key("/api/zonas") && rutas.contains_key("/api/zonas/{id}"));
}
