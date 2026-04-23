import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image, ImageTk
import pikepdf

try:
    import pymupdf as fitz
except Exception:
    try:
        import fitz
    except Exception:
        fitz = None

try:
    import win32api
    import win32print
except Exception:
    win32api = None
    win32print = None

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False
    DND_FILES = None
    TkinterDnD = None


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "Logo.png"
ICON_PATH = ASSETS_DIR / "app.ico"
SUMATRA_PATH = Path(r"C:\Users\karsc\AppData\Local\SumatraPDF\SumatraPDF.exe")
OUTPUT_DIR = BASE_DIR / "salidas"
UPDATE_REPO_OWNER = "carscx"
UPDATE_REPO_NAME = "bunker-print-master-gui"
UPDATE_API_URL = f"https://api.github.com/repos/{UPDATE_REPO_OWNER}/{UPDATE_REPO_NAME}/releases/latest"

IMPRESORAS_FALLBACK = [
    "EPSON_L5590_RAW",
    "EPSON_L3250_RAW",
    "BROTHER_L2360D_RAW",
]


def parse_version(value):
    if not value:
        return (0,)
    cleaned = value.strip().lstrip("vV")
    nums = re.findall(r"\d+", cleaned)
    if not nums:
        return (0,)
    return tuple(int(n) for n in nums)


def version_to_text(value):
    if not value:
        return "0.0.0"
    cleaned = value.strip().lstrip("vV")
    return cleaned or "0.0.0"


def obtener_version_local():
    version_files = []
    if getattr(sys, "frozen", False):
        version_files.append(
            Path(sys.executable).resolve().parent / "version.txt")
    version_files.append(BASE_DIR / "version.txt")

    for file_path in version_files:
        try:
            if file_path.exists():
                data = file_path.read_text(encoding="utf-8").strip()
                if data:
                    return version_to_text(data)
        except Exception:
            continue
    return "0.0.0"


def obtener_release_mas_reciente():
    req = urllib.request.Request(
        UPDATE_API_URL,
        headers={"User-Agent": "BunkerPrintMasterGUI-Updater"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    tag_name = payload.get("tag_name") or payload.get("name") or "0.0.0"
    version = version_to_text(tag_name)
    assets = payload.get("assets", [])

    installer_asset = None
    for asset in assets:
        name = str(asset.get("name", ""))
        if name.startswith("Setup-Bunker-Print-Master-GUI-") and name.endswith(".exe"):
            installer_asset = asset
            break

    if not installer_asset:
        raise RuntimeError(
            "No se encontro el instalador en la ultima release.")

    download_url = installer_asset.get("browser_download_url")
    if not download_url:
        raise RuntimeError("La release no contiene URL de descarga valida.")

    return {
        "version": version,
        "installer_name": installer_asset.get("name", "setup.exe"),
        "download_url": download_url,
    }


def descargar_archivo(url, destino):
    req = urllib.request.Request(
        url, headers={"User-Agent": "BunkerPrintMasterGUI-Updater"})
    with urllib.request.urlopen(req, timeout=60) as response, open(destino, "wb") as out:
        shutil.copyfileobj(response, out)


def ejecutar_instalador_silencioso(installer_path):
    args = [
        str(installer_path),
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/SP-",
        "/CLOSEAPPLICATIONS",
        "/RESTARTAPPLICATIONS",
    ]
    subprocess.Popen(args, close_fds=True)


def beep():
    try:
        import winsound
        winsound.Beep(1000, 420)
    except Exception:
        print("\a")


def detectar_impresoras_windows():
    if os.name != "nt":
        return []

    if win32print:
        try:
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            datos = win32print.EnumPrinters(flags)
            nombres = []
            for item in datos:
                if len(item) >= 3 and item[2]:
                    nombres.append(str(item[2]).strip())
            return sorted(set([x for x in nombres if x]), key=str.lower)
        except Exception:
            pass

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


def obtener_total_paginas(archivo_pdf):
    pdf_temp = pikepdf.Pdf.open(str(archivo_pdf))
    try:
        return len(pdf_temp.pages)
    finally:
        pdf_temp.close()


def obtener_pdfs_disponibles():
    salida = []
    for carpeta in (BASE_DIR, WORKSPACE_DIR):
        for archivo in carpeta.iterdir():
            if archivo.is_file() and archivo.suffix.lower() == ".pdf" and not archivo.name.startswith("FIX_"):
                salida.append(archivo)

    vistos = set()
    final = []
    for archivo in salida:
        clave = str(archivo.resolve()).lower()
        if clave in vistos:
            continue
        vistos.add(clave)
        final.append(archivo)
    return final


def validar_parametros(archivo_pdf, pagina_inicio, paginas_por_tanda):
    if not archivo_pdf:
        raise ValueError("Debes seleccionar un archivo PDF.")
    if not archivo_pdf.exists():
        raise FileNotFoundError(f"No se encontro el archivo: {archivo_pdf}")
    if pagina_inicio < 1:
        raise ValueError("La pagina inicial debe ser mayor o igual a 1.")
    if paginas_por_tanda < 1:
        raise ValueError(
            "Las hojas por tanda deben ser mayores o iguales a 1.")

    total_paginas = obtener_total_paginas(archivo_pdf)
    if pagina_inicio > total_paginas:
        raise ValueError(
            f"La pagina inicial no puede superar el total del documento ({total_paginas})."
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
                    "folder": str(folder),
                }
            )
            num_tanda += 1
        return tandas
    finally:
        pdf.close()


def imprimir_pdf(archivo, impresora):
    if win32api and win32print:
        try:
            win32api.ShellExecute(0, "printto", str(
                archivo), f'"{impresora}"', ".", 0)
            beep()
            return
        except Exception:
            pass

    if not SUMATRA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontro metodo de impresion. Instala SumatraPDF en {SUMATRA_PATH}"
        )

    subprocess.run(
        f'"{SUMATRA_PATH}" -print-to "{impresora}" -exit-on-print "{archivo}"',
        shell=True,
        check=True,
    )
    beep()


