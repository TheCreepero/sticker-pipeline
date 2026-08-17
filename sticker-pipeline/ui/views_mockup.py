import json
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

class MockupView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.image_path = None
        self.original_image = None
        self.display_image = None
        self.tk_image = None
        self.points = []          
        self.real_points = []     
        self.scale_factor = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.templates = {}

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        controls_frame = ctk.CTkFrame(self, width=250)
        controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        title = ctk.CTkLabel(controls_frame, text="Mockup Calibrator", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        # Browser Dropdown
        ctk.CTkLabel(controls_frame, text="Select Template:", font=ctk.CTkFont(weight="bold")).pack(padx=15, anchor="w")
        self.template_dropdown = ctk.CTkOptionMenu(controls_frame, values=["New Template..."], command=self.on_template_select)
        self.template_dropdown.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_load = ctk.CTkButton(controls_frame, text="📸 Load Image File", command=self.load_image)
        self.btn_load.pack(fill="x", padx=15, pady=10)

        self.btn_clear = ctk.CTkButton(controls_frame, text="❌ Clear Points", fg_color="#E03B3B", hover_color="#B82C2C", command=self.clear_points)
        self.btn_clear.pack(fill="x", padx=15, pady=10)

        self.btn_delete = ctk.CTkButton(controls_frame, text="🗑 Delete Template", fg_color="transparent", border_width=1, text_color="#E03B3B", hover_color="#4a1515", command=self.delete_template, state="disabled")
        self.btn_delete.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(controls_frame, text="Template Name:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 2), padx=15, anchor="w")
        self.name_entry = ctk.CTkEntry(controls_frame, placeholder_text="e.g. cozy_desk")
        self.name_entry.pack(fill="x", padx=15, pady=(0, 15))

        self.btn_save = ctk.CTkButton(
            controls_frame, text="💾 Save to Config", font=ctk.CTkFont(weight="bold"), 
            fg_color="#0052cc", hover_color="#0747a6", height=40, command=self.save_template
        )
        self.btn_save.pack(fill="x", padx=15, pady=20)

        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        canvas_frame.grid_columnconfigure(0, weight=1)
        canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", self.on_resize)

    def load_config(self):
        config_path = "config/templates.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    self.templates = json.load(f)
                except json.JSONDecodeError:
                    self.templates = {}
        
        options = ["New Template..."] + list(self.templates.keys())
        self.template_dropdown.configure(values=options)
        self.template_dropdown.set("New Template...")

    def on_template_select(self, choice):
        if choice == "New Template...":
            self.clear_points()
            self.image_path = None
            self.original_image = None
            self.canvas.delete("all")
            self.name_entry.delete(0, 'end')
            self.btn_delete.configure(state="disabled")
        else:
            data = self.templates[choice]
            self.image_path = data["file"]
            if os.path.exists(self.image_path):
                # Using 'with' forces PIL to load into memory and immediately close the file handle
                with Image.open(self.image_path) as img:
                    img.load()
                    self.original_image = img.copy()
                
                self.real_points = data["corners"]
                self.name_entry.delete(0, 'end')
                self.name_entry.insert(0, choice)
                self.btn_delete.configure(state="normal")
                self.draw_image()
            else:
                messagebox.showerror("Error", f"Image file not found at: {self.image_path}")

    def delete_template(self):
        choice = self.template_dropdown.get()
        if choice == "New Template...":
            return
        
        if messagebox.askyesno("Confirm", f"Remove '{choice}' from config?"):
            del self.templates[choice]
            with open("config/templates.json", "w", encoding="utf-8") as f:
                json.dump(self.templates, f, indent=4)
            
            self.load_config()
            self.on_template_select("New Template...")

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.template_dropdown.set("New Template...")
            self.btn_delete.configure(state="disabled")
            self.name_entry.delete(0, 'end')
            self.image_path = file_path
            
            # Using 'with' forces PIL to load into memory and immediately close the file handle
            with Image.open(file_path) as img:
                img.load()
                self.original_image = img.copy()
                
            self.clear_points()
            self.draw_image()

    def on_resize(self, event):
        if self.original_image:
            self.draw_image()

    def draw_image(self):
        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w < 10 or canvas_h < 10:
            return

        img_w, img_h = self.original_image.size
        self.scale_factor = min(canvas_w / img_w, canvas_h / img_h)
        
        new_w = max(1, int(img_w * self.scale_factor))
        new_h = max(1, int(img_h * self.scale_factor))

        self.display_image = self.original_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)

        self.x_offset = (canvas_w - new_w) // 2
        self.y_offset = (canvas_h - new_h) // 2

        self.canvas.create_image(self.x_offset, self.y_offset, anchor="nw", image=self.tk_image)
        
        # Translate real points back to canvas coordinates
        self.points = []
        for rx, ry in self.real_points:
            cx = rx * self.scale_factor + self.x_offset
            cy = ry * self.scale_factor + self.y_offset
            self.points.append((cx, cy))

        self.redraw_points()

    def on_canvas_click(self, event):
        if not self.original_image or len(self.points) >= 4:
            return

        img_w, img_h = self.display_image.size
        if not (self.x_offset <= event.x <= self.x_offset + img_w and self.y_offset <= event.y <= self.y_offset + img_h):
            return

        real_x = int((event.x - self.x_offset) / self.scale_factor)
        real_y = int((event.y - self.y_offset) / self.scale_factor)

        self.points.append((event.x, event.y))
        self.real_points.append([real_x, real_y])
        
        self.redraw_points()

    def redraw_points(self):
        self.canvas.delete("overlay")
        r = 5
        for i, (cx, cy) in enumerate(self.points):
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#36b37e", outline="white", width=2, tags="overlay")
            self.canvas.create_text(cx + 12, cy - 12, text=str(i + 1), fill="white", font=("Arial", 12, "bold"), tags="overlay")

            if i > 0:
                px, py = self.points[i - 1]
                self.canvas.create_line(px, py, cx, cy, fill="#36b37e", width=2, dash=(4, 2), tags="overlay")
        
        if len(self.points) == 4:
            px, py = self.points[3]
            cx, cy = self.points[0]
            self.canvas.create_line(px, py, cx, cy, fill="#36b37e", width=2, dash=(4, 2), tags="overlay")

    def clear_points(self):
        self.points = []
        self.real_points = []
        if self.original_image:
            self.draw_image()

    def save_template(self):
        if len(self.real_points) != 4:
            messagebox.showwarning("Incomplete", "Please select exactly 4 corners on the image.")
            return
            
        template_name = self.name_entry.get().strip().lower().replace(" ", "_")
        if not template_name:
            messagebox.showwarning("Missing Name", "Please enter a template name.")
            return

        os.makedirs("config", exist_ok=True)
        os.makedirs("templates", exist_ok=True)

        ext = os.path.splitext(self.image_path)[1]
        dest_filename = f"{template_name}{ext}"
        dest_path = os.path.join("templates", dest_filename)
        
        # Because we safely closed the file using the context manager, we can now overwrite it if needed
        try:
            shutil.copy2(self.image_path, dest_path)
        except shutil.SameFileError:
            pass

        self.templates[template_name] = {
            "file": f"templates/{dest_filename}",
            "corners": self.real_points
        }

        with open("config/templates.json", "w", encoding="utf-8") as f:
            json.dump(self.templates, f, indent=4)

        messagebox.showinfo("Success", f"Template '{template_name}' successfully mapped and saved!")
        self.load_config()
        self.on_template_select(template_name)