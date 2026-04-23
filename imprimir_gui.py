import ctypes
import os
import shutil
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pikepdf


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
SUMATRA_PATH = Path(r"C:\Users\karsc\AppData\Local\SumatraPDF\SumatraPDF.exe")
IMPRESORAS_FALLBACK = ["EPSON_L5590_RAW",
                       "EPSON_L3250_RAW", "BROTHER_L2360D_RAW"]
OUTPUT_DIR = BASE_DIR / "salidas"


def beep():
    try:
        import winsound
        winsound.Beep(1000, 500)
    except Exception:
        print("\a")


def detectar_impresoras_windows():
    if os.name != "nt":
        return []

    try:
        from ctypes import wintypes

        PRINTER_ENUM_LOCAL = 0x2
        PRINTER_ENUM_CONNECTIONS = 0x4

        class PRINTER_INFO_4(ctypes.Structure):
            _fields_ = [
                ("pPrinterName", wintypes.LPWSTR),
                ("pServerName", wintypes.LPWSTR),
                ("Attributes", wintypes.DWORD),
            ]

        winspool = ctypes.WinDLL("winspool.drv")
        needed = wintypes.DWORD(0)
        returned = wintypes.DWORD(0)

        # Primera llamada para obtener el tamaño del buffer.
        winspool.EnumPrintersW(
            PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS,
            None,
            4,
            None,
            0,
            ctypes.byref(needed),
            ctypes.byref(returned),
        )

        if needed.value == 0:
            return []

        buffer = (ctypes.c_byte * needed.value)()
        ok = winspool.EnumPrintersW(
            PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS,
            None,
            4,
            ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)),
            needed.value,
            ctypes.byref(needed),
            ctypes.byref(returned),
        )
        if not ok:
            return []

        info_array = ctypes.cast(
            buffer,
            ctypes.POINTER(PRINTER_INFO_4 * returned.value),
        ).contents

        nombres = []
        for item in info_array:
            if item.pPrinterName:
                nombre = item.pPrinterName.strip()
                if nombre:
                    nombres.append(nombre)

        return sorted(set(nombres), key=str.lower)
    except Exception:
        return []


def obtener_pdfs_disponibles():
    archivos = []
    for carpeta in (BASE_DIR, WORKSPACE_DIR):
        for archivo in carpeta.iterdir():
            if archivo.is_file() and archivo.suffix.lower() == ".pdf" and not archivo.name.startswith("FIX_"):
                archivos.append(archivo)

    vistos = set()
    resultado = []
    for archivo in archivos:
        clave = str(archivo.resolve()).lower()
        if clave not in vistos:
            vistos.add(clave)
            resultado.append(archivo)
    return resultado


def obtener_total_paginas(archivo_pdf):
    pdf_temp = pikepdf.Pdf.open(str(archivo_pdf))
    try:
        return len(pdf_temp.pages)
    finally:
        pdf_temp.close()


def validar_parametros(archivo_pdf, pagina_inicio, paginas_por_tanda):
    if not archivo_pdf:
        raise ValueError("Debes seleccionar un archivo PDF.")
    if not archivo_pdf.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {archivo_pdf}")
    if pagina_inicio < 1:
        raise ValueError("La página inicial debe ser mayor o igual a 1.")
    if paginas_por_tanda < 1:
        raise ValueError(
            "Las hojas por tanda deben ser mayores o iguales a 1.")

    total_paginas = obtener_total_paginas(archivo_pdf)
    if pagina_inicio > total_paginas:
        raise ValueError(
            f"La página inicial no puede superar el total del documento ({total_paginas})."
        )
    return total_paginas


def crear_tandas(archivo_pdf, pagina_inicio, impresora_nombre, paginas_por_tanda):
    OUTPUT_DIR.mkdir(exist_ok=True)
    nombre_limpio = archivo_pdf.stem.replace(" ", "_")
    folder = OUTPUT_DIR / f"FIX_{nombre_limpio}_{impresora_nombre}"

    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)

    pdf = pikepdf.Pdf.open(str(archivo_pdf))
    try:
        total_total = len(pdf.pages)
        idx_inicio = max(0, pagina_inicio - 1)

        tandas = []
        num_tanda = 1
        for i in range(idx_inicio, total_total, paginas_por_tanda):
            fin = min(i + paginas_por_tanda, total_total)
            f_path = folder / f"F_{num_tanda}_FRENTE.pdf"
            d_path = folder / f"F_{num_tanda}_DORSO.pdf"

            frente = pikepdf.Pdf.new()
            pag_impares = [pdf.pages[p] for p in range(i, fin, 2)]
            pag_impares.reverse()
            for pagina in pag_impares:
                frente.pages.append(pagina)
            if pag_impares:
                frente.save(str(f_path))

            dorso = pikepdf.Pdf.new()
            pag_pares = [pdf.pages[p] for p in range(i + 1, fin, 2)]
            pag_pares.reverse()
            for pagina in pag_pares:
                dorso.pages.append(pagina)
            if pag_pares:
                dorso.save(str(d_path))
            else:
                d_path = None

            tandas.append(
                {
                    "id": num_tanda,
                    "frente": str(f_path),
                    "dorso": str(d_path) if d_path else None,
                    "pags": f"{i + 1}-{fin}",
                }
            )
            num_tanda += 1
        return tandas
    finally:
        pdf.close()


