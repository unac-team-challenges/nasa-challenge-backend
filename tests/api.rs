use axum::{
    body::{to_bytes, Body},
    http::{Request, StatusCode},
    Router,
};
use nasa_challenge_backend::{
    app,
    data::{Datos, Estado, Fuentes},
    models::{power, variable::Variable, zona::Status},
};
use serde_json::Value;
use std::sync::{Arc, LazyLock};
use tower::ServiceExt;

/// Se cargan y validan una vez para todos los tests.
static DATOS: LazyLock<Estado> = LazyLock::new(|| Arc::new(Datos::cargar().unwrap()));

fn router() -> Router {
    app(DATOS.clone(), vec!["https://demo.vercel.app".into()])
}

async fn get(ruta: &str, origen: Option<&str>) -> (StatusCode, Option<String>, Value) {
    let mut req = Request::get(ruta);
    if let Some(o) = origen {
        req = req.header("origin", o);
    }
    let res = router()
        .oneshot(req.body(Body::empty()).unwrap())
        .await
        .unwrap();
    let status = res.status();
    let acao = res
        .headers()
        .get("access-control-allow-origin")
        .map(|v| v.to_str().unwrap().to_string());
    let body = to_bytes(res.into_body(), usize::MAX).await.unwrap();
    (
        status,
        acao,
        serde_json::from_slice(&body).unwrap_or(Value::Null),
    )
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
    assert!(anios
        .values()
        .all(|m| ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN"]
            .iter()
            .all(|k| m[*k].is_number())));
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
    for ruta in [
        "/power/ancash",
        "/power/%C3%81ncash",
        "/power/ANCASH",
        "/power/san%20martin",
    ] {
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
    for o in [
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "https://demo.vercel.app",
    ] {
        assert_eq!(get("/regiones", Some(o)).await.1.as_deref(), Some(o));
    }
    for o in ["http://localhost.evil.com", "https://otro.vercel.app"] {
        assert_eq!(get("/regiones", Some(o)).await.1, None, "{o}");
    }
}

#[tokio::test]
async fn api_variables_lista_lluvia_temperatura_e_imerg() {
    let (s, _, b) = get("/api/variables", None).await;
    assert_eq!(s, StatusCode::OK);
    let ids: Vec<_> = b
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v["id"].as_str().unwrap())
        .collect();
    assert_eq!(ids, ["lluvia", "temperatura", "lluvia_imerg"]);
    assert!(b[0]["anio_inicio"].is_number() && b[0]["unidad"] == "mm/día");
}

#[tokio::test]
async fn api_zonas_son_25_con_ubigeo_texto() {
    let (s, _, b) = get("/api/zonas?variable=lluvia", None).await;
    assert_eq!(s, StatusCode::OK);
    let zonas = b.as_array().unwrap();
    assert_eq!(zonas.len(), 25);
    let mut ids: Vec<_> = zonas
        .iter()
        .map(|z| z["id"].as_str().unwrap().to_string())
        .collect();
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
    for (var, unidad) in [
        ("lluvia", "mm/día"),
        ("temperatura", "°C"),
        ("lluvia_imerg", "mm/día"),
    ] {
        let (s, _, b) = get(&format!("/api/zonas/15?variable={var}"), None).await;
        assert_eq!(s, StatusCode::OK);
        assert_eq!(
            (b["id"].as_str(), b["nombre"].as_str(), b["unidad"].as_str()),
            (Some("15"), Some("Lima"), Some(unidad))
        );
        let serie = b["serie"].as_array().unwrap();
        assert!(!serie.is_empty());
        assert!(serie
            .iter()
            .all(|p| p["anio"].is_number() && p["valor"].is_number()));
    }
}

