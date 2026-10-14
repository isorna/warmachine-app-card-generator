"""Extract only required spiral artwork from the user's own installation."""
import hashlib, json, os
from pathlib import Path
from PIL import Image

NAMES = ("health_spiral_arms_COLOR", "health_spiral_arms_large_COLOR")

def prepare_assets(install, output):
    import UnityPy
    source = Path(install) / "Warmachine App_Data/resources.assets"
    signature = hashlib.sha256(source.read_bytes()).hexdigest()
    output = Path(output)
    manifest = output / "manifest.json"
    if manifest.exists():
        previous = json.loads(manifest.read_text(encoding="utf8"))
        if previous.get("sourceSha256") == signature and all(
            (output / (name + ".png")).is_file() and
            hashlib.sha256((output / (name + ".png")).read_bytes()).hexdigest() == previous.get("files", {}).get(name)
            for name in NAMES
        ): return output
    env = UnityPy.load(str(source))
    found = {}
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            texture = obj.read()
            if texture.m_Name in NAMES:
                found[texture.m_Name] = texture.image
    missing = set(NAMES) - found.keys()
    if missing: raise ValueError("La instalacion no contiene las espirales esperadas: " + ", ".join(sorted(missing)))
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, image in found.items():
        if image.size != (1024, 1024):
            raise ValueError("La geometria de espiral ha cambiado; se requiere adaptar el generador.")
        target = output / (name + ".png")
        temp = target.with_suffix(".tmp")
        image.save(temp, format="PNG")
        temp.replace(target)
        hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest.write_text(json.dumps({"sourceSha256": signature, "files": hashes}, indent=2), encoding="utf8")
    return output
