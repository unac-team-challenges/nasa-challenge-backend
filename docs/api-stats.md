# Servir los `stats` en la API (para Sebastian)

`pipeline/tendencias.py` (#28) ya escribe las tendencias en `data/`. **Falta que la API Rust las sirva.** Esta guía dice qué hacer, con qué archivos y cómo comprobar que quedó bien. Reglas generales: [`CONDITIONS.md`](../CONDITIONS.md) y [`reglas-datos.md`](reglas-datos.md). La API **nunca calcula**: solo lee estos JSON y los devuelve.

## 1. Qué hay y qué falta

| Archivo (ya existe) | Contenido | Ruta que lo debe servir |
|---|---|---|
| `data/variables.json` | `id`, `unidad`, `fuente`, `descripcion`, `anio_inicio`, `anio_fin` | `GET /api/variables` |
| `data/zonas/{variable}.json` | 25 zonas sin serie: `id`, `nombre`, `lat`, `lon`, `celdas`, `nota?`, `stats` | `GET /api/zonas?variable=` |
| `data/zonas/{variable}/{id}.json` | La zona con `variable`, `unidad`, `fuente`, `serie` y `stats` | `GET /api/zonas/{id}?variable=` |

Hoy la API ya sirve esas tres rutas, pero **sin `stats`**: calcula `variables` y la serie desde `power.json`/`gpm.json`. Hay que añadirlos.

`stats` (todos son números salvo los marcados):

| Campo | Nota |
|---|---|
| `year_start`, `year_end`, `n_years` | enteros; hoy 2001, 2024, 24 |
| `slope_per_decade` | unidad de la variable por década |
| `intercept` | **en años calendario**: `valor ≈ intercept + slope_per_decade / 10 × año` (no por índice 0, 1, 2…) |
| `ci_low`, `ci_high` | intervalo 95 % de la pendiente, por década |
| `p_value`, `q_value` | antes y después de Benjamini-Hochberg |
| `lag1` | autocorrelación |
| `pct_change_per_decade` | **solo lluvia** (opcional) |
| `status` (texto) | `"real"` · `"posible_casualidad"` · `"pocos_datos"` |
| `aviso` (texto, opcional) | **siempre en lluvia** (salto de IMERG en 2014); también si `lag1 > 0.5` |

## 2. Qué hacer

1. **Modelo** (`src/models/`): una `struct Stats` con esos campos (`pct_change_per_decade` y `aviso` como `Option`, con `skip_serializing_if`) y un `enum Status` con los tres valores en minúsculas y `_`. `#[derive(Deserialize, Serialize, ToSchema)]` y `#[serde(deny_unknown_fields)]`, como el resto de modelos: si el pipeline añade un campo y la API no lo conoce, debe fallar al arrancar.
2. **Datos** (`src/data.rs`): embebe con `include_str!` `data/variables.json`, `data/zonas/lluvia.json` y `data/zonas/temperatura.json` (tres constantes, sin crates nuevos). Valida al cargar: 25 zonas por variable y los `id` son exactamente `01`–`25`. Un JSON malo debe impedir que la API arranque (igual que hoy).
   - La serie sigue saliendo de `power.json`/`gpm.json`, **pero solo los años entre `year_start` y `year_end` del `stats`**, para que serie y tendencia hablen del mismo periodo (el cron puede añadir años a esos JSON).
   - Alternativa: servir los 50 archivos `data/zonas/{variable}/{id}.json` con la crate `include_dir` (es lo que sugiere el `07` del Drive). Más fiel al contrato, pero una dependencia más. Elige una y déjala escrita en el changelog.
3. **Rutas** (`src/routes/api.rs`, `src/schema.rs`):
   - `Zona` (lista) gana `celdas`, `nota?` y `stats`: el mapa pinta el semáforo con esto.
   - `ZonaDetalle` gana `stats` (y `celdas`).
   - `/api/variables` puede leerse de `variables.json` en vez de recalcularse.
   - **No cambies ningún valor**: ni el `status`, ni el `aviso`. Se devuelven tal cual.
4. **OpenAPI:** `UPDATE_OPENAPI=1 cargo test openapi` y sube el `openapi.json` nuevo (un test falla si queda viejo).
5. **Tests** (`tests/api.rs`) y `tests/e2e.sh`:
   - `/api/zonas?variable=lluvia` devuelve 25 zonas y todas con `stats.status` válido.
   - `/api/zonas/15?variable=lluvia` trae `stats` y su `aviso` menciona 2014; temperatura no lo trae.
   - Una zona con `pocos_datos` (p. ej. Callao) lleva `nota` y `stats.status == "pocos_datos"`.
   - `year_start`/`year_end` de `stats` coinciden con el primer y último año de `serie`.
   - Un `data/zonas/*.json` con un campo desconocido se rechaza (como `campos_desconocidos_y_regiones_distintas_se_rechazan`).
6. **Docs:** la tabla de endpoints de `README.md`, `docs/datos.md` si cambia la forma, y quita el «llega con el cálculo de…» de `src/schema.rs`.

## 3. Trampas

- **`include_str!` se evalúa al compilar:** si regeneras `data/zonas/*` hay que recompilar. Un JSON con `NaN` impide arrancar.
- **No recalcules ni redondees** `stats` en Rust: el pipeline ya dejó los decimales que quiere.
- **No ocultes el `aviso` de lluvia.** El equipo decidió usar IMERG sabiendo que baja ~10 % en los 25 departamentos desde 2014 (cambio TRMM → GPM). Cómo mostrarlo («real» sí o no) es una decisión de producto aparte; la API solo lo transporta.
- **`nota` y `aviso` son cosas distintas:** `nota` = pocas celdas (fuente), `aviso` = cuidado al interpretar la tendencia.
- **Ids como texto:** `"07"`, no `7`. `07` = Callao, `15` = Lima.

## 4. Listo cuando

- [ ] `bash tests/e2e.sh` → TODO OK, y el CI `e2e` en verde.
- [ ] `curl 'localhost:3000/api/zonas/15?variable=lluvia'` devuelve `stats` con `status`, `q_value` y `aviso`.
- [ ] `openapi.json` actualizado y documenta `Stats`.
- [ ] Rama `feat/api-stats`, `changelog/feat-api-stats.md`, PR a `developer` y 1 aprobación de otra persona.
- [ ] Avisa al frontend: los campos están en `openapi.json`.