#[tokio::test]
async fn api_variable_es_obligatoria_y_valida() {
    for ruta in [
        "/api/zonas",
        "/api/zonas/15",
        "/api/zonas?variable=viento",
        "/api/zonas/15?variable=",
    ] {
        let (s, _, b) = get(ruta, None).await;
        assert_eq!(s, StatusCode::BAD_REQUEST, "{ruta}");
        assert!(b["error"].as_str().unwrap().contains("lluvia"));
    }
}

#[tokio::test]
async fn api_variable_ignora_mayusculas_y_espacios() {
    for v in ["LLUVIA", "Lluvia", "%20lluvia%20"] {
        let (s, _, b) = get(&format!("/api/zonas/15?variable={v}"), None).await;
        assert_eq!(s, StatusCode::OK, "{v}");
        assert_eq!(b["variable"], "lluvia", "{v}");
    }
}

/// `Variable::parse` compara con `eq_ignore_ascii_case`: un id con tilde (p. ej. "vegetación")
/// dejaría de ignorar mayúsculas en esa letra. Si este test falla, vuelve a `to_lowercase()`.
#[test]
fn ids_de_variable_son_ascii() {
    assert!(Variable::TODAS.iter().all(|v| v.id().is_ascii()));
}

#[tokio::test]
async fn api_zona_inexistente_da_404() {
    for id in ["00", "26", "99", "lima"] {
        assert_eq!(
            get(&format!("/api/zonas/{id}?variable=lluvia"), None)
                .await
                .0,
            StatusCode::NOT_FOUND,
            "{id}"
        );
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
    assert!(
        b["error"].as_str().unwrap().len() < 200,
        "el error no debe reflejar toda la entrada"
    );
}

#[tokio::test]
async fn datos_se_cachean_pero_health_no() {
    let cabecera = |ruta: &'static str| async move {
        let res = router()
            .oneshot(Request::get(ruta).body(Body::empty()).unwrap())
            .await
            .unwrap();
        res.headers()
            .get("cache-control")
            .map(|v| v.to_str().unwrap().to_string())
    };
    assert!(cabecera("/gpm/lima").await.unwrap().contains("s-maxage"));
    assert_eq!(cabecera("/health").await.as_deref(), Some("no-store"));
}

/// `Datos` con `power.json` y `gpm.json` cambiados; el resto, los embebidos.
fn con_power_gpm(power: &str, gpm: &str) -> Result<Datos, serde_json::Error> {
    Datos::desde(Fuentes {
        power,
        gpm,
        ..Fuentes::EMBEBIDAS
    })
}

/// Aplica `f` a un JSON y lo devuelve como texto.
fn editar(json: &str, f: impl FnOnce(&mut Value)) -> String {
    let mut v: Value = serde_json::from_str(json).unwrap();
    f(&mut v);
    v.to_string()
}

