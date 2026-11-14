# 01 · API Rust (Axum)

La API es pequeña (≈200 líneas), está bien separada en módulos y tiene tests de integración útiles. Los puntos de abajo son pulido, no fallas graves. Están ordenados por utilidad para la demo.

---

## 1. 404 sin cuerpo JSON

**Qué pasa.** `/power/noexiste` devuelve `404` con `{"error": ...}`, pero cualquier ruta que no existe (`/noexiste`, `/power/lima/` con barra final) devuelve `404` **con cuerpo vacío**.

```text
404 0B /power/lima/
404 0B /noexiste
```

**Por qué importa.** El frontend tiene que manejar dos formatos de error. Además, la barra final es un error muy común al construir URLs a mano.

**Cómo.** Un `fallback` en el router. Opcionalmente, quitar la barra final con `NormalizePathLayer` (ya viene en `tower-http`).

```rust
// src/routes/mod.rs
async fn no_existe(uri: axum::http::Uri) -> (StatusCode, Json<Value>) {
    (StatusCode::NOT_FOUND, Json(json!({"error": format!("ruta '{}' no existe", uri.path())})))
}

Router::new()
    // ...rutas...
    .fallback(no_existe)
```

Test sugerido: `assert_eq!(get("/noexiste", None).await.2["error"].is_string(), true);`

---

## 2. Sin `Cache-Control`

**Qué pasa.** Las respuestas no traen `Cache-Control` ni `ETag`. Los datos se embeben al compilar con `include_str!`, así que **no cambian mientras el binario vive**.

**Por qué importa.** Sin cabecera, el navegador y el CDN de Vercel no guardan nada: cada clic en el mapa vuelve a pedir lo mismo. En plan Hobby, cada invocación cuenta para el límite. En la demo, un caché del navegador también protege si la red se corta un momento.

**Cómo.** Una capa de `tower-http` (ya es dependencia, solo hay que activar la *feature* `set-header`):

```toml
tower-http = { version = "0.6", features = ["cors", "set-header"] }
```

```rust
// src/lib.rs
use axum::http::{header, HeaderValue};
use tower_http::set_header::SetResponseHeaderLayer;

routes::router()
    .layer(SetResponseHeaderLayer::if_not_present(
        header::CACHE_CONTROL,
        // 1 h en el navegador, 1 día en el CDN; se invalida al desplegar.
        HeaderValue::from_static("public, max-age=3600, s-maxage=86400"),
    ))
    .layer(cors)
```

> No hace falta `ETag`: con `s-maxage` el CDN ya sirve copias, y cada despliegue nuevo invalida el caché de Vercel.

---

## 3. Compresión: no hace falta todavía

`/gpm/lima` pesa ~2 KB. Comprimir con `CompressionLayer` ahorraría bytes que no importan. **Recomendación: no añadirlo** hasta que exista un endpoint de más de ~100 KB (por ejemplo, series mensuales de las 25 zonas). Vercel ya comprime en el borde.

---

## 4. Sin apagado ordenado

**Qué pasa.** Con `SIGTERM` el proceso muere al instante (probado). `main.rs` usa `.unwrap()` en `bind` y el mensaje de `expect` dice `"data/power.json inválido"` aunque el que falle sea `gpm.json`.

**Por qué importa.** Las plataformas de contenedores (Cloud Run, Fly.io, Render, el Docker de Vercel) mandan `SIGTERM` antes de matar el proceso. Sin apagado ordenado se cortan las peticiones en curso. El mensaje de error equivocado hace perder tiempo al depurar.

**Cómo.**

```rust
// src/main.rs
let datos = Arc::new(Datos::cargar().expect("data/*.json no encaja con src/models"));
let l = tokio::net::TcpListener::bind(&addr).await
    .unwrap_or_else(|e| panic!("no se pudo abrir {addr}: {e}"));
axum::serve(l, app(datos, cfg.origenes))
    .with_graceful_shutdown(async { tokio::signal::ctrl_c().await.ok(); })
    .await
    .unwrap();
```

> `ctrl_c` cubre `SIGINT`. Para `SIGTERM` en Linux hace falta `tokio::signal::unix::signal(SignalKind::terminate())` (activar la *feature* `signal` de tokio). Solo vale la pena si se despliega en contenedor.

