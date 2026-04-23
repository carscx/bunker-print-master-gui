# Bunker Print Master GUI

Aplicacion de escritorio para Windows orientada a impresion por tandas (frente/dorso) con flujo guiado.

## Objetivo

- Facilitar impresion por tandas para documentos PDF.
- Mantener una interfaz simple para operadores no tecnicos.
- Permitir distribucion gratuita en Windows con codigo fuente publico.

## Transparencia y seguridad

Este proyecto publica su codigo fuente para que cualquiera pueda auditarlo.

Eso mejora la confianza porque:

1. El comportamiento del programa es verificable.
2. El ejecutable se construye a partir de este mismo codigo.
3. Se publican checksums SHA256 para validar integridad del archivo descargado.

Nota importante: ningun software puede garantizar riesgo cero absoluto. Publicar codigo y hashes reduce el riesgo de manera significativa frente a binarios cerrados sin trazabilidad.

## Instalacion para usuarios finales

Sigue la guia paso a paso en [INSTALLACION_WINDOWS.md](INSTALLACION_WINDOWS.md).

## Estructura del proyecto

- [imprimir_gui.py](imprimir_gui.py): aplicacion principal.
- [imprimir_gui.spec](imprimir_gui.spec): build PyInstaller.
- [imprimir_gui_installer.iss](imprimir_gui_installer.iss): script del instalador Inno Setup.
- [build_release.bat](build_release.bat): compila exe + instalador + checksums.
- [build_installer.bat](build_installer.bat): compila solo instalador.
- [sign_release.bat](sign_release.bat): firma digital opcional.
- [create_checksums.bat](create_checksums.bat): genera SHA256SUMS.txt.
- [assets/README.md](assets/README.md): guia para icono del exe e instalador.

## Compilar una release

En Windows, dentro de esta carpeta:

```bat
build_release.bat 1.0.4
```

Salida esperada:

- instalador en `installer/Setup-Bunker-Print-Master-GUI-<version>.exe`
- hash en `installer/SHA256SUMS.txt`

## Publicar en GitHub Releases

1. Crear tag de version.
2. Subir como assets:
   1. Setup-Bunker-Print-Master-GUI-<version>.exe
   2. SHA256SUMS.txt
3. Copiar plantilla de [RELEASE_TEMPLATE.md](RELEASE_TEMPLATE.md).

Guia completa de publicacion:

- [PUBLISH_GITHUB.md](PUBLISH_GITHUB.md)

## Licencia

Proyecto publicado bajo licencia MIT. Ver [LICENSE](LICENSE).
