"""Laboratorio 0: inicia sesión en NASA Earthdata y guarda la sesión en tu equipo.
La contraseña se escribe solo en esta terminal; el script no la imprime ni la guarda en el proyecto.
"""
import earthaccess

print("Escribe tu usuario y tu contraseña de Earthdata (https://urs.earthdata.nasa.gov).")
auth = earthaccess.login(strategy="interactive", persist=True)
print()
print("Sesión iniciada:", bool(auth and auth.authenticated))
print("Listo. Ya puedes volver al chat.")