**Logs.** Hoy no hay ningún log por petición. Si algo falla en la demo, no hay rastro. La opción estándar es `tracing` + `tracing-subscriber` + `TraceLayer` de `tower-http`. Son 2 dependencias nuevas: añadir **solo si se despliega como servidor** (en Vercel Functions los logs ya los da la plataforma).

---

## 5. Campos desconocidos se ignoran en silencio

**Qué pasa.** `serde` rechaza `null` (bien, hay test), pero **acepta campos de más**. Si el pipeline renombra `lluvia_mm_dia` a `lluvia_mm` y deja el viejo, o añade `nota`, la API arranca igual y el campo nuevo desaparece de la respuesta sin aviso.

**Por qué importa.** `docs/reglas-datos.md` §4 ya planea un campo `nota`. El contrato es "si el JSON no encaja, la API no arranca"; hoy eso solo es cierto a medias.

**Cómo.** Una línea por struct:

```rust
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Medidas { /* ... */ }
```

Y otra en `models::Region<M>`. Test: el mismo `json_con_forma_incorrecta_se_rechaza` con un campo extra.

---

## 6. Las regiones de `/regiones` solo salen de `power.json`

**Qué pasa.** `/regiones` lista `power.json`. Si `gpm.json` tuviera otra región o le faltara una, `/regiones` no lo mostraría. Hoy los nombres coinciden (verificado), pero nada lo garantiza.

**Cómo.** En `Datos::desde_json`, comprobar que ambos índices tienen las mismas claves y devolver error si no. Son 3 líneas y convierten un error silencioso en un fallo de arranque, que es la filosofía del repo.

```rust
if indexar(&regiones).keys().collect::<BTreeSet<_>>() != indexar(&gpm).keys().collect() {
    // devolver un error propio, o `panic!` con mensaje claro
}
```

---

## 7. Detalles menores

| Punto | Por qué | Cómo |
|---|---|---|
| El mensaje de 404 repite la entrada completa (probado con 5000 caracteres) | Respuesta inflada; reflejar entrada no es grave en JSON, pero no aporta | Recortar: `r.chars().take(60).collect::<String>()` |
| `edition = "2021"` | La edición 2024 es estable desde Rust 1.85 | `cargo fix --edition` y cambiar a `2024`; sin prisa |
| Sin `rust-version` ni `rust-toolchain.toml` | Cada persona y el CI pueden compilar con versiones distintas | `rust-toolchain.toml` con `channel = "1.9x"` |
| `tower-http` 0.6 | Existe 0.7.1 | Subir junto con `utoipa` 6 en un solo PR, no antes de la demo |
| Cada petición clona la región (`.cloned()`) | Irrelevante con 25 regiones | **No tocar.** Solo si se sirven series grandes |

---

## 8. Notas sobre el PR #21 (OpenAPI)

El PR es buena idea: el test `openapi_json_esta_al_dia` que compara el `openapi.json` guardado con el generado es exactamente el tipo de guardia que evita sorpresas en el frontend. Observaciones:

1. **`utoipa = "5"`**: ya existe `utoipa 6.0.0` y `utoipa-axum 0.3.0`. Si se va a adoptar ahora, mejor empezar en 6 que migrar después.
2. **`/api/zonas` exige `?variable=` pero no la usa** (`variable(p)?;` valida y descarta). O se usa para algo (por ejemplo, devolver solo zonas con datos de esa variable) o se quita del contrato. Un parámetro obligatorio que no cambia nada confunde a quien consume la API.
3. **`/api/variables` recorre las 25 series en cada petición.** Es poco trabajo, pero choca con la regla "la API nunca calcula". Se puede calcular una vez en `Datos::cargar()`.
4. **Conviven dos API**: `/power/{region}` + `/gpm/{region}` (por nombre) y `/api/zonas/{id}` (por ubigeo). Conviene decidir cuál consume el frontend y marcar la otra como interna o quitarla, para no mantener dos contratos.
5. Los ubigeos del 01 al 25 coinciden con INEI (verificado contra el CSV de `pipeline/exploracion/josue/resultados/`).