def imprimir_pdf(archivo, impresora):
    if not SUMATRA_PATH.exists():
        raise FileNotFoundError(f"No se encontró SumatraPDF en {SUMATRA_PATH}")

    subprocess.run(
        f'"{SUMATRA_PATH}" -print-to "{impresora}" -exit-on-print "{archivo}"',
        shell=True,
        check=True,
    )
    beep()


class PrintApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BUNKER PRINT MASTER GUI")
        self.root.geometry("820x600")
        self.root.minsize(780, 560)

        self.impresoras = detectar_impresoras_windows() or IMPRESORAS_FALLBACK
        self.archivo_pdf = tk.StringVar()
        self.impresora = tk.StringVar(
            value=self.impresoras[0] if self.impresoras else "")
        self.pagina_inicio = tk.StringVar(value="1")
        self.paginas_por_tanda = tk.StringVar(value="50")
        self.total_paginas = tk.StringVar(value="Total de páginas: -")
        self.estado = tk.StringVar(
            value="Prepara una tanda desde esta carpeta paralela.")

        self.pdfs = []
        self.tandas = []
        self.tanda_actual_idx = -1
        self.etapa_actual = "sin_preparar"

        self._build_ui()
        self._cargar_pdfs_locales()
        self._actualizar_controles()

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 10))

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="BUNKER PRINT MASTER",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text="Versión paralela dentro de impresion-tandas. Las salidas se guardan en esta carpeta.",
            style="Status.TLabel",
        ).pack(anchor="w", pady=(4, 12))

        config_frame = ttk.LabelFrame(main, text="Configuración", padding=12)
        config_frame.pack(fill="x")
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="PDF").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.pdf_combo = ttk.Combobox(
            config_frame, textvariable=self.archivo_pdf, state="normal")
        self.pdf_combo.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Button(config_frame, text="Actualizar lista", command=self._cargar_pdfs_locales).grid(
            row=0, column=2, padx=(8, 0), pady=6
        )
        ttk.Button(config_frame, text="Buscar PDF", command=self._seleccionar_pdf).grid(
            row=0, column=3, padx=(8, 0), pady=6
        )

        ttk.Label(config_frame, text="Impresora").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        self.printer_combo = ttk.Combobox(
            config_frame,
            textvariable=self.impresora,
            values=self.impresoras,
            state="readonly",
        )
        self.printer_combo.grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(config_frame, text="Actualizar impresoras", command=self._cargar_impresoras).grid(
            row=1, column=3, padx=(8, 0), pady=6
        )

        ttk.Label(config_frame, text="Página inicial").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(config_frame, textvariable=self.pagina_inicio).grid(
            row=2, column=1, sticky="ew", pady=6)

        ttk.Label(config_frame, text="Hojas por tanda").grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(config_frame, textvariable=self.paginas_por_tanda).grid(
            row=3, column=1, sticky="ew", pady=6)

        ttk.Button(config_frame, text="Leer páginas", command=self._leer_paginas_pdf).grid(
            row=3, column=3, padx=(8, 0), pady=6
        )
        ttk.Label(config_frame, textvariable=self.total_paginas, style="Status.TLabel").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

        action_frame = ttk.LabelFrame(
            main, text="Flujo de impresión", padding=12)
        action_frame.pack(fill="x", pady=12)
        for columna in range(3):
            action_frame.columnconfigure(columna, weight=1)

        self.prepare_button = ttk.Button(
            action_frame, text="Preparar tandas", command=self._preparar_tandas)
        self.prepare_button.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        self.frente_button = ttk.Button(
            action_frame, text="Imprimir frente", command=self._imprimir_frente)
        self.frente_button.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        self.dorso_button = ttk.Button(
            action_frame, text="Imprimir dorso", command=self._imprimir_dorso)
        self.dorso_button.grid(row=0, column=2, sticky="ew", padx=4, pady=4)

        self.ok_button = ttk.Button(
            action_frame, text="Tanda correcta / siguiente", command=self._confirmar_tanda)
        self.ok_button.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        self.stop_button = ttk.Button(
            action_frame, text="Detener", command=self._detener_proceso)
        self.stop_button.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        self.reset_button = ttk.Button(
            action_frame, text="Reiniciar", command=self._reiniciar_estado)
        self.reset_button.grid(row=1, column=2, sticky="ew", padx=4, pady=4)

        status_frame = ttk.LabelFrame(main, text="Estado", padding=12)
        status_frame.pack(fill="both", expand=True)

        ttk.Label(
            status_frame,
            textvariable=self.estado,
            wraplength=720,
            justify="left",
            style="Status.TLabel",
        ).pack(fill="x", anchor="w")

        self.detail_text = tk.Text(
            status_frame, height=16, wrap="word", state="disabled")
        self.detail_text.pack(fill="both", expand=True, pady=(12, 0))

    def _ruta_pdf_actual(self):
        valor = self.archivo_pdf.get().strip()
        if not valor:
            return None
        ruta = Path(valor)
        if ruta.exists():
            return ruta
        for archivo in self.pdfs:
            if archivo.name == valor:
                return archivo
        return ruta

    def _set_estado(self, mensaje, detalle=""):
        self.estado.set(mensaje)
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, detalle)
        self.detail_text.configure(state="disabled")

    def _cargar_impresoras(self):
        detectadas = detectar_impresoras_windows()
        self.impresoras = detectadas or IMPRESORAS_FALLBACK
        self.printer_combo["values"] = self.impresoras

        actual = self.impresora.get().strip()
        if actual not in self.impresoras:
            self.impresora.set(self.impresoras[0] if self.impresoras else "")

        origen = "Windows" if detectadas else "lista fallback"
        detalle = "\n".join(
            self.impresoras) if self.impresoras else "No hay impresoras disponibles."
        self._set_estado(f"Impresoras cargadas ({origen}).", detalle)

    def _cargar_pdfs_locales(self):
        self.pdfs = obtener_pdfs_disponibles()
        valores = [str(pdf) if pdf.parent ==
                   BASE_DIR else pdf.name for pdf in self.pdfs]
        self.pdf_combo["values"] = valores
        if valores and not self.archivo_pdf.get():
            self.archivo_pdf.set(valores[0])
        self._set_estado(
            "Lista de PDFs actualizada.",
            "\n".join(
                valores) if valores else "No se encontraron PDFs en la carpeta paralela ni en la carpeta principal.",
        )

    def _seleccionar_pdf(self):
        archivo = filedialog.askopenfilename(
            title="Selecciona un PDF",
            initialdir=str(WORKSPACE_DIR),
            filetypes=[("Archivos PDF", "*.pdf")],
        )
        if archivo:
            self.archivo_pdf.set(archivo)
            self._leer_paginas_pdf()

    def _leer_paginas_pdf(self):
        try:
            archivo = self._ruta_pdf_actual()
            total = obtener_total_paginas(archivo)
        except Exception as exc:
            messagebox.showerror("PDF no válido", str(exc))
            self.total_paginas.set("Total de páginas: -")
            return

        self.total_paginas.set(f"Total de páginas: {total}")
        self._set_estado(
            "PDF cargado correctamente.",
            f"Archivo: {archivo}\nTotal de páginas detectadas: {total}",
        )

    def _preparar_tandas(self):
        try:
            archivo_pdf = self._ruta_pdf_actual()
            if not self.impresora.get().strip():
                raise ValueError("No hay impresora seleccionada.")
            pagina_inicio = int(self.pagina_inicio.get())
            paginas_por_tanda = int(self.paginas_por_tanda.get())
            total = validar_parametros(
                archivo_pdf, pagina_inicio, paginas_por_tanda)
            self.tandas = crear_tandas(
                archivo_pdf, pagina_inicio, self.impresora.get(), paginas_por_tanda)
        except ValueError as exc:
            messagebox.showerror("Parámetros inválidos", str(exc))
            return
        except Exception as exc:
            messagebox.showerror(
                "No se pudieron preparar las tandas", str(exc))
            return

        if not self.tandas:
            messagebox.showwarning(
                "Sin tandas", "No se generaron tandas para los parámetros indicados.")
            return

        self.total_paginas.set(f"Total de páginas: {total}")
        self.tanda_actual_idx = 0
        self.etapa_actual = "lista_para_frente"
        self._mostrar_tanda_actual(
            "Tandas preparadas. Ya puedes imprimir el frente de la primera tanda.")
        self._actualizar_controles()

    def _tanda_actual(self):
        if 0 <= self.tanda_actual_idx < len(self.tandas):
            return self.tandas[self.tanda_actual_idx]
        return None

    def _mostrar_tanda_actual(self, encabezado):
        tanda = self._tanda_actual()
        if not tanda:
            self._set_estado("No hay una tanda activa.")
            return

        total_tandas = len(self.tandas)
        porcentaje = int((self.tanda_actual_idx / total_tandas) * 100)
        detalle = (
            f"PDF: {self._ruta_pdf_actual()}\n"
            f"Impresora: {self.impresora.get()}\n"
            f"Tanda: {tanda['id']} de {total_tandas}\n"
            f"Páginas: {tanda['pags']}\n"
            f"Progreso estimado: {porcentaje}%\n\n"
            f"Frente: {tanda['frente']}\n"
            f"Dorso: {tanda['dorso'] or 'No aplica'}"
        )
        self._set_estado(encabezado, detalle)

    def _imprimir_frente(self):
        tanda = self._tanda_actual()
        if not tanda:
            return
        try:
            imprimir_pdf(tanda["frente"], self.impresora.get())
        except Exception as exc:
            messagebox.showerror("Error de impresión", str(exc))
            return

        if tanda["dorso"]:
            self.etapa_actual = "lista_para_dorso"
            self._mostrar_tanda_actual(
                "Frente enviado. Gira el papel y luego usa 'Imprimir dorso'.")
        else:
            self.etapa_actual = "libro_finalizado"
            self._mostrar_tanda_actual(
                "La última tanda solo tenía frente. El libro ha terminado.")
        self._actualizar_controles()

    def _imprimir_dorso(self):
        tanda = self._tanda_actual()
        if not tanda or not tanda["dorso"]:
            return
        try:
            imprimir_pdf(tanda["dorso"], self.impresora.get())
        except Exception as exc:
            messagebox.showerror("Error de impresión", str(exc))
            return

        self.etapa_actual = "pendiente_confirmacion"
        self._mostrar_tanda_actual(
            "Dorso enviado. Revisa el resultado y confirma si la tanda salió bien.")
        self._actualizar_controles()

    def _confirmar_tanda(self):
        tanda = self._tanda_actual()
        if not tanda:
            return

        if self.etapa_actual == "pendiente_confirmacion":
            if not messagebox.askyesno("Confirmar tanda", "¿La tanda salió bien?"):
                self._set_estado(
                    "Proceso detenido para corrección manual.",
                    "No se avanzó a la siguiente tanda. Puedes reimprimir o reiniciar el proceso.",
                )
                return

        self.tanda_actual_idx += 1
        if self.tanda_actual_idx >= len(self.tandas):
            self.etapa_actual = "libro_finalizado"
            self._set_estado(
                "Proceso finalizado con éxito.",
                f"Se completaron {len(self.tandas)} tandas. Salidas guardadas en {OUTPUT_DIR}",
            )
        else:
            self.etapa_actual = "lista_para_frente"
            self._mostrar_tanda_actual(
                "Tanda confirmada. Ya puedes imprimir el frente de la siguiente tanda.")
        self._actualizar_controles()

    def _detener_proceso(self):
        self.etapa_actual = "detenido"
        self._set_estado(
            "Proceso detenido.",
            "Puedes reiniciar el estado actual o preparar las tandas nuevamente.",
        )
        self._actualizar_controles()

    def _reiniciar_estado(self):
        self.tandas = []
        self.tanda_actual_idx = -1
        self.etapa_actual = "sin_preparar"
        self._set_estado(
            "Estado reiniciado.",
            f"Las salidas previas quedan disponibles en {OUTPUT_DIR}.",
        )
        self._actualizar_controles()

    def _actualizar_controles(self):
        self.prepare_button.configure(state="normal")
        self.frente_button.configure(
            state="normal" if self.etapa_actual == "lista_para_frente" else "disabled")
        self.dorso_button.configure(
            state="normal" if self.etapa_actual == "lista_para_dorso" else "disabled")
        self.ok_button.configure(
            state="normal" if self.etapa_actual == "pendiente_confirmacion" else "disabled")
        self.stop_button.configure(
            state="normal" if self.etapa_actual in {
                "lista_para_frente", "lista_para_dorso", "pendiente_confirmacion", "detenido"} else "disabled"
        )
        self.reset_button.configure(state="normal")

    def run(self):
        self.root.mainloop()


def main():
    PrintApp().run()


if __name__ == "__main__":
    main()