class PrintApp:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = ctk.CTk()
        self.root.title("BUNKER PRINT MASTER")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if screen_w <= 1366 and screen_h <= 768:
            self.ui_mode = "compact"
            scale = 0.88
        elif screen_w <= 1600 and screen_h <= 900:
            self.ui_mode = "normal"
            scale = 0.96
        else:
            self.ui_mode = "wide"
            scale = 1.0
        # Evita recortes de texto de CustomTkinter en pantallas bajas.
        ctk.set_widget_scaling(1.0)

        if self.ui_mode == "compact":
            self.fs_title = 30
            self.fs_subtitle = 14
            self.fs_step_main = 14
            self.fs_step_secondary = 13
            self.fs_body = 13
            self.fs_status = 14
            self.fs_tanda = 16
            self.step_wrap = 250
            self.header_height = 70
            self.step1_title = "PASO 1: Preparar"
            self.step2_title = "PASO 2: Frente"
        elif self.ui_mode == "normal":
            self.fs_title = 38
            self.fs_subtitle = 16
            self.fs_step_main = 17
            self.fs_step_secondary = 15
            self.fs_body = 14
            self.fs_status = 15
            self.fs_tanda = 19
            self.step_wrap = 290
            self.header_height = 90
            self.step1_title = "PASO 1: Preparar Tandas"
            self.step2_title = "PASO 2: Imprimir Frente"
        else:
            self.fs_title = 46
            self.fs_subtitle = 18
            self.fs_step_main = 20
            self.fs_step_secondary = 17
            self.fs_body = 15
            self.fs_status = 16
            self.fs_tanda = 22
            self.header_height = 110
            self.step_wrap = 360
            self.step1_title = "PASO 1: Preparar Tandas"
            self.step2_title = "PASO 2: Imprimir Frente"

        self.root.geometry("1440x840")
        self.root.minsize(1220, 680)

        if ICON_PATH.exists():
            try:
                self.root.iconbitmap(str(ICON_PATH))
            except Exception:
                pass

        self.impresoras = detectar_impresoras_windows() or IMPRESORAS_FALLBACK
        self.archivo_pdf = tk.StringVar(value="")
        self.impresora = tk.StringVar(
            value=self.impresoras[0] if self.impresoras else "")
        self.pagina_inicio = tk.StringVar(value="1")
        self.paginas_por_tanda = tk.StringVar(value="50")
        self.total_paginas = tk.StringVar(value="Total de paginas: -")
        self.version_local = obtener_version_local()

        self.tandas = []
        self.tanda_actual_idx = -1
        self.etapa_actual = "sin_preparar"

        self.pdf_catalog = []
        self.pdf_records = []
        self.preview_images = []

        self.logo_header = self._load_ctk_image(LOGO_PATH, (52, 52))
        self.drop_active = False
        self.drop_pulse = False

        self._build_ui()
        self._cargar_pdfs_locales()
        self._actualizar_controles()

    def _load_ctk_image(self, path, size):
        if not path.exists():
            return None
        try:
            img = Image.open(path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            return None

    def _build_ui(self):
        self.root.grid_columnconfigure(0, weight=5, minsize=520)
        self.root.grid_columnconfigure(1, weight=6, minsize=620)
        self.root.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.root, corner_radius=0,
                              fg_color="#eef3fa", height=self.header_height)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="", image=self.logo_header).grid(
            row=0, column=0, padx=(20, 10), pady=14)

        title_wrap = ctk.CTkFrame(header, fg_color="transparent")
        title_wrap.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            title_wrap,
            text="BUNKER PRINT MASTER",
            font=ctk.CTkFont("Segoe UI", self.fs_title, "bold"),
            text_color="#1f2a37",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_wrap,
            text="Listado y Previsualizacion",
            font=ctk.CTkFont("Segoe UI", self.fs_subtitle),
            text_color="#5b6675",
        ).pack(anchor="w")

        left = ctk.CTkFrame(self.root, corner_radius=18, fg_color="#f7f9fc")
        right = ctk.CTkFrame(self.root, corner_radius=18, fg_color="#f7f9fc")
        left.grid(row=1, column=0, sticky="nsew", padx=(14, 8), pady=(12, 14))
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 14), pady=(12, 14))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_drop_panel(left)
        self._build_config_panel(left)
        self._build_pdf_list_panel(left)

        self._build_step_panel(right)
        self._build_preview_and_status_panel(right)

    def _build_drop_panel(self, parent):
        drop = ctk.CTkFrame(parent, corner_radius=14, fg_color="#ffffff")
        drop.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        drop.grid_columnconfigure(0, weight=1)

        self.drop_canvas = tk.Canvas(
            drop,
            height=94,
            bg="#f8fbff",
            highlightthickness=0,
            bd=0,
        )
        self.drop_canvas.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.drop_canvas.bind("<Configure>", self._redraw_drop_zone)
        self.drop_canvas.bind("<Button-1>", lambda _e: self._seleccionar_pdf())

        if DND_AVAILABLE:
            try:
                for widget in (self.drop_canvas, self.root):
                    if hasattr(widget, "drop_target_register") and hasattr(widget, "dnd_bind"):
                        widget.drop_target_register(DND_FILES)
                        widget.dnd_bind("<<Drop>>", self._on_drop_pdf)
                        widget.dnd_bind("<<DropEnter>>", self._on_drop_enter)
                        widget.dnd_bind("<<DropLeave>>", self._on_drop_leave)
                self.drop_hint = "Arrastra y suelta un PDF aqui o haz clic para buscar"
            except Exception:
                self.drop_hint = "Haz clic para seleccionar un PDF"
        else:
            self.drop_hint = "Haz clic para seleccionar un PDF"

        self._redraw_drop_zone()

    def _redraw_drop_zone(self, _event=None):
        self.drop_canvas.delete("all")
        w = max(self.drop_canvas.winfo_width(), 20)
        h = max(self.drop_canvas.winfo_height(), 20)
        if self.drop_active:
            fill = "#e7f4ff" if self.drop_pulse else "#d9edff"
            outline = "#1d6fb8"
            hint = "Suelta los PDFs aqui"
        else:
            fill = "#f8fbff"
            outline = "#4d7fb0"
            hint = self.drop_hint

        self.drop_canvas.configure(bg=fill)
        self.drop_canvas.create_rectangle(
            6,
            6,
            w - 6,
            h - 6,
            dash=(6, 4),
            outline=outline,
            width=2,
        )
        self.drop_canvas.create_text(
            w / 2,
            h / 2,
            text=hint,
            fill="#2f4c6f",
            font=("Segoe UI", 12, "bold"),
        )

    def _pulse_drop_zone(self):
        if not self.drop_active:
            return
        self.drop_pulse = not self.drop_pulse
        self._redraw_drop_zone()
        self.root.after(220, self._pulse_drop_zone)

    def _on_drop_enter(self, _event):
        self.drop_active = True
        self.drop_pulse = False
        self._redraw_drop_zone()
        self._pulse_drop_zone()
        return "copy"

    def _on_drop_leave(self, _event):
        self.drop_active = False
        self.drop_pulse = False
        self._redraw_drop_zone()
        return "copy"

    def _on_drop_pdf(self, event):
        self.drop_active = False
        self.drop_pulse = False
        self._redraw_drop_zone()

        data = (event.data or "").strip()
        if not data:
            return "copy"

        try:
            candidates = list(self.root.tk.splitlist(data))
        except Exception:
            candidates = [data]

        rutas_validas = []
        for candidate in candidates:
            cleaned = str(candidate).strip().strip("{}\"")
            if cleaned.lower().startswith("file://"):
                cleaned = urllib.parse.unquote(
                    cleaned.replace("file:///", "", 1))

            path = Path(cleaned)
            if path.exists() and path.suffix.lower() == ".pdf":
                rutas_validas.append(path)

        if rutas_validas:
            self._agregar_pdfs(rutas_validas)
            return "copy"

        messagebox.showwarning(
            "Archivo invalido", "Solo se permiten archivos PDF.")
        return "copy"

    def _build_config_panel(self, parent):
        cfg = ctk.CTkFrame(parent, corner_radius=14, fg_color="#eaf0f7")
        cfg.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        cfg.grid_columnconfigure(1, weight=3, minsize=220)
        cfg.grid_columnconfigure(2, weight=1)
        cfg.grid_columnconfigure(3, weight=2, minsize=140)

        ctk.CTkLabel(cfg, text="PDF", font=ctk.CTkFont("Segoe UI", 15, "bold")).grid(
            row=0, column=0, padx=(14, 8), pady=8, sticky="w"
        )
        self.pdf_entry = ctk.CTkEntry(
            cfg,
            textvariable=self.archivo_pdf,
            placeholder_text="Ruta del PDF seleccionado",
            height=36,
            corner_radius=10,
        )
        self.pdf_entry.grid(row=0, column=1, columnspan=3,
                            sticky="ew", padx=(0, 14), pady=8)

        ctk.CTkLabel(cfg, text="Impresora", font=ctk.CTkFont("Segoe UI", 15, "bold")).grid(
            row=1, column=0, padx=(14, 8), pady=8, sticky="w"
        )
        self.printer_combo = ctk.CTkComboBox(
            cfg,
            variable=self.impresora,
            values=self.impresoras if self.impresoras else [""],
            height=34,
            width=260,
            corner_radius=10,
            state="readonly",
        )
        self.printer_combo.grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=8)
        ctk.CTkButton(
            cfg,
            text="Actualizar",
            width=110,
            height=34,
            command=self._cargar_impresoras,
        ).grid(row=1, column=3, padx=(8, 14), pady=8, sticky="ew")

        ctk.CTkLabel(cfg, text="Pagina inicial", font=ctk.CTkFont("Segoe UI", 15, "bold")).grid(
            row=2, column=0, padx=(14, 8), pady=8, sticky="w"
        )
        self.entry_inicio = ctk.CTkEntry(
            cfg, textvariable=self.pagina_inicio, height=32, width=140)
        self.entry_inicio.grid(row=2, column=1, sticky="w", pady=8)

        ctk.CTkLabel(cfg, text="Hojas por tanda", font=ctk.CTkFont("Segoe UI", 15, "bold")).grid(
            row=2, column=2, padx=(8, 8), pady=8, sticky="w"
        )
        self.entry_tanda = ctk.CTkEntry(
            cfg, textvariable=self.paginas_por_tanda, height=32, width=140)
        self.entry_tanda.grid(
            row=2, column=3, padx=(0, 14), pady=8, sticky="w")

        ctk.CTkLabel(cfg, textvariable=self.total_paginas, font=ctk.CTkFont("Segoe UI", 15, "bold")).grid(
            row=3, column=0, columnspan=2, padx=14, pady=(4, 10), sticky="w"
        )
        ctk.CTkButton(
            cfg,
            text="Leer paginas",
            width=120,
            height=32,
            command=self._leer_paginas_pdf,
        ).grid(row=3, column=2, columnspan=2, padx=(8, 14), pady=(4, 10), sticky="ew")

    def _build_pdf_list_panel(self, parent):
        panel = ctk.CTkFrame(parent, corner_radius=14, fg_color="#ffffff")
        panel.grid(row=2, column=0, sticky="nsew", padx=14, pady=(8, 14))
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="Entrada | Tandas Preparadas | Salidas",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color="#34506f",
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        ctk.CTkLabel(
            panel,
            text="Listado de PDF",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="#5b6675",
        ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

        style = ttk.Style()
        style.configure("Pdf.Treeview", font=("Segoe UI", 11), rowheight=28)
        style.configure("Pdf.Treeview.Heading", font=("Segoe UI", 11, "bold"))

        table_wrap = ctk.CTkFrame(panel, corner_radius=10, fg_color="#f4f7fb")
        table_wrap.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        self.name_tree = ttk.Treeview(
            table_wrap,
            style="Pdf.Treeview",
            columns=("nombre",),
            show="headings",
            selectmode="browse",
        )
        self.name_tree.heading("nombre", text="Nombre")
        self.name_tree.column("nombre", width=360, anchor="w")

        self.pdf_tree = ttk.Treeview(
            table_wrap,
            style="Pdf.Treeview",
            columns=("hojas", "tandas"),
            show="headings",
            selectmode="browse",
            height=16,
        )
        self.pdf_tree.heading("hojas", text="Hojas")
        self.pdf_tree.heading("tandas", text="Tandas")
        self.pdf_tree.column("hojas", width=90, anchor="center")
        self.pdf_tree.column("tandas", width=90, anchor="center")

        self.name_tree.grid(row=0, column=0, sticky="nsew")
        self.pdf_tree.grid(row=0, column=1, sticky="ns")

        ybar = ttk.Scrollbar(table_wrap, orient="vertical",
                             command=self._sync_scroll)
        self.name_tree.configure(yscrollcommand=ybar.set)
        self.pdf_tree.configure(yscrollcommand=ybar.set)
        ybar.grid(row=0, column=2, sticky="ns")

        self.name_tree.bind("<<TreeviewSelect>>", self._on_select_pdf)

    def _build_step_panel(self, parent):
        top = ctk.CTkFrame(parent, corner_radius=14, fg_color="#ffffff")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)
        self.steps_top = top

        step1 = ctk.CTkFrame(top, corner_radius=12, fg_color="#dfeaf8")
        step2 = ctk.CTkFrame(top, corner_radius=12, fg_color="#e8edf5")
        step1.grid(row=0, column=0, sticky="nsew", padx=(12, 8), pady=12)
        step2.grid(row=0, column=1, sticky="nsew", padx=(8, 12), pady=12)
        step2.grid_columnconfigure(0, weight=1)
        self.step1_frame = step1
        self.step2_frame = step2

        self.prepare_button = ctk.CTkButton(
            step1,
            text=self.step1_title,
            height=54,
            corner_radius=10,
            font=ctk.CTkFont("Segoe UI", self.fs_step_main, "bold"),
            command=self._preparar_tandas,
            fg_color="#2f79b7",
            hover_color="#245f91",
        )
        self.prepare_button.pack(fill="x", padx=12, pady=(12, 10))

        ctk.CTkLabel(
            step1,
            text="Click para actualizar el PDF con la separacion\ny habilitar el siguiente paso.",
            justify="left",
            wraplength=self.step_wrap,
            font=ctk.CTkFont("Segoe UI", self.fs_body),
            text_color="#334155",
        ).pack(anchor="w", padx=14, pady=(0, 12))

        self.frente_button = ctk.CTkButton(
            step2,
            text=self.step2_title,
            height=48,
            font=ctk.CTkFont("Segoe UI", self.fs_step_main, "bold"),
            command=self._imprimir_frente,
        )
        self.frente_button.grid(
            row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

        self.dorso_button = ctk.CTkButton(
            step2,
            text="Imprimir Dorso",
            height=44,
            font=ctk.CTkFont("Segoe UI", self.fs_step_secondary, "bold"),
            command=self._imprimir_dorso,
            fg_color="#6b8cad",
            hover_color="#56718e",
        )
        self.dorso_button.grid(
            row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(
            step2,
            text="Usa estas para imprimir un lado a la vez y evitar atascos.",
            justify="left",
            wraplength=self.step_wrap,
            font=ctk.CTkFont("Segoe UI", self.fs_body),
            text_color="#334155",
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))

        self.steps_top.bind("<Configure>", self._on_steps_resize)

    def _on_steps_resize(self, _event=None):
        if not hasattr(self, "steps_top"):
            return
        width = self.steps_top.winfo_width()
        if width < 780:
            self.step1_frame.grid_configure(
                row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
            self.step2_frame.grid_configure(
                row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
            self.steps_top.grid_columnconfigure(1, weight=0)
        else:
            self.step1_frame.grid_configure(
                row=0, column=0, padx=(12, 8), pady=12, sticky="nsew")
            self.step2_frame.grid_configure(
                row=0, column=1, padx=(8, 12), pady=12, sticky="nsew")
            self.steps_top.grid_columnconfigure(1, weight=1)

    def _build_preview_and_status_panel(self, parent):
        bottom = ctk.CTkFrame(parent, corner_radius=14, fg_color="#ffffff")
        bottom.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 14))
        bottom.grid_rowconfigure(1, weight=1)
        bottom.grid_columnconfigure(0, weight=1)

        self.tanda_label = ctk.CTkLabel(
            bottom,
            text="Tanda 0 de 0",
            font=ctk.CTkFont("Segoe UI", self.fs_tanda, "bold"),
            text_color="#264b72",
        )
        self.tanda_label.grid(row=0, column=0, sticky="e",
                              padx=14, pady=(12, 8))

        preview_wrap = ctk.CTkFrame(
            bottom, corner_radius=10, fg_color="#ecf2f8")
        preview_wrap.grid(row=1, column=0, sticky="nsew",
                          padx=12, pady=(0, 10))
        preview_wrap.grid_rowconfigure(0, weight=1, minsize=340)
        preview_wrap.grid_columnconfigure((0, 1, 2), weight=1)

        self.preview_labels = []
        for col in range(3):
            card = tk.Frame(preview_wrap, bg="#ffffff", highlightthickness=0)
            card.grid(row=0, column=col, padx=10, pady=12, sticky="nsew")
            card.grid_propagate(False)
            card.configure(width=260, height=330)

            box = tk.Label(
                card,
                text="Sin previsualizacion",
                bg="#ffffff",
                fg="#6b7280",
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                anchor="center",
                justify="center",
                wraplength=220,
            )
            box.pack(fill="both", expand=True)
            self.preview_labels.append(box)

        status_wrap = ctk.CTkFrame(
            bottom, corner_radius=10, fg_color="#eef3f9")
        status_wrap.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        status_wrap.grid_columnconfigure((0, 1, 2), weight=1)

        self.estado_msg = ctk.CTkLabel(
            status_wrap,
            text="Estado: listo para preparar tandas.",
            font=ctk.CTkFont("Segoe UI", self.fs_status, "bold"),
            text_color="#1f2a37",
        )
        self.estado_msg.grid(row=0, column=0, columnspan=3,
                             sticky="w", padx=12, pady=(12, 6))

        self.info_pdf = ctk.CTkLabel(
            status_wrap, text="PDF: -", font=ctk.CTkFont("Segoe UI", self.fs_body))
        self.info_impresora = ctk.CTkLabel(
            status_wrap, text="Impresora actual: -", font=ctk.CTkFont("Segoe UI", self.fs_body))
        self.info_pdf.grid(row=1, column=0, columnspan=3,
                           sticky="w", padx=12, pady=2)
        self.info_impresora.grid(
            row=2, column=0, columnspan=3, sticky="w", padx=12, pady=2)

        self.progress = ctk.CTkProgressBar(status_wrap)
        self.progress.grid(row=3, column=0, columnspan=3,
                           sticky="ew", padx=12, pady=(8, 10))
        self.progress.set(0)

        self.ok_button = ctk.CTkButton(
            status_wrap,
            text="Tanda correcta / siguiente",
            command=self._confirmar_tanda,
            height=40,
        )
        self.stop_button = ctk.CTkButton(
            status_wrap,
            text="Detener y Revisar",
            command=self._detener_proceso,
            height=40,
            fg_color="#b45309",
            hover_color="#92400e",
        )
        self.reset_button = ctk.CTkButton(
            status_wrap,
            text="Reiniciar Proceso",
            command=self._reiniciar_estado,
            height=40,
            fg_color="#64748b",
            hover_color="#475569",
        )

        self.ok_button.grid(row=4, column=0, padx=(12, 8),
                            pady=(0, 12), sticky="ew")
        self.stop_button.grid(row=4, column=1, padx=8,
                              pady=(0, 12), sticky="ew")
        self.reset_button.grid(row=4, column=2, padx=(
            8, 12), pady=(0, 12), sticky="ew")

        self.update_button = ctk.CTkButton(
            status_wrap,
            text=f"Actualizar app (v{self.version_local})",
            command=self._buscar_actualizacion,
            height=38,
            fg_color="#166534",
            hover_color="#14532d",
        )
        self.update_button.grid(row=5, column=0, columnspan=3,
                                padx=12, pady=(0, 12), sticky="ew")

    def _sync_scroll(self, *args):
        self.name_tree.yview(*args)
        self.pdf_tree.yview(*args)

    def _ruta_pdf_actual(self):
        valor = self.archivo_pdf.get().strip()
        if not valor:
            return None
        ruta = Path(valor)
        if ruta.exists():
            return ruta
        for item in self.pdf_catalog:
            if item.name == valor:
                return item
        return ruta

    def _set_estado(self, mensaje):
        self.estado_msg.configure(text=f"Estado: {mensaje}")

    def _buscar_actualizacion(self):
        self.update_button.configure(
            state="disabled", text="Buscando actualizacion...")
        self._set_estado("buscando nueva release...")
        worker = threading.Thread(
            target=self._buscar_actualizacion_worker, daemon=True)
        worker.start()

    def _buscar_actualizacion_worker(self):
        try:
            latest = obtener_release_mas_reciente()
            local_tuple = parse_version(self.version_local)
            remote_tuple = parse_version(latest["version"])

            if remote_tuple <= local_tuple:
                self.root.after(
                    0,
                    lambda: self._resultado_actualizacion(
                        f"No hay actualizaciones. Version actual: v{self.version_local}",
                        habilitar=True,
                    ),
                )
                return

            temp_dir = Path(tempfile.gettempdir()) / \
                "bunker-print-master-updates"
            temp_dir.mkdir(parents=True, exist_ok=True)
            installer_path = temp_dir / latest["installer_name"]

            self.root.after(
                0,
                lambda: self._set_estado(
                    f"descargando instalador v{latest['version']}..."),
            )
            descargar_archivo(latest["download_url"], installer_path)
            ejecutar_instalador_silencioso(installer_path)

            self.root.after(
                0,
                lambda: self._resultado_actualizacion(
                    f"Instalador v{latest['version']} lanzado. La app se cerrara para completar la actualizacion.",
                    habilitar=False,
                    cerrar_app=True,
                ),
            )
        except Exception as exc:
            self.root.after(
                0,
                lambda: self._resultado_actualizacion(
                    f"No se pudo actualizar automaticamente: {exc}",
                    habilitar=True,
                ),
            )

    def _resultado_actualizacion(self, mensaje, habilitar=True, cerrar_app=False):
        self._set_estado(mensaje)
        if habilitar:
            self.update_button.configure(
                state="normal", text=f"Actualizar app (v{self.version_local})")
        else:
            self.update_button.configure(
                state="disabled", text="Actualizacion en progreso...")
        if cerrar_app:
            self.root.after(1800, self.root.destroy)

    def _cargar_impresoras(self):
        detectadas = detectar_impresoras_windows()
        self.impresoras = detectadas or IMPRESORAS_FALLBACK
        self.printer_combo.configure(
            values=self.impresoras if self.impresoras else [""])
        if self.impresora.get() not in self.impresoras and self.impresoras:
            self.impresora.set(self.impresoras[0])
        self._set_estado("impresoras actualizadas")
        self._actualizar_info_panel()

    def _cargar_pdfs_locales(self):
        self.pdf_catalog = obtener_pdfs_disponibles()
        self._actualizar_registros_pdf()
        self._set_estado("listado de PDFs actualizado")

    def _agregar_pdf(self, ruta):
        self._agregar_pdfs([ruta])

    def _agregar_pdfs(self, rutas):
        primera = None
        agregados = 0

        for ruta in rutas:
            if not ruta.exists() or ruta.suffix.lower() != ".pdf":
                continue
            if primera is None:
                primera = ruta

            if all(str(ruta.resolve()).lower() != str(p.resolve()).lower() for p in self.pdf_catalog):
                self.pdf_catalog.insert(0, ruta)
                agregados += 1

        if primera is None:
            return

        self.archivo_pdf.set(str(primera))
        self._actualizar_registros_pdf()
        self._leer_paginas_pdf()
        if len(rutas) > 1:
            self._set_estado(f"{agregados} PDF(s) agregados por arrastre")

    def _actualizar_registros_pdf(self):
        try:
            paginas_tanda = max(int(self.paginas_por_tanda.get() or 1), 1)
        except Exception:
            paginas_tanda = 1

        self.pdf_records = []
        self.name_tree.delete(*self.name_tree.get_children())
        self.pdf_tree.delete(*self.pdf_tree.get_children())

        for idx, pdf_path in enumerate(self.pdf_catalog):
            try:
                hojas = obtener_total_paginas(pdf_path)
            except Exception:
                hojas = 0
            tandas = max((hojas + paginas_tanda - 1) // paginas_tanda, 0)
            self.pdf_records.append(
                {"path": pdf_path, "hojas": hojas, "tandas": tandas})

            iid = f"row_{idx}"
            self.name_tree.insert("", "end", iid=iid, values=(pdf_path.name,))
            self.pdf_tree.insert("", "end", iid=iid, values=(hojas, tandas))

        if self.pdf_records:
            self.name_tree.selection_set("row_0")
            self.pdf_tree.selection_set("row_0")
            self._usar_record(self.pdf_records[0])
        else:
            self.archivo_pdf.set("")
            self.total_paginas.set("Total de paginas: -")
            self._limpiar_preview()

    def _usar_record(self, record):
        self.archivo_pdf.set(str(record["path"]))
        self.total_paginas.set(f"Total de paginas: {record['hojas']}")
        self._actualizar_info_panel()
        self._render_preview(record["path"])

    def _on_select_pdf(self, _event):
        selected = self.name_tree.selection()
        if not selected:
            return
        iid = selected[0]
        self.pdf_tree.selection_set(iid)
        idx = int(iid.split("_")[1])
        if 0 <= idx < len(self.pdf_records):
            self._usar_record(self.pdf_records[idx])

    def _seleccionar_pdf(self):
        archivos = filedialog.askopenfilenames(
            title="Selecciona uno o varios PDF",
            initialdir=str(WORKSPACE_DIR),
            filetypes=[("Archivos PDF", "*.pdf")],
        )
        if not archivos:
            return
        rutas = [Path(p) for p in archivos if p]
        self._agregar_pdfs(rutas)

    def _leer_paginas_pdf(self):
        try:
            archivo = self._ruta_pdf_actual()
            total = obtener_total_paginas(archivo)
        except Exception as exc:
            messagebox.showerror("PDF no valido", str(exc))
            self.total_paginas.set("Total de paginas: -")
            return

        self.total_paginas.set(f"Total de paginas: {total}")
        self._set_estado("PDF cargado correctamente")
        self._actualizar_info_panel()
        self._render_preview(archivo)

    def _render_preview(self, pdf_path):
        self._limpiar_preview()

        if not fitz:
            for label in self.preview_labels:
                label.configure(text="Instala PyMuPDF para previsualizar")
            self._set_estado("previsualizacion no disponible: falta PyMuPDF")
            return

        try:
            doc = fitz.open(str(pdf_path))
            paginas = min(3, doc.page_count)
            successful_pages = 0

            for idx in range(paginas):
                try:
                    page = doc.load_page(idx)
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(0.75, 0.75), alpha=False)
                    img = Image.frombytes(
                        "RGB", (pix.width, pix.height), pix.samples)
                    img.thumbnail((260, 330), Image.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    self.preview_images.append(tk_img)
                    self.preview_labels[idx].configure(image=tk_img, text="")
                    self.preview_labels[idx].image = tk_img
                    successful_pages += 1
                except Exception as page_exc:
                    self.preview_labels[idx].configure(
                        text=f"Pagina {idx+1}\nerror: {page_exc}")

            doc.close()
            if successful_pages == paginas:
                self._set_estado("PDF cargado correctamente con previsualizacion")
            else:
                self._set_estado(f"PDF cargado: {successful_pages}/{paginas} paginas mostradas")
        except Exception as exc:
            for label in self.preview_labels:
                label.configure(text=f"Sin previsualizacion\n{exc}")
            self._set_estado(f"fallo en previsualizacion: {exc}")

    def _limpiar_preview(self):
        for label in self.preview_labels:
            label.image = None
            label.configure(image=None, text="Sin previsualizacion")
        self.preview_images = []

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
                archivo_pdf,
                pagina_inicio,
                self.impresora.get(),
                paginas_por_tanda,
            )
        except Exception as exc:
            messagebox.showerror(
                "No se pudieron preparar las tandas", str(exc))
            return

        if not self.tandas:
            messagebox.showwarning(
                "Sin tandas", "No se generaron tandas para los parametros indicados.")
            return

        self.tanda_actual_idx = 0
        self.etapa_actual = "lista_para_frente"
        self.total_paginas.set(f"Total de paginas: {total}")
        self._set_estado(
            "Tandas preparadas. Ya puedes imprimir el frente de la primera tanda.")
        self._actualizar_controles()
        self._actualizar_info_panel()

    def _tanda_actual(self):
        if 0 <= self.tanda_actual_idx < len(self.tandas):
            return self.tandas[self.tanda_actual_idx]
        return None

    def _imprimir_frente(self):
        tanda = self._tanda_actual()
        if not tanda:
            return
        try:
            imprimir_pdf(tanda["frente"], self.impresora.get())
        except Exception as exc:
            messagebox.showerror("Error de impresion", str(exc))
            return

        if tanda["dorso"]:
            self.etapa_actual = "lista_para_dorso"
            self._set_estado(
                "Frente enviado. Voltea las hojas y continua con Imprimir Dorso.")
        else:
            self.etapa_actual = "pendiente_confirmacion"
            self._set_estado(
                "Tanda sin dorso. Confirma para pasar a la siguiente.")
        self._actualizar_controles()
        self._actualizar_info_panel()

    def _imprimir_dorso(self):
        tanda = self._tanda_actual()
        if not tanda or not tanda["dorso"]:
            return
        try:
            imprimir_pdf(tanda["dorso"], self.impresora.get())
        except Exception as exc:
            messagebox.showerror("Error de impresion", str(exc))
            return

        self.etapa_actual = "pendiente_confirmacion"
        self._set_estado(
            "Dorso enviado. Revisa la tanda y confirma para continuar.")
        self._actualizar_controles()

    def _confirmar_tanda(self):
        tanda = self._tanda_actual()
        if not tanda:
            return

        if not messagebox.askyesno("Confirmar tanda", "La tanda salio bien?"):
            self._set_estado("Proceso detenido para revision manual.")
            self.etapa_actual = "detenido"
            self._actualizar_controles()
            return

        self.tanda_actual_idx += 1
        if self.tanda_actual_idx >= len(self.tandas):
            self.etapa_actual = "finalizado"
            self._set_estado("Proceso finalizado con exito.")
            self.progress.set(1)
        else:
            self.etapa_actual = "lista_para_frente"
            self._set_estado(
                "Tanda confirmada. Ya puedes imprimir el frente de la siguiente tanda.")

        self._actualizar_controles()
        self._actualizar_info_panel()

    def _detener_proceso(self):
        self.etapa_actual = "detenido"
        self._set_estado("Proceso detenido. Puedes revisar o reiniciar.")
        self._actualizar_controles()

    def _reiniciar_estado(self):
        self.tandas = []
        self.tanda_actual_idx = -1
        self.etapa_actual = "sin_preparar"
        self.progress.set(0)
        self._set_estado(
            "Estado reiniciado. Configura y prepara una nueva tanda.")
        self._actualizar_controles()
        self._actualizar_info_panel()

    def _actualizar_info_panel(self):
        self.info_pdf.configure(
            text=f"PDF Path: {self.archivo_pdf.get() or '-'}")
        self.info_impresora.configure(
            text=f"Impresora actual: {self.impresora.get() or '-'}")

        total_tandas = len(self.tandas)
        if total_tandas <= 0:
            self.tanda_label.configure(text="Tanda 0 de 0")
            self.progress.set(0)
            return

        actual = min(max(self.tanda_actual_idx + 1, 1), total_tandas)
        self.tanda_label.configure(text=f"Tanda {actual} de {total_tandas}")
        self.progress.set((actual - 1) / total_tandas)

    def _actualizar_controles(self):
        lista_para_frente = self.etapa_actual == "lista_para_frente"
        lista_para_dorso = self.etapa_actual == "lista_para_dorso"
        pendiente = self.etapa_actual == "pendiente_confirmacion"

        self.prepare_button.configure(state="normal")
        self.frente_button.configure(
            state="normal" if lista_para_frente else "disabled")
        self.dorso_button.configure(
            state="normal" if lista_para_dorso else "disabled")
        self.ok_button.configure(state="normal" if pendiente else "disabled")
        self.stop_button.configure(
            state="normal"
            if self.etapa_actual in {"lista_para_frente", "lista_para_dorso", "pendiente_confirmacion", "detenido"}
            else "disabled"
        )
        self.reset_button.configure(state="normal")

    def run(self):
        self.root.mainloop()


def main():
    app = PrintApp()
    app.run()


if __name__ == "__main__":
    main()
