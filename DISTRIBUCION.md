# Distribucion en Windows

Este proyecto ya genera una aplicacion instalable para Windows.

## Archivos importantes

- `imprimir_gui.py`: codigo fuente de la app.
- `imprimir_gui.spec`: build del `.exe` con PyInstaller.
- `imprimir_gui_installer.iss`: script del instalador Inno Setup.
- `build_release.bat`: compila `.exe` + instalador en un solo paso.
- `build_installer.bat`: compila solo el instalador (si el `.exe` ya existe).
- `sign_release.bat`: firma digital de ejecutables con `signtool`.

## Generar release completa

Desde la carpeta `impresion-tandas`, ejecuta:

```bat
build_release.bat
```

Esto crea:

- `dist\imprimir_gui.exe`
- `installer\Setup-Bunker-Print-Master-GUI-<version>.exe`

## Generar release con version especifica

```bat
build_release.bat 1.0.2
```

El instalador saldra con ese numero de version.

## Firma digital (recomendado para reducir alertas)

Para reducir alertas de SmartScreen en equipos de terceros, firma el `.exe` y el instalador con un certificado de firma de codigo real (OV o EV).

Variables de entorno requeridas antes de compilar:

```bat
set SIGN_PFX=C:\ruta\tu-certificado.pfx
set SIGN_PFX_PASSWORD=tu_clave
set SIGN_TIMESTAMP_URL=http://timestamp.digicert.com
```

Luego ejecuta:

```bat
build_release.bat 1.0.2
```

Si `SIGN_PFX` no esta configurado, el build funciona pero deja los binarios sin firma.

Notas:

1. Un certificado autofirmado no evita alertas en otras PCs.
2. EV Code Signing reduce advertencias mas rapido que OV.
3. El timestamp permite que la firma siga valida tras expirar el certificado.

## Distribuir a otras personas

Comparte solo el archivo del instalador dentro de `installer\`.

Recomendado:

1. Verificar en una PC de prueba que instala, abre y desinstala bien.
2. Mantener un historial simple de versiones (1.0.1, 1.0.2, etc.).
3. No compartir el `dist\imprimir_gui.exe` suelto si quieres una experiencia de instalacion normal.

## Requisitos en maquina de compilacion

- Python 3
- PyInstaller
- Inno Setup 6 (ISCC)

La maquina del usuario final no necesita Python.
