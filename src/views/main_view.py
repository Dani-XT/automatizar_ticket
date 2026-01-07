import os
import tkinter as tk


class MainView(tk.Frame):
    def __init__(self, master, assets_dir, base_dir):
        super().__init__(master, bg="#E91A1D")
        self.assets_dir = assets_dir
        self.base_dir = base_dir

        self._load_assets()
        self._build_header()
        self._build_body()
        self._build_footer()

    def _load_assets(self):
        self.logo_img = tk.PhotoImage(file = self.assets_dir / "logo.png")
        self.input_img = tk.PhotoImage(file = self.assets_dir / "input_file.png")
        self.help_img = tk.PhotoImage(file = self.assets_dir / "helper.png")
        self.config_img = tk.PhotoImage(file = self.assets_dir / "configuracion.png")
        self.send_img = tk.PhotoImage(file = self.assets_dir / "enviar.png")

    def _build_header(self):
        header = tk.Frame(self, bg="#E91A1D")
        header.place(x=42, y=30)

        logo_label = tk.Label(header, image=self.logo_img, bg="#E91A1D")
        logo_label.pack(side="left")

        title_label = tk.Label(header, text="Carga Automatica de Ticket", font=("Segoe UI", 18, "bold"), fg="white", bg="#E91A1D")
        title_label.pack(side="left", padx=38)

    def _build_body(self):
        tk.Label(self, text="Cargar Planilla", font=("Segoe UI", 12, "bold"), fg="white", bg="#E91A1D").place(x=40, y=140)
        
        help_btn = tk.Button(self, image=self.help_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._open_help)
        help_btn.place(x=165, y=140)

        input_btn = tk.Button(self, image=self.input_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._select_file)
        input_btn.place(x=40, y=170)

    def _build_footer(self):
        footer =tk.Frame(self, bg="#E91A1D")
        footer.place(relx=0.5, y=300, anchor="center")

        config_btn = tk.Button(footer, image=self.config_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._open_config)
        config_btn.pack(side="left", padx=15)

        send_btn = tk.Button(footer, image=self.send_img, bg="#E91A1D", activebackground="#E91A1D", borderwidth=0, command=self._send)
        send_btn.pack(side="left", padx=15)

    
    def _open_help(self):
        help_file = self.base_dir / "readme.txt"

        if not help_file.exists():
            tk.messagebox.showerror(
                title="Archivo no encontrado",
                message="No se encontró el archivo de ayuda (readme.txt)."
            )
            return
        
        try:
            os.startfile(help_file)
        except Exception as e:
            tk.messagebox.showerror(
                title="Error al abrir ayuda",
                message=f"Ocurrió un error al intentar abrir el archivo:\n{e}"
            )

    def _select_file(self):
        print("hola 2")

    def _open_config(self):
        print("hola 3")

    def _send(self):
        print("hola 4")

