# inputs/ — entradas congeladas por hash (no versionadas)

Este repositorio es **público**. Por eso las dos entradas binarias del proyecto **no se
suben a git**; se colocan aquí localmente y se verifican por contenido:

| Archivo | Bytes | SHA-256 | Por qué no está en git |
|---|---:|---|---|
| `P1070614.JPG` | 4,260,352 | `8f6e3b6f…ec529d` | fotografía de personas reales con etiquetas de nombre visibles |
| `pragma-extension.zip` | 3,528,382 | `a7fa93d2…a9d80` | extensión v1.2.0; invariante: no modificar; se conserva fuera de git |

```bash
cd pragma/inputs && sha256sum -c INPUTS_SHA256.txt      # Linux
cd pragma/inputs && shasum -a 256 -c INPUTS_SHA256.txt  # macOS
```

El nombre puede variar; el contenido no. Todas las herramientas de `pragma_ae` buscan la
foto por hash y se niegan a trabajar con otra imagen.

Si en el futuro el repositorio pasa a ser privado y quieres versionar estas entradas,
elimina las reglas `inputs/*` del `.gitignore` de forma explícita; no lo hagas por defecto.