#[test]
fn campos_desconocidos_y_regiones_distintas_se_rechazan() {
    let forma_ok = |json: &str| serde_json::from_str::<Vec<power::Region>>(json).is_ok();
    let medida_ok = r#"{"PRECTOTCORR":1,"T2M":2,"T2M_MAX":3,"T2M_MIN":0}"#;
    let region = |m: &str| {
        format!(r#"[{{"region":"X","lat":1,"lon":2,"celdas":4,"anios":{{"2020":{m}}}}}]"#)
    };
    let gpm_ok = region(r#"{"lluvia_mm_dia":1}"#);
    assert!(forma_ok(&region(medida_ok)));
    // un campo de más en las medidas
    let power_extra = region(r#"{"PRECTOTCORR":1,"T2M":2,"T2M_MAX":3,"T2M_MIN":0,"nuevo":1}"#);
    assert!(!forma_ok(&power_extra));
    assert!(con_power_gpm(&power_extra, &gpm_ok).is_err());
    // un campo de más en la región
    let region_extra = r#"[{"region":"X","lat":1,"lon":2,"celdas":4,"nuevo":"x","anios":{}}]"#;
    assert!(con_power_gpm(region_extra, "[]").is_err());
    // power.json y gpm.json con regiones distintas
    let otra = gpm_ok.replace("\"X\"", "\"Y\"");
    assert!(con_power_gpm(&region(medida_ok), &otra).is_err());
    // `celdas` es obligatorio; `nota` es opcional
    assert!(!forma_ok(r#"[{"region":"X","lat":1,"lon":2,"anios":{}}]"#));
    assert!(forma_ok(
        r#"[{"region":"X","lat":1,"lon":2,"celdas":1,"nota":"x","anios":{}}]"#
    ));
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

#[tokio::test]
async fn zona_devuelve_la_nota_de_su_variable() {
    for var in ["temperatura", "lluvia", "lluvia_imerg"] {
        let (_, _, callao) = get(&format!("/api/zonas/07?variable={var}"), None).await;
        assert!(callao["nota"].is_string(), "Callao/{var}");
        let (_, _, lima) = get(&format!("/api/zonas/15?variable={var}"), None).await;
        assert!(lima.get("nota").is_none(), "Lima/{var}");
    }
    // Lambayeque tiene 3 celdas en POWER pero muchas en IMERG: la nota depende de la fuente
    let (_, _, t) = get("/api/zonas/14?variable=temperatura", None).await;
    let (_, _, l) = get("/api/zonas/14?variable=lluvia", None).await;
    let (_, _, i) = get("/api/zonas/14?variable=lluvia_imerg", None).await;
    assert!(t["nota"].is_string() && l["nota"].is_string() && i.get("nota").is_none());
}

#[test]
fn json_con_forma_incorrecta_se_rechaza() {
    assert!(con_power_gpm(
        r#"[{"region":"X","lat":1,"lon":2,"celdas":4,"anios":{"2020":{"T2M":null}}}]"#,
        "[]"
    )
    .is_err());
    assert!(con_power_gpm(
        "[]",
        r#"[{"region":"X","lat":1,"lon":2,"celdas":4,"anios":{"2020":{"lluvia_mm_dia":null}}}]"#
    )
    .is_err());
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
    assert_eq!(
        guardado, actual,
        "openapi.json desactualizado: corre UPDATE_OPENAPI=1 cargo test openapi"
    );
}

#[tokio::test]
async fn openapi_se_sirve_con_las_4_rutas() {
    let (s, _, b) = get("/api/openapi.json", None).await;
    assert_eq!(s, StatusCode::OK);
    let rutas = b["paths"].as_object().unwrap();
    assert!(
        rutas.contains_key("/api/variables")
            && rutas.contains_key("/api/zonas")
            && rutas.contains_key("/api/zonas/{id}")
            && rutas.contains_key("/api/vegetacion")
    );
}

fn status_valido(v: &Value) -> bool {
    serde_json::from_value::<Status>(v.clone()).is_ok()
}

#[tokio::test]
async fn api_zonas_traen_stats() {
    for var in ["lluvia", "temperatura", "lluvia_imerg"] {
        let (s, _, b) = get(&format!("/api/zonas?variable={var}"), None).await;
        assert_eq!(s, StatusCode::OK);
        let zonas = b.as_array().unwrap();
        assert_eq!(zonas.len(), 25, "{var}");
        for z in zonas {
            assert!(z["celdas"].is_u64(), "{var}/{}", z["id"]);
            assert!(status_valido(&z["stats"]["status"]), "{var}/{}", z["id"]);
            assert!(z.get("serie").is_none(), "la lista va sin serie");
        }
    }
}

#[tokio::test]
async fn imerg_trae_aviso_2014_y_power_no() {
    let (_, _, l) = get("/api/zonas/15?variable=lluvia_imerg", None).await;
    let st = &l["stats"];
    assert!(st["aviso"].as_str().unwrap().contains("2014"));
    assert!(st["q_value"].is_number() && st["pct_change_per_decade"].is_number());
    assert!(status_valido(&st["status"]));
    let (_, _, t) = get("/api/zonas/15?variable=temperatura", None).await;
    assert!(t["stats"].get("aviso").is_none() && t["stats"].get("pct_change_per_decade").is_none());
    assert!(t["celdas"].is_u64());
    // La lluvia principal (POWER) no lleva el aviso del salto de satélites de IMERG
    let (_, _, p) = get("/api/zonas?variable=lluvia", None).await;
    for z in p.as_array().unwrap() {
        let aviso = z["stats"]["aviso"].as_str().unwrap_or("");
        assert!(!aviso.contains("2014"), "lluvia/{}", z["id"]);
        assert!(
            z["stats"]["pct_change_per_decade"].is_number(),
            "lluvia/{}",
            z["id"]
        );
    }
}

/// Opción C: la lluvia principal (POWER) puede salir «real»; IMERG, la segunda fuente, nunca.
#[tokio::test]
async fn lluvia_power_puede_ser_real_e_imerg_nunca() {
    let reales = |b: &Value| {
        b.as_array()
            .unwrap()
            .iter()
            .filter(|z| z["stats"]["status"] == "real")
            .count()
    };
    let (_, _, power) = get("/api/zonas?variable=lluvia", None).await;
    let (_, _, imerg) = get("/api/zonas?variable=lluvia_imerg", None).await;
    assert!(reales(&power) > 0);
    assert_eq!(reales(&imerg), 0);
    let (_, _, v) = get("/api/variables", None).await;
    assert!(v[0]["fuente"].as_str().unwrap().contains("POWER"));
    assert!(v[2]["fuente"].as_str().unwrap().contains("IMERG"));
}

#[tokio::test]
async fn pocos_datos_lleva_nota() {
    let (_, _, callao) = get("/api/zonas/07?variable=temperatura", None).await;
    assert_eq!(callao["stats"]["status"], "pocos_datos");
    assert!(callao["nota"].is_string());
    for var in ["lluvia", "temperatura", "lluvia_imerg"] {
        let (_, _, b) = get(&format!("/api/zonas?variable={var}"), None).await;
        for z in b
            .as_array()
            .unwrap()
            .iter()
            .filter(|z| z["stats"]["status"] == "pocos_datos")
        {
            assert!(z["nota"].is_string(), "{var}/{}", z["id"]);
        }
    }
}

#[tokio::test]
async fn serie_y_stats_hablan_del_mismo_periodo() {
    for var in ["lluvia", "temperatura", "lluvia_imerg"] {
        for n in 1..=25 {
            let (s, _, b) = get(&format!("/api/zonas/{n:02}?variable={var}"), None).await;
            assert_eq!(s, StatusCode::OK);
            let (serie, st) = (b["serie"].as_array().unwrap(), &b["stats"]);
            assert_eq!(
                serie.first().unwrap()["anio"],
                st["year_start"],
                "{var}/{n:02}"
            );
            assert_eq!(
                serie.last().unwrap()["anio"],
                st["year_end"],
                "{var}/{n:02}"
            );
            assert_eq!(
                serie.len() as u64,
                st["n_years"].as_u64().unwrap(),
                "{var}/{n:02}"
            );
        }
    }
}

#[tokio::test]
async fn variables_salen_del_archivo() {
    let (_, _, b) = get("/api/variables", None).await;
    let archivo: Value = serde_json::from_str(Fuentes::EMBEBIDAS.variables).unwrap();
    assert_eq!(b, archivo);
}

#[tokio::test]
async fn ids_que_no_son_ubigeo_exacto_dan_404() {
    for id in ["7", "007", "15 ", "Lima"] {
        let ruta = format!("/api/zonas/{}?variable=lluvia", id.replace(' ', "%20"));
        assert_eq!(get(&ruta, None).await.0, StatusCode::NOT_FOUND, "{id}");
    }
}

#[tokio::test]
async fn detalle_trae_la_zona_entera() {
    for var in ["lluvia", "temperatura", "lluvia_imerg"] {
        let (_, _, lista) = get(&format!("/api/zonas?variable={var}"), None).await;
        for z in lista.as_array().unwrap() {
            let (_, _, d) = get(
                &format!("/api/zonas/{}?variable={var}", z["id"].as_str().unwrap()),
                None,
            )
            .await;
            for (k, v) in z.as_object().unwrap() {
                assert_eq!(&d[k], v, "{var}/{}: campo {k}", z["id"]);
            }
        }
    }
}

type Cambio = fn(&mut Value);

#[test]
fn zonas_y_variables_mal_formadas_se_rechazan() {
    let e = Fuentes::EMBEBIDAS;
    let con_zonas = |f: Cambio| {
        let z = editar(e.zonas[0], f);
        Datos::desde(Fuentes {
            zonas: [&z, e.zonas[1], e.zonas[2]],
            ..e
        })
    };
    let con_variables = |f: Cambio| {
        let v = editar(e.variables, f);
        Datos::desde(Fuentes { variables: &v, ..e })
    };
    assert!(
        con_zonas(|_| {}).is_ok(),
        "los datos embebidos sin cambios cargan"
    );
    let malos: [(&str, Cambio); 12] = [
        ("campo desconocido en la zona", |z| z[0]["nuevo"] = 1.into()),
        ("campo desconocido en stats", |z| {
            z[0]["stats"]["nuevo"] = 1.into()
        }),
        ("status inválido", |z| {
            z[0]["stats"]["status"] = "quizas".into()
        }),
        ("falta un campo de stats", |z| {
            z[0]["stats"].as_object_mut().unwrap().remove("q_value");
        }),
        ("24 zonas", |z| {
            z.as_array_mut().unwrap().pop();
        }),
        ("ids desordenados", |z| z.as_array_mut().unwrap().swap(0, 1)),
        ("nombre que no es el del ubigeo", |z| {
            z[0]["nombre"] = "Lima".into()
        }),
        ("year_end fuera de la serie", |z| {
            z[0]["stats"]["year_end"] = 2030.into()
        }),
        ("n_years no cuadra con la serie", |z| {
            z[0]["stats"]["n_years"] = 23.into()
        }),
        ("periodo fuera del de variables.json", |z| {
            z[0]["stats"]["year_end"] = 2025.into();
            z[0]["stats"]["n_years"] = 25.into();
        }),
        ("celdas distintas de su fuente", |z| {
            z[0]["celdas"] = 1.into()
        }),
        ("nota que su fuente no tiene", |z| {
            z[14]["nota"] = "x".into()
        }),
    ];
    // Una zona con su propio periodo, dentro del de variables.json (p. ej. le falta 2001), es válida.
    assert!(con_zonas(|z| {
        z[0]["stats"]["year_start"] = 2002.into();
        z[0]["stats"]["n_years"] = 23.into();
    })
    .is_ok());
    for (caso, f) in malos {
        assert!(con_zonas(f).is_err(), "{caso}");
    }
    assert!(
        con_variables(|v| {
            v.as_array_mut().unwrap().pop();
        })
        .is_err(),
        "falta una variable"
    );
    assert!(
        con_variables(|v| v[0]["nuevo"] = 1.into()).is_err(),
        "campo desconocido en variables.json"
    );
}

/// Valores de `data/ndvi.json` en 2001 y 2024: los mismos del Lab 3 de Favio
/// (`pipeline/exploracion/favio/resultados/lab3_resumen.json`), servidos tal cual.
#[tokio::test]
async fn api_vegetacion_trae_las_2_zonas_del_caso_2() {
    let (s, _, b) = get("/api/vegetacion", None).await;
    assert_eq!(s, StatusCode::OK);
    let zonas = b.as_array().unwrap();
    let ids: Vec<_> = zonas.iter().map(|z| z["id"].as_str().unwrap()).collect();
    assert_eq!(ids, ["chavimochic", "ica-villacuri"]);
    // (ubigeo, NDVI 2001, km² 2001, NDVI 2024, km² 2024)
    let esperado = [
        ("13", 0.1906, 188.9, 0.3104, 355.5),
        ("11", 0.1403, 117.6, 0.198, 221.5),
    ];
    for (z, (ubigeo, n01, a01, n24, a24)) in zonas.iter().zip(esperado) {
        assert_eq!(z["ubigeo"], ubigeo);
        assert!(z["unidad_geografica"]
            .as_str()
            .unwrap()
            .contains("recuadro"));
        assert!(status_valido(&z["stats"]["status"]));
        assert_eq!(z["stats"]["status"], "real", "{}", z["id"]);
        let serie = z["serie"].as_array().unwrap();
        assert_eq!(serie.len(), 24);
        assert_eq!(z["stats"]["n_years"], 24);
        let (p01, p24) = (&serie[0], &serie[23]);
        assert_eq!(
            (p01["anio"].as_u64(), p24["anio"].as_u64()),
            (Some(2001), Some(2024))
        );
        assert_eq!(p01["ndvi_anual"], n01);
        assert_eq!(p01["area_verde_km2"], a01);
        assert_eq!(p24["ndvi_anual"], n24);
        assert_eq!(p24["area_verde_km2"], a24);
        // p y q nunca se publican como 0: el piso es 0,000001
        assert!(
            z["stats"]["p_value"].as_f64().unwrap() > 0.0
                && z["stats"]["q_value"].as_f64().unwrap() > 0.0
        );
    }
}

#[test]
fn vegetacion_mal_formada_se_rechaza() {
    let e = Fuentes::EMBEBIDAS;
    let con_ndvi = |f: Cambio| {
        let n = editar(e.ndvi, f);
        Datos::desde(Fuentes { ndvi: &n, ..e })
    };
    assert!(con_ndvi(|_| {}).is_ok(), "ndvi.json sin cambios carga");
    let malos: [(&str, Cambio); 13] = [
        ("sin zonas", |z| z.as_array_mut().unwrap().clear()),
        ("campo desconocido en la zona", |z| z[0]["nuevo"] = 1.into()),
        ("campo desconocido en un año", |z| {
            z[0]["serie"][0]["nuevo"] = 1.into()
        }),
        ("NDVI fuera de −1 a 1", |z| {
            z[0]["serie"][0]["ndvi_anual"] = 1.5.into()
        }),
        ("área verde negativa", |z| {
            z[0]["serie"][0]["area_verde_km2"] = (-1.0).into()
        }),
        ("ubigeo inexistente", |z| z[0]["ubigeo"] = "99".into()),
        ("departamento que no es el del ubigeo", |z| {
            z[0]["departamento"] = "Ica".into()
        }),
        ("sin unidad geográfica", |z| {
            z[0]["unidad_geografica"] = " ".into()
        }),
        ("lat fuera del recuadro", |z| z[0]["lat"] = 0.into()),
        ("años desordenados en la serie", |z| {
            z[0]["serie"].as_array_mut().unwrap().swap(0, 1)
        }),
        ("n_years no cuadra con serie", |z| {
            z[0]["stats"]["n_years"] = 23.into()
        }),
        ("id repetido", |z| {
            let copia = z[0].clone();
            z.as_array_mut().unwrap().push(copia);
        }),
        ("status inválido", |z| {
            z[0]["stats"]["status"] = "quizas".into()
        }),
    ];
    for (caso, f) in malos {
        assert!(con_ndvi(f).is_err(), "{caso}");
    }
    // El error dice qué zona falla
    let msg = con_ndvi(|z| z[1]["ubigeo"] = "99".into())
        .err()
        .unwrap()
        .to_string();
    assert!(msg.contains("ica-villacuri"), "{msg}");
}
