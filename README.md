# Warmachine App Card Generator

Generador local para Windows: convierte tus listas guardadas en Warmachine App en cartas horizontales con anverso y reverso para MakePlayingCards (MPC).

Proyecto independiente: no requiere Wardice, Codex, Node.js ni Poppler. No incluye perfiles, ilustraciones, iconos ni listas del juego. Lee los datos descargados por tu propia instalaciÃ³n de Warmachine App, sin modificarlos.

## Propiedad intelectual e independencia

**Warmachine, Warmachine App y los datos y recursos del juego utilizados por esta herramienta (reglas, perfiles, textos, nombres, ilustraciones, iconos y demÃ¡s assets) son propiedad de Steamforged Games Ltd.** Todos los derechos sobre esos contenidos pertenecen a sus titulares. Sitio oficial: [warmachine.gg](https://warmachine.gg/).

**Este proyecto no tiene ninguna relaciÃ³n con Steamforged Games Ltd.: no estÃ¡ afiliado, patrocinado, autorizado ni respaldado por la empresa.** Es una herramienta comunitaria no oficial, desarrollada sin Ã¡nimo de lucro para ayudar a los jugadores a preparar cartas de referencia para sus partidas.

La licencia MIT se aplica exclusivamente al cÃ³digo y la documentaciÃ³n propios del generador, no a Warmachine App ni a los datos o assets del juego. Extraer o transformar esos recursos no transfiere su propiedad ni concede permisos para redistribuirlos o explotarlos. Los componentes de terceros conservan sus propias licencias.

La finalidad sin Ã¡nimo de lucro describe este proyecto; no aÃ±ade una restricciÃ³n de uso comercial a la licencia MIT del cÃ³digo. Consulta [LICENSE](LICENSE) y [THIRD_PARTY.md](THIRD_PARTY.md).

## Inicio rÃ¡pido

1. Instala **Python de 64 bits, 3.11 o posterior** desde [python.org](https://www.python.org/downloads/windows/). Activa la opciÃ³n de aÃ±adirlo al PATH. Probado localmente con Python 3.13.
2. Abre Warmachine App con tu usuario habitual, deja que descargue los datos y guarda al menos una lista. Evita actualizar la app mientras exportas.
3. Descarga o clona este proyecto en una carpeta donde puedas escribir y extrae el ZIP completo si lo descargaste como archivo.
4. Ejecuta **Configurar-rutas.cmd**. Propone las ubicaciones detectadas; pulsa Intro para aceptarlas o escribe otras rutas.
5. Ejecuta **Generar-cartas-Warmachine.cmd**, elige una lista y espera la exportaciÃ³n.

La primera ejecuciÃ³n crea `.venv` e instala las librerÃ­as desde PyPI; necesita Internet. Las siguientes exportaciones son locales y no requieren conexiÃ³n si no cambian las dependencias.

Las rutas tambiÃ©n se detectan automÃ¡ticamente al generar. La configuraciÃ³n explÃ­cita evita ambigÃ¼edades si tienes varias instalaciones.

## Rutas y diagnÃ³stico

Hay dos ubicaciones distintas:

- **InstalaciÃ³n:** contiene `Warmachine App.exe` y `Warmachine App_Data/resources.assets`. Se consulta el registro de desinstalaciÃ³n de Windows (usuario/equipo, vistas de 32/64 bits), Program Files y la carpeta local de aplicaciones.
- **Datos:** normalmente `%USERPROFILE%\AppData\LocalLow\Privateer Press\Warmachine App`. Debe contener una Ãºnica cachÃ© `public-*` con archivos `.bundle`. Las listas son `force-*.json`.

Prioridad: argumentos de consola > configuraciÃ³n guardada > detecciÃ³n automÃ¡tica. Una ruta guardada que deja de ser vÃ¡lida produce un error; no se cambia silenciosamente por otra instalaciÃ³n. No se recorren todos los discos. Usa **Configurar-rutas.cmd** para instalaciones portables o movidas.

**Comprobar-instalacion.cmd** valida las rutas, disponibilidad de la clave local del perfil y las dos imÃ¡genes de espirales; no imprime ni exporta la clave. No garantiza que todos los perfiles tengan un adaptador de maquetaciÃ³n.

La configuraciÃ³n y los recursos de espirales quedan en `.local/`, excluido de Git. La clave se obtiene del registro del usuario que ejecuta el programa; no se guarda en la configuraciÃ³n. Copiar sÃ³lo la carpeta de cachÃ© desde otro equipo no sustituye la instalaciÃ³n y el perfil local.

## Resultado

Cada ejecuciÃ³n crea una carpeta nueva en `output/warmachine-app/cards/`:

- `cartas-mpc.pdf`: revisiÃ³n, una cara por pÃ¡gina.
- `cartas-mpc.zip`: PNG de 300 ppp emparejados `001-front.png` / `001-back.png`.
- `print-profiles.json`, manifiestos y `avisos.json`: datos utilizados y diagnÃ³stico.
- `errores.json`: si una incidencia impide completar la exportaciÃ³n.

Formato: corte **146,05 Ã— 88,9 mm** (5,75 Ã— 3,5 pulgadas), PNG con sangrado **1797 Ã— 1122 px**. Conserva iconos, tablas de armas/hechizos, secciones de reglas y espirales originales. Los perfiles extensos tienen cartas complementarias. Cabeceras con colores de facciÃ³n y grabado vectorial. El PDF no es una imposiciÃ³n de dos cartas por hoja A4.

Revisa el resultado y la previsualizaciÃ³n de MPC antes de imprimir.

## CÃ³mo funciona

1. Comprueba rutas.
2. Lee la cachÃ© y copia los datos a un snapshot fechado, verificando que no cambien durante la lectura.
3. Resuelve los identificadores de las listas contra el catÃ¡logo y aplica opciones.
4. Recupera imÃ¡genes e iconos de la cachÃ©; extrae las espirales de los recursos Unity instalados.
5. Maqueta, comprueba mÃ¡rgenes y exporta los pares de PNG y el PDF.

No consulta servidores del juego ni inicia sesiÃ³n por ti. La actualidad de los datos depende de lo que haya descargado Warmachine App. No modifica la app, el registro, tus listas ni el proyecto Wardice original.

## Consola

DespuÃ©s de la primera ejecuciÃ³n:

```powershell
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --doctor
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --configure --app-install "E:\Games\Warmachine App" --app-data "E:\Datos\Warmachine App"
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --list
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --force "Nombre exacto de la lista"
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --snapshot "output\warmachine-app\snapshots\FECHA" --force "Nombre exacto de la lista"
```

`--snapshot` reutiliza los datos estructurados; sigue requiriendo los medios de la cachÃ© local. Para conservar una exportaciÃ³n reproducible, guarda su carpeta de salida completa.

`--check-all` comprueba la materializaciÃ³n de todas las listas, no su maquetaciÃ³n. Los nombres duplicados se seleccionan mediante GUID o menÃº.

## Compatibilidad y lÃ­mites

- Windows, fuentes Arial/Segoe UI del sistema y Warmachine App instalada con datos descargados.
- Cartas de reglas de ejÃ©rcito (Army) sin modelos, como Dreadtides: imagen y reglas completas en cartas complementarias.
- DaÃ±o Box, Box Multi, Grid, Grid Large (rejillas izquierda/derecha de colosales), Spiral, Spiral Large, Web y Web Large; perfiles mÃºltiples con daÃ±o asignable por nombre; cartas de mando seleccionadas.
- Tipos de daÃ±o no soportados, metadatos desconocidos o referencias ambiguas se rechazan con informe. No se inventan datos.
- En perfiles con varios modelos, un marcador Box Ãºnico sin nombre se asigna sÃ³lo si un modelo coincide exactamente y de forma Ãºnica con el nombre del perfil (por ejemplo, Malady Man). Las asignaciones ambiguas se rechazan.
- El lector depende del formato local de la app. Una actualizaciÃ³n puede requerir adaptar el proyecto.
- Es una herramienta comunitaria independiente, no un producto oficial.

## Desarrollo y publicaciÃ³n

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s scripts/tests
```

Las pruebas son sintÃ©ticas: no necesitan una cuenta ni datos del juego. El workflow de GitHub Actions ejecuta las pruebas en Windows.

Publica sÃ³lo los archivos fuente versionados. `.gitignore` excluye `output/`, `.local/` y `.venv/`. No adjuntes snapshots, exportaciones ni carpetas de la app a una release o incidencia: pueden contener listas y contenido del juego. Los informes locales tambiÃ©n pueden incluir rutas y nombres de usuario.

El cÃ³digo mantiene la licencia MIT del proyecto de origen. Consulta [THIRD_PARTY.md](THIRD_PARTY.md) para distinguir el cÃ³digo de los recursos del juego.

## English quick start

Windows only. Run **Comprobar-Python.cmd** to check for stable 64-bit Python 3.11+ (including venv and pip), or get help installing Python 3.13 via WinGet or the official website. Then launch Warmachine App, download its data and save a force. Extract this project, run **Configurar-rutas.cmd** to confirm your installation/data directories, then **Generar-cartas-Warmachine.cmd** to select a force. Dependencies install automatically into a local virtual environment on first launch. **Comprobar-instalacion.cmd** checks the installation.

Output: `output/warmachine-app/cards/`, with a review PDF and paired 300 dpi PNG files in a ZIP for MPC Large Landscape (5.75 Ã— 3.5 inches). Game data and artwork are read locally and are not shipped in this repository. Current UI and diagnostic messages are in Spanish.

**Ownership and independence:** Warmachine, Warmachine App and the game data and assets used by this tool are the property of Steamforged Games Ltd. This is an unofficial community project, developed without a profit motive to help players. It has no relationship with, and is not affiliated with, sponsored, authorized or endorsed by Steamforged Games Ltd. The MIT license covers only the generator's own code and documentation, not the game or its content. The project's non-profit purpose does not add a non-commercial restriction to the MIT license. Official website: [warmachine.gg](https://warmachine.gg/).
