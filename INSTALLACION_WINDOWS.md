# Instalacion Paso A Paso (Windows)

## Opcion recomendada: instalador

1. Ir a la seccion Releases del repositorio en GitHub.
2. Descargar:
   1. Setup-Bunker-Print-Master-GUI-<version>.exe
   2. SHA256SUMS.txt
3. Verificar integridad:
   1. Abrir PowerShell en la carpeta de descarga.
   2. Ejecutar:

```powershell
Get-FileHash .\Setup-Bunker-Print-Master-GUI-<version>.exe -Algorithm SHA256
```

4. Comparar el hash con el valor de SHA256SUMS.txt.
5. Ejecutar el instalador.
6. Completar asistente de instalacion.
7. Abrir desde Menu Inicio: Bunker Print Master GUI.

## Si Windows muestra advertencia SmartScreen

En proyectos gratuitos/open source sin firma comercial, puede aparecer advertencia.

Pasos:

1. Verifica que descargaste desde el Release oficial del proyecto.
2. Verifica SHA256.
3. Si coincide, puedes continuar con "Mas informacion" > "Ejecutar de todas formas".

## Requisitos del usuario final

- Windows 10/11
- No requiere Python instalado
