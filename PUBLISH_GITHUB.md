# Publicar En GitHub (Paso a Paso)

## 1) Crear repositorio en GitHub

1. En GitHub, crear un repositorio nuevo, por ejemplo: `bunker-print-master-gui`.
2. No inicializar con README desde GitHub (este proyecto ya lo tiene).

## 1.1) Preparar icono de la aplicacion

1. Copiar el logo en formato `.ico` a `assets/app.ico`.
2. Si tienes logo en `.png`, convertirlo a `.ico` antes de compilar release.
3. El build aplicara ese icono al `.exe`, al instalador y a los accesos directos.

## 2) Primer commit local

En esta carpeta (`impresion-tandas`):

```bat
git add .
git commit -m "chore: preparar proyecto para distribucion open source"
```

## 3) Conectar remoto

Reemplaza `TU_USUARIO` y nombre de repo:

```bat
git remote add origin https://github.com/TU_USUARIO/bunker-print-master-gui.git
git branch -M main
git push -u origin main
```

## 4) Crear release distribuible

```bat
build_release.bat 1.0.4
```

## 5) Publicar GitHub Release

1. Crear tag `v1.0.4` en GitHub Releases.
2. Adjuntar archivos desde `installer/`:
   1. `Setup-Bunker-Print-Master-GUI-1.0.4.exe`
   2. `SHA256SUMS.txt`
3. Copiar contenido base de [RELEASE_TEMPLATE.md](RELEASE_TEMPLATE.md).

## 6) Mensaje recomendado para usuarios

- Codigo fuente publico en este repositorio.
- Binario generado a partir de ese codigo.
- Hash SHA256 publicado para verificar integridad.
