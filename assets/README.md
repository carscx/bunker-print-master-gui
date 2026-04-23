# Icono de la aplicacion

Para usar tu logo como icono del ejecutable, instalador y accesos directos:

1. Guarda el archivo como `app.ico` en esta carpeta.
2. Ruta final esperada: `assets/app.ico`.

## Recomendaciones de formato

- Formato: `.ico`
- Tamaños incluidos: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16
- Fondo: transparente

## Flujo

1. Colocar `assets/app.ico`.
2. Ejecutar `build_release.bat <version>`.
3. Verificar en el instalador y acceso directo que aparece el nuevo icono.

Si `assets/app.ico` no existe, el build sigue funcionando con icono por defecto.
