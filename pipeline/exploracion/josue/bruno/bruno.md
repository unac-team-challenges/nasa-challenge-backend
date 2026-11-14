# Colección de Bruno: *Detective Josue*

**Dónde:** `bruno/coleccion/` (en la laptop de Josue: `~/bruno/Detective Josue`) · Bruno 4.3.0 · formato OpenCollection YAML

Bruno sirve para **mirar las APIs a mano** antes de programar. El pipeline real es Python. Por decisión del equipo (documento 13), no se usa Giovanni.

## Abrirla

1. Bruno → **Open Collection** → carpeta `bruno/coleccion/` de este repo.
2. Arriba a la derecha, elige el environment **Peru**.
3. Para AppEEARS, completa `edl_user` y `edl_pass`. Son **variables secretas**: Bruno las cifra fuera de los `.yml`.

## Peticiones

| Carpeta | Petición | Para qué | ¿Cuenta? |
|---|---|---|---|
| `1 POWER (Lab 1)` | `1 Piura` … `5 Iquitos` | Serie mensual 1981–2024 de 7 variables | No |
| `1 POWER (Lab 1)` | `6`–`9 Recuadro Peru NO/NE/SO/SE` | Malla de POWER sobre Perú. La API admite máximo 10° por lado | No |
| `3 AppEEARS (Lab 3)` | `1 Login AppEEARS` | Token; un script lo guarda **solo en memoria** | Sí |
| `3 AppEEARS (Lab 3)` | `2 Capas MOD13A3` | Nombres de capa, escala y relleno del NDVI | No |
| `3 AppEEARS (Lab 3)` | `3 Mis tareas` | Estado de las tareas | Sí |

Variables del environment: `power_params`, `inicio` y `fin` (se cambian en un solo lugar).

## Ejecutarla sin la interfaz

El CLI oficial (`npm i @usebruno/cli` → `bru run`) **no se pudo instalar**: el registro de npm no respondió desde el entorno de trabajo. En su lugar, `scripts/correr_bruno.py` lee los mismos `.yml`, sustituye las variables del environment y ejecuta cada petición. Las que necesitan credencial se saltan si no existen `EDL_USER` y `EDL_PASS` en el entorno del proceso.

```bash
.venv/bin/python scripts/correr_bruno.py bruno/coleccion    # → salida/bruno_resultados.{json,md}
```

Resultados: [resultados-bruno.md](resultados-bruno.md).

## Buenas prácticas aplicadas

- Credenciales solo como variables secretas: nunca en la URL ni en los `.yml`.
- Tokens con `bru.setEnvVar` solo en memoria.
- Cada petición tiene `docs` que dice qué mirar en la respuesta.
- `docs` entre comillas simples en YAML: un `:` sin comillas rompe el archivo (pasó y se corrigió).
