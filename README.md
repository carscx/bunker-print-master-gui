# Bunker Print Master GUI

Aplicacion de escritorio para Windows para imprimir PDFs grandes por tandas (frente/dorso) con un flujo guiado y seguro para operador.

## Que hace este programa

- Carga uno o varios PDFs por boton o arrastrar y soltar.
- Calcula hojas y tandas por documento.
- Genera tandas separadas en frente/dorso para reducir errores de impresion.
- Muestra previsualizacion de paginas antes de imprimir.
- Guía el proceso por pasos con estados visibles.
- Permite detener o reiniciar el proceso en cualquier momento.

## Flujo de uso recomendado

1. Cargar PDF(s) y seleccionar impresora.
2. Definir pagina inicial y hojas por tanda.
3. Pulsar `Leer paginas`.
4. Pulsar `PASO 1: Preparar Tandas`.
5. Imprimir `Frente` y luego `Dorso` segun corresponda.
6. Confirmar tanda correcta y continuar.
7. Si algo falla: usar `Detener y Revisar` o `Reiniciar Proceso`.

## Donde se guardan los archivos

- **PDF original:** se usa desde su ruta original (no se mueve ni se sobrescribe).
- **Tandas generadas:** se guardan en `salidas/`.
- Carpeta por trabajo: `salidas/FIX_<nombre_pdf>_<impresora>/`
- Archivos generados por tanda:
  - `F_<n>_FRENTE.pdf`
  - `F_<n>_DORSO.pdf` (si aplica)

## Instalacion (usuario final)

Sigue la guia paso a paso en [INSTALLACION_WINDOWS.md](INSTALLACION_WINDOWS.md).

## Build de release (desarrollador)

Desde la carpeta del proyecto en Windows:

```bat
build_release.bat
```

O especificando version manual:

```bat
build_release.bat 1.4.0
```

Salida esperada:

- `installer/Setup-Bunker-Print-Master-GUI-<version>.exe`
- `installer/SHA256SUMS.txt`

## Estructura clave del proyecto

- [imprimir_gui.py](imprimir_gui.py): logica principal de interfaz y proceso.
- [imprimir_gui.spec](imprimir_gui.spec): configuracion de PyInstaller.
- [imprimir_gui_installer.iss](imprimir_gui_installer.iss): script de Inno Setup.
- [build_release.bat](build_release.bat): genera exe + instalador + checksum.
- [version.txt](version.txt): version actual utilizada por scripts de build.

## Publicacion

- Guia completa: [PUBLISH_GITHUB.md](PUBLISH_GITHUB.md)
- Plantilla de notas: [RELEASE_TEMPLATE.md](RELEASE_TEMPLATE.md)
- Historial de cambios: [CHANGELOG.md](CHANGELOG.md)

## Transparencia y seguridad

El proyecto es auditable porque publica su codigo fuente y checksums SHA256 para validar integridad de instaladores.

## Licencia

MIT. Ver [LICENSE](LICENSE).
