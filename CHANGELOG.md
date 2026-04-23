# Changelog

All notable changes to this project will be documented in this file.

## [1.2.6] - 2026-04-23

### Changed

- UI redesigned para mejor responsividad en pantallas pequeñas
- Preview minsize reducido de 340 → 200px
- Preview cards más compactos (220px vs 260px fijos)
- Steps panel siempre en 2 columnas (sin apilamiento vertical)
- Botones de steps más compactos (36-40px vs 54/48px)
- Status panel comprimido (combine info rows, reduce padding)
- Font sizes optimizados para compact mode (fs_step_button, fs_step_secondary)

### Result

- Compact mode (1220×680): Muestra PDF completo sin clipping
- Distribución de altura: Header 70px + Steps 80px + Preview 200px + Status 130px = 480px total
- Mejor uso del espacio vertical en resoluciones pequeñas

## [1.2.5] - 2026-04-23

### Fixed

- Previsualización PDF en blanco - aumentado DPI de renderizado (0.35 → 0.75)
- Manejo de errores en previsualización - ahora muestra páginas parciales cuando una falla
- Fuga de memoria en gestión de referencias de imágenes de PDF
- Soporte para pantallas 1360x768 - reducido minsize (1366x720 → 1220x680)

### Changed

- Lógica de detección de resolución: cambio de OR a AND para selección precisa de ui_mode
- Altura del header ahora adaptativa (compact: 70px, normal: 90px, wide: 110px)
- Matriz de renderizado PDF mejorada para mejor legibilidad en previsualizaciones

## [1.2.0] - 2026-04-23

### Added

- Sistema de actualizacion automatica desde GitHub Releases integrado en la GUI.
- Descarga automatica del instalador mas reciente y ejecucion silenciosa con minima intervencion.
- Archivo `version.txt` incluido en la app instalada para control de version local.

### Changed

- `build_release.bat` ahora elimina instaladores antiguos antes de generar una nueva release.
- El instalador Inno Setup cierra/reinicia la app automaticamente durante actualizaciones.
- Se ampliaron `hiddenimports` para compatibilidad con `pymupdf` y `tkinterdnd2`.

## [1.0.4] - 2026-04-22

### Added

- Flujo de release completo con checksums SHA256 automaticos.
- Documentacion para distribucion segura en GitHub.
- Plantilla de release y guia de instalacion paso a paso.

### Changed

- Pipeline de build preparado para publicacion open source.

## [1.0.3] - 2026-04-22

### Added

- Instalador versionado generado con Inno Setup.
- Integracion de firma digital opcional en pipeline.

## [1.0.2] - 2026-04-22

### Added

- build_release.bat para compilar exe + instalador en un solo comando.

## [1.0.1] - 2026-04-22

### Added

- Primer instalador para Windows.
- Deteccion automatica de impresoras de Windows con fallback.
