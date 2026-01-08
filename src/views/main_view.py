import os
import tkinter as tk
import shutil
from pathlib import Path
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk

from src import config

from .error_view import ErrorView

from src.controllers.excel_controller import ExcelController
from src.utils.tooltip import Tooltip


class MainView(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#E91A1D")

        self.select_file = None

        self._load_assets()
        self._build_header()
        self._build_body()
        self._build_footer()

    def _load_assets(self):
        self.logo_img = tk.PhotoImage(file = config.ASSETS_DIR / "main_frame/logo.png")
        
        excel_image = Image.open(config.ASSETS_DIR / "main_frame/excel.png")
        excel_image = excel_image.resize((40, 40), Image.LANCZOS)
        self.excel_img = ImageTk.PhotoImage(excel_image)
        
        self.input_img = tk.PhotoImage(file = config.ASSETS_DIR / "main_frame/input_file.png")
        self.help_img = tk.PhotoImage(file = config.ASSETS_DIR / "main_frame/helper.png")
        self.config_img = tk.PhotoImage(file = config.ASSETS_DIR / "main_frame/configuracion.png")
        self.send_img = tk.PhotoImage(file = config.ASSETS_DIR / "main_frame/enviar.png")
        self.clear_img = tk.PhotoImage(file = config.ASSETS_DIR / "main_frame/close.png")

    def _build_header(self):
        header = tk.Frame(self, bg="#E91A1D")
        header.place(x=42, y=30)

        logo_label = tk.Label(header, image=self.logo_img, bg="#E91A1D")
        logo_label.pack(side="left")

        title_label = tk.Label(header, text="Carga Automatica de Ticket", font=("Segoe UI", 18, "bold"), fg="white", bg="#E91A1D")
        title_label.pack(side="left", padx=38)

        excel_btn = tk.Button(header, image=self.excel_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._downlaod_excel, cursor="hand2")
        excel_btn.pack(side="left", padx=5)

        Tooltip(excel_btn, "Descargar Planilla")

    def _build_body(self):
        tk.Label(self, text="Cargar Planilla", font=("Segoe UI", 12, "bold"), fg="white", bg="#E91A1D").place(x=40, y=140)
        
        help_btn = tk.Button(self, image=self.help_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._open_help, cursor="hand2")
        help_btn.place(x=165, y=140)

        Tooltip(help_btn, "Ayuda")

        input_btn = tk.Button(self, image=self.input_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._select_file, cursor="hand2")
        input_btn.place(x=40, y=170)

        Tooltip(input_btn, "Cargar planilla")

        self.file_container = tk.Frame(self, bg="#FDF7F7")
        self.file_label = tk.Label(self.file_container, text="", font=("Segoe UI", 12, "bold"), fg="#333333", bg="#FDF7F7", anchor="w")
        self.clear_btn = tk.Button(self.file_container, image=self.clear_img, bg="#FDF7F7", activebackground="#FDF7F7", borderwidth=0, command=self._clear_file, cursor="hand2")

    def _build_footer(self):
        footer =tk.Frame(self, bg="#E91A1D")
        footer.place(relx=0.5, y=300, anchor="center")

        config_btn = tk.Button(footer, image=self.config_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._open_config, cursor="hand2")
        config_btn.pack(side="left", padx=15)

        send_btn = tk.Button(footer, image=self.send_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._send, cursor="hand2")
        send_btn.pack(side="left", padx=15)

    def _downlaod_excel(self):
        template_path = config.DOWNLOAD_DIR / "Planilla de Actividades - Nombre Tecnico.xlsx"
        if not template_path.exists():
            ErrorView(self, title="Plantilla no encontrada", messagebox="No se encontro la planilla de actividades")
            return

        save_path = filedialog.asksaveasfilename(title="Guardar planilla", defaultextension=".xlsx", filetypes=[("Archivos Excel", "*.xlsx")], initialfile=template_path.name)

        if not save_path:
            return

        try:
            shutil.copyfile(template_path, save_path)
            ErrorView(self, title="Descarga exitosa", message="La planilla se guardo correctamente.", level="info")
        
        except Exception as e:
            ErrorView(self, title="Error al guardar", message=str(e))

    def _open_help(self):
        help_file = config.BASE_DIR / "readme.txt"

        if not help_file.exists():
            ErrorView(self, title="Archivo no encontrado", message="No se encontró el archivo de ayuda (readme.txt).")
            return
        try:
            os.startfile(help_file)
        except Exception as e:
            # TODO: CAMBIAR POR UN VIEW DE ERRORES
            messagebox.showerror(
                title="Error al abrir ayuda",
                message=f"Ocurrió un error al intentar abrir el archivo:\n{e}"
            )

    def _select_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar planilla de Excel",
            filetypes=[
                ("Archivos Excel", "*.xlsx *.xls"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not file_path:
            return
        
        self.select_file = Path(file_path)
        self.file_label.config(text=self.select_file.name)
        
        if not self.file_container.winfo_ismapped():
            self.file_label.pack(side="left", fill="x", expand=True, padx=(5, 0))
            self.clear_btn.pack(side="right", padx=5)
            self.file_container.place(x=55, y=180, width=480, height=24)
        
    def _clear_file(self):
        self.select_file = None
        self.file_container.place_forget()

    def _open_config(self):
        print("hola 3")

    def _send(self):
        if not self.select_file:
            ErrorView(self, title="Error al enviar", message="Debe seleccionar un archivo antes de enviar")
            return
        
        try:
            ExcelController(self.select_file)

        except Exception as e:
            ErrorView(self, title="Error con el excel", message=e)



