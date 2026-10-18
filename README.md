# Warmachine App Card Generator

Generador local para Windows: convierte tus listas guardadas en Warmachine App en cartas horizontales con anverso y reverso para MakePlayingCards (MPC).

Proyecto independiente: no requiere Wardice, Codex, Node.js ni Poppler. No incluye perfiles, ilustraciones, iconos ni listas del juego. Lee los datos descargados por tu propia instalación de Warmachine App, sin modificarlos.

## Propiedad intelectual e independencia

**Warmachine, Warmachine App y los datos y recursos del juego utilizados por esta herramienta (reglas, perfiles, textos, nombres, ilustraciones, iconos y demás assets) son propiedad de Steamforged Games Ltd.** Todos los derechos sobre esos contenidos pertenecen a sus titulares. Sitio oficial: [warmachine.gg](https://warmachine.gg/).

**Este proyecto no tiene ninguna relación con Steamforged Games Ltd.: no está afiliado, patrocinado, autorizado ni respaldado por la empresa.** Es una herramienta comunitaria no oficial, desarrollada sin ánimo de lucro para ayudar a los jugadores a preparar cartas de referencia para sus partidas.

La licencia MIT se aplica exclusivamente al código y la documentación propios del generador, no a Warmachine App ni a los datos o assets del juego. Extraer o transformar esos recursos no transfiere su propiedad ni concede permisos para redistribuirlos o explotarlos. Los componentes de terceros conservan sus propias licencias.

La finalidad sin ánimo de lucro describe este proyecto; no añade una restricción de uso comercial a la licencia MIT del código. Consulta [LICENSE](LICENSE) y [THIRD_PARTY.md](THIRD_PARTY.md).

## Inicio rápido

1. Instala **Python de 64 bits, 3.11 o posterior** desde [python.org](https://www.python.org/downloads/windows/). Activa la opción de añadirlo al PATH. Probado localmente con Python 3.13.
2. Abre Warmachine App con tu usuario habitual, deja que descargue los datos y guarda al menos una lista. Evita actualizar la app mientras exportas.
3. Descarga o clona este proyecto en una carpeta donde puedas escribir y extrae el ZIP completo si lo descargaste como archivo.
4. Ejecuta **Configurar-rutas.cmd**. Propone las ubicaciones detectadas; pulsa Intro para aceptarlas o escribe otras rutas.
5. Ejecuta **Generar-cartas-Warmachine.cmd**, elige una lista y espera la exportación.

La primera ejecución crea `.venv` e instala las librerías desde PyPI; necesita Internet. Las siguientes exportaciones son locales y no requieren conexión si no cambian las dependencias.

Las rutas también se detectan automáticamente al generar. La configuración explícita evita ambigüedades si tienes varias instalaciones.

## Rutas y diagnóstico

Hay dos ubicaciones distintas:

- **Instalación:** contiene `Warmachine App.exe` y `Warmachine App_Data/resources.assets`. Se consulta el registro de desinstalación de Windows (usuario/equipo, vistas de 32/64 bits), Program Files y la carpeta local de aplicaciones.
- **Datos:** normalmente `%USERPROFILE%\AppData\LocalLow\Privateer Press\Warmachine App`. Debe contener una única caché `public-*` con archivos `.bundle`. Las listas son `force-*.json`.

Prioridad: argumentos de consola > configuración guardada > detección automática. Una ruta guardada que deja de ser válida produce un error; no se cambia silenciosamente por otra instalación. No se recorren todos los discos. Usa **Configurar-rutas.cmd** para instalaciones portables o movidas.

**Comprobar-instalacion.cmd** valida las rutas, disponibilidad de la clave local del perfil y las dos imágenes de espirales; no imprime ni exporta la clave. No garantiza que todos los perfiles tengan un adaptador de maquetación.

La configuración y los recursos de espirales quedan en `.local/`, excluido de Git. La clave se obtiene del registro del usuario que ejecuta el programa; no se guarda en la configuración. Copiar sólo la carpeta de caché desde otro equipo no sustituye la instalación y el perfil local.

## Resultado

Cada ejecución crea una carpeta nueva en `output/warmachine-app/cards/`:

- `cartas-mpc.pdf`: revisión, una cara por página.
- `cartas-mpc.zip`: PNG de 300 ppp emparejados `001-front.png` / `001-back.png`.
- `print-profiles.json`, manifiestos y `avisos.json`: datos utilizados y diagnóstico.
- `errores.json`: si una incidencia impide completar la exportación.

Formato: corte **146,05 × 88,9 mm** (5,75 × 3,5 pulgadas), PNG con sangrado **1797 × 1122 px**. Conserva iconos, tablas de armas/hechizos, secciones de reglas y espirales originales. Los perfiles extensos tienen cartas complementarias. Cabeceras con colores de facción y grabado vectorial. El PDF no es una imposición de dos cartas por hoja A4.

Revisa el resultado y la previsualización de MPC antes de imprimir.

## Cómo funciona

1. Comprueba rutas.
2. Lee la caché y copia los datos a un snapshot fechado, verificando que no cambien durante la lectura.
3. Resuelve los identificadores de las listas contra el catálogo y aplica opciones.
4. Recupera imágenes e iconos de la caché; extrae las espirales de los recursos Unity instalados.
5. Maqueta, comprueba márgenes y exporta los pares de PNG y el PDF.

No consulta servidores del juego ni inicia sesión por ti. La actualidad de los datos depende de lo que haya descargado Warmachine App. No modifica la app, el registro, tus listas ni el proyecto Wardice original.

## Consola

Después de la primera ejecución:

```powershell
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --doctor
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --configure --app-install "E:\Games\Warmachine App" --app-data "E:\Datos\Warmachine App"
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --list
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --force "Nombre exacto de la lista"
.venv\Scripts\python.exe scripts\generate-warmachine-cards.py --snapshot "output\warmachine-app\snapshots\FECHA" --force "Nombre exacto de la lista"
```

`--snapshot` reutiliza los datos estructurados; sigue requiriendo los medios de la caché local. Para conservar una exportación reproducible, guarda su carpeta de salida completa.

`--check-all` comprueba la materialización de todas las listas, no su maquetación. Los nombres duplicados se seleccionan mediante GUID o menú.

## Compatibilidad y límites

- Windows, fuentes Arial/Segoe UI del sistema y Warmachine App instalada con datos descargados.
- Cartas de reglas de ejército (Army) sin modelos, como Dreadtides: imagen y reglas completas en cartas complementarias.
- Daño Box, Box Multi, Grid, Grid Large (rejillas izquierda/derecha de colosales), Spiral, Spiral Large, Web y Web Large; perfiles múltiples con daño asignable por nombre; cartas de mando seleccionadas.
- Tipos de daño no soportados, metadatos desconocidos o referencias ambiguas se rechazan con informe. No se inventan datos.
- En perfiles con varios modelos, un marcador Box único sin nombre se asigna sólo si un modelo coincide exactamente y de forma única con el nombre del perfil (por ejemplo, Malady Man). Las asignaciones ambiguas se rechazan.
- El lector depende del formato local de la app. Una actualización puede requerir adaptar el proyecto.
- Es una herramienta comunitaria independiente, no un producto oficial.

## Desarrollo y publicación

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s scripts/tests
```

Las pruebas son sintéticas: no necesitan una cuenta ni datos del juego. El workflow de GitHub Actions ejecuta las pruebas en Windows.

Publica sólo los archivos fuente versionados. `.gitignore` excluye `output/`, `.local/` y `.venv/`. No adjuntes snapshots, exportaciones ni carpetas de la app a una release o incidencia: pueden contener listas y contenido del juego. Los informes locales también pueden incluir rutas y nombres de usuario.

El código mantiene la licencia MIT del proyecto de origen. Consulta [THIRD_PARTY.md](THIRD_PARTY.md) para distinguir el código de los recursos del juego.

## English quick start

Windows only. Install 64-bit Python 3.11+, launch Warmachine App, download its data and save a force. Extract this project, run **Configurar-rutas.cmd** to confirm your installation/data directories, then **Generar-cartas-Warmachine.cmd** to select a force. Dependencies install automatically into a local virtual environment on first launch. **Comprobar-instalacion.cmd** checks the installation.

Output: `output/warmachine-app/cards/`, with a review PDF and paired 300 dpi PNG files in a ZIP for MPC Large Landscape (5.75 × 3.5 inches). Game data and artwork are read locally and are not shipped in this repository. Current UI and diagnostic messages are in Spanish.

**Ownership and independence:** Warmachine, Warmachine App and the game data and assets used by this tool are the property of Steamforged Games Ltd. This is an unofficial community project, developed without a profit motive to help players. It has no relationship with, and is not affiliated with, sponsored, authorized or endorsed by Steamforged Games Ltd. The MIT license covers only the generator's own code and documentation, not the game or its content. The project's non-profit purpose does not add a non-commercial restriction to the MIT license. Official website: [warmachine.gg](https://warmachine.gg/).
