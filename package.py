"""Build the local Workshop source archive without transient Python files."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

project = Path(__file__).resolve().parent
archive = project.parent / "WeaponSkinShop-v1.2.0.zip"
files = sorted(
    path for path in project.rglob("*")
    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
)
with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
    for path in files:
        output.write(path, "Weapon Skin Shop/" + path.relative_to(project).as_posix())
print(f"{archive}: {len(files)} files")
