# ci/dependabot-developer

PR → `developer`.

## Cambiado
- `.github/dependabot.yml`: `target-branch: developer` en los tres bloques. Antes dependabot abría sus PRs contra `main`, saltándose el flujo (PR a `developer`; `main` solo desde `developer`).

## Notas
- Las PRs #30–#33 (abiertas contra `main`) se cierran y dependabot las recrea contra `developer`.
