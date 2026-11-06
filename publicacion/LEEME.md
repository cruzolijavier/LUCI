# Cómo publicar una versión nueva de LUCI

LUCI tiene **un único repositorio público**: `https://github.com/cruzolijavier/LUCI`. Contiene todo el código
y, en la pestaña **Releases**, los ejecutables que genera GitHub Actions.

## Publicar una versión (siempre igual)

Desde la carpeta de LUCI, en PowerShell:

```powershell
.\publicar.ps1 -Version 0.3.1 -Notas "- Lo que ha cambiado`n- Otra cosa"
```

El script cambia el número de versión, hace commit de todo, crea la etiqueta `v0.3.1` y lo sube.
GitHub compila (unos 10-15 minutos, pestaña **Actions**) y crea la release con dos archivos:

- `LUCI_windows.zip`: la carpeta `LUCI` (LUCI.exe + luci-cli.exe + `_internal`).
- `version.json`: versión, SHA-256 y tamaño del zip. Es lo que lee el botón **Update LUCI**.

## Qué ve quien ya tiene LUCI

- Al abrir LUCI (y cada hora) mira `version.json`. Si hay una versión nueva sale un aviso una vez y el botón
  **Update LUCI** (arriba a la derecha) muestra una **!** roja.
- Al pulsar **Update now**: descarga el zip, comprueba el SHA-256, cierra LUCI, sustituye los archivos de la
  carpeta y lo vuelve a abrir. No se mueve ni se renombra nada: el acceso directo sigue funcionando.
- Los entornos, ajustes y la clave de OpenAI están en `%LOCALAPPDATA%\LUCI`, fuera de la carpeta del
  programa, así que no se tocan.
- No actualiza si hay un workflow en ejecución, ni si la carpeta de LUCI no es escribible
  (por ejemplo `C:\Program Files`).

## La clave de OpenAI y el robot

Los ejecutables de GitHub **no llevan ninguna clave** (el repositorio es público: cualquiera podría extraerla
del .exe). El robot del asistente aparece **en gris** hasta que alguien pega su clave en
**Tools > Settings > OpenAI API key**; entonces se enciende solo. `packaging/build_exe.bat` (compilación local)
sigue pudiendo empaquetar una clave para uso interno, pero ese .exe no debe subirse a GitHub.

## Primera vez

1. Crear en GitHub el repositorio público vacío `LUCI` (sin README ni .gitignore).
2. En la carpeta de LUCI:

   ```powershell
   git init -b main
   git add -A
   git status        # comprueba que NO aparece openai_key.txt ni bundled_key.txt
   git commit -m "LUCI: código inicial"
   git remote add origin https://github.com/cruzolijavier/LUCI.git
   git push -u origin main
   ```

3. En GitHub: **Settings > Actions > General > Workflow permissions** = *Read and write permissions*.
4. Publicar la primera versión (`.\publicar.ps1 -Version 0.3.0 -Notas "Primera versión con actualizaciones"`),
   descargar `LUCI_windows.zip` de Releases, descomprimir y repartir esa carpeta.
5. Para probar el ciclo, publicar `0.3.1` y pulsar **Update LUCI** en la 0.3.0.

## Si algo falla

- Registro de actualizaciones: `%LOCALAPPDATA%\LUCI\update.log`.
- Si la compilación falla, se ve en la pestaña **Actions**; no se publica nada hasta que acabe bien.
- Para retirar una versión mala: borrar su release (y la etiqueta) en GitHub; la anterior vuelve a ser la
  «latest».
