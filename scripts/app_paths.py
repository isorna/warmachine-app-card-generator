"""Discover and validate local Warmachine paths without reading account secrets."""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".local" / "config.json"

def public_cache(app):
    app = Path(app)
    candidates = [p for p in app.glob("public-*") if p.is_dir() and any(p.glob("*.bundle"))]
    if len(candidates) != 1:
        raise ValueError("La carpeta de datos debe contener exactamente una cache public-* con bundles. Abre Warmachine App y descarga sus datos.")
    return candidates[0]

def valid_install(path):
    p = Path(path)
    return (p / "Warmachine App.exe").is_file() and (p / "Warmachine App_Data/resources.assets").is_file()

def registry_installs():
    if sys.platform != "win32":
        return []
    import winreg
    result = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, winreg.KEY_READ | view) as root:
                    for i in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            with winreg.OpenKey(root, winreg.EnumKey(root, i)) as key:
                                name = winreg.QueryValueEx(key, "DisplayName")[0]
                                if "warmachine" in name.casefold():
                                    value = winreg.QueryValueEx(key, "InstallLocation")[0]
                                    if value: result.append(Path(value.strip('"')))
                        except OSError:
                            continue
            except OSError:
                continue
    return result

def detected_installs():
    candidates = registry_installs()
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        if os.environ.get(env):
            candidates.append(Path(os.environ[env]) / "Warmachine App")
    unique = {}
    for p in candidates:
        if valid_install(p): unique[str(p.resolve()).casefold()] = p.resolve()
    return list(unique.values())

def default_data():
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    return local.parent / "LocalLow/Privateer Press/Warmachine App"

def load_config(path=CONFIG):
    if not path.exists(): return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise ValueError("Configuracion ilegible: " + str(path)) from exc
    if not isinstance(data, dict) or any(k in data and not isinstance(data[k], str) for k in ("app_install", "app_data")):
        raise ValueError("Configuracion invalida: las rutas deben ser texto.")
    return data

def validate_data(path):
    public_cache(path)
    return Path(path).resolve()

def pick_path(label, candidate, validator, interactive):
    while True:
        if interactive:
            try:
                value = input(f"{label} [{candidate or 'sin detectar'}]: ").strip().strip('"')
            except EOFError as exc:
                raise ValueError("Entrada cerrada; indica --app-install y --app-data para configurar sin preguntas.") from exc
            if value: candidate = Path(os.path.expandvars(value)).expanduser()
        try:
            if candidate is None: raise ValueError("No se ha detectado la ruta.")
            candidate = Path(candidate).expanduser().resolve()
            if validator(candidate) is False: raise ValueError("No contiene los archivos esperados.")
            return candidate
        except (ValueError, OSError) as exc:
            if not interactive:
                raise ValueError(f"{label}: {candidate}. {exc} Ejecuta Configurar-rutas.cmd o indica --app-install y --app-data.") from exc
            print("Ruta no valida:", exc)

def resolve_paths(app_install=None, app_data=None, configure=False, config_path=CONFIG):
    cfg = load_config(config_path)
    detected = detected_installs() if not app_install and not cfg.get("app_install") else []
    install = app_install or cfg.get("app_install") or (detected[0] if len(detected) == 1 else None)
    data = app_data or cfg.get("app_data") or default_data()
    interactive = configure and sys.stdin.isatty() and not (app_install and app_data)
    if configure and not interactive:
        # Explicit CLI paths also allow unattended setup.
        if not app_install or not app_data: raise ValueError("Sin consola interactiva: indica ambas rutas para --configure.")
    install = pick_path("Instalacion de Warmachine App", install, valid_install, interactive)
    data = pick_path("Datos de Warmachine App", data, validate_data, interactive)
    if configure:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        temp = config_path.with_suffix(".tmp")
        temp.write_text(json.dumps({"app_install": str(install), "app_data": str(data)}, indent=2) + "\n", encoding="utf8")
        temp.replace(config_path)
    return install, data
