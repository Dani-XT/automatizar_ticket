import tkinter as tk

class App:
    def __init__(self, base_dir):
        self.base_dir = base_dir

        self.root = tk.Tk()
        self.root.title("Carga automatica de Ticket")
        self.root.geometry("650x350")
        self.root.resizable(False, False)
        self.root.configure(bg="#E91A1D")
        
        icon_path = self.base_dir / "src/assets/favicon.png"
        self.icon_img = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(True, self.icon_img)
    
    def run(self):
        self.root.mainloop()

