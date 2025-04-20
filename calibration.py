import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import json
from PIL import Image, ImageTk

class ColorCalibrationApp:
    def __init__(self, master):
        try:
            master.state('zoomed')  # Windows
        except:
            master.attributes('-zoomed', True)  # Linux/Mac

        self.master = master
        master.title("Color Mask Calibration App")

        self.original_image = None
        self.hsv_value = tk.StringVar(master, value="H: -, S: -, V: -")
        self.h_tolerance = tk.IntVar(master, value=50)
        self.s_tolerance = tk.IntVar(master, value=40)
        self.v_tolerance = tk.IntVar(master, value=30)
        self.mask_values = None

        # Configure grid layout
        master.grid_columnconfigure(0, weight=9)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=8)

        # Original Picture
        self.original_image_frame = tk.Frame(master)
        self.original_image_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

        self.original_label = tk.Label(self.original_image_frame, text="Original Picture")
        self.original_label.pack()
        self.original_canvas = tk.Canvas(self.original_image_frame)
        self.original_canvas.pack(expand=True, fill=tk.BOTH)
        self.original_canvas.bind("<Button-1>", self.pick_color)

        # Binary Image
        self.binary_image_frame = tk.Frame(master)
        self.binary_image_frame.grid(row=0, column=1, sticky="new")

        self.binary_label = tk.Label(self.binary_image_frame, text="Binary Image (Mask)")
        self.binary_label.pack()
        self.binary_canvas = tk.Canvas(self.binary_image_frame, bg="#d3d3d3", highlightthickness=0)
        self.binary_canvas.pack(expand=True, fill=tk.BOTH)
        self.binary_canvas.bind("<Button-1>", self.open_binary_image_in_viewer)

        # Right side controls (sliders)
        self.right_frame = tk.Frame(master)
        self.right_frame.grid(row=1, column=1, sticky="nse")

        tk.Label(self.right_frame, text="HSV value:").pack()
        self.hsv_display_label = tk.Label(self.right_frame, textvariable=self.hsv_value)
        self.hsv_display_label.pack()
        # Manual HSV input
        tk.Label(self.right_frame, text="Manual HSV:").pack(pady=(10, 0))

        hsv_manual_frame = tk.Frame(self.right_frame)
        hsv_manual_frame.pack()

        tk.Label(hsv_manual_frame, text="H:").grid(row=0, column=0)
        self.h_manual = tk.Entry(hsv_manual_frame, width=4)
        self.h_manual.grid(row=0, column=1)

        tk.Label(hsv_manual_frame, text="S:").grid(row=0, column=2)
        self.s_manual = tk.Entry(hsv_manual_frame, width=4)
        self.s_manual.grid(row=0, column=3)

        tk.Label(hsv_manual_frame, text="V:").grid(row=0, column=4)
        self.v_manual = tk.Entry(hsv_manual_frame, width=4)
        self.v_manual.grid(row=0, column=5)

        set_manual_button = tk.Button(self.right_frame, text="Set HSV manually", command=self.set_manual_hsv)
        set_manual_button.pack(pady=5, fill="x")
        # Tolerance H
        tk.Label(self.right_frame, text="Tolerance H:").pack()
        h_frame = tk.Frame(self.right_frame)
        h_frame.pack()
        self.h_scale = tk.Scale(h_frame, from_=0, to=180, orient=tk.HORIZONTAL, variable=self.h_tolerance, command=self.update_mask_from_sliders)
        self.h_scale.pack(side=tk.LEFT)
        self.h_entry = tk.Entry(h_frame, width=4)
        self.h_entry.pack(side=tk.LEFT, padx=5)
        self.h_entry.insert(0, str(self.h_tolerance.get()))
        self.h_entry.bind("<Return>", lambda e: self.update_tolerance_from_entry('h'))

        # Tolerance S
        tk.Label(self.right_frame, text="Tolerance S:").pack()
        s_frame = tk.Frame(self.right_frame)
        s_frame.pack()
        self.s_scale = tk.Scale(s_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.s_tolerance, command=self.update_mask_from_sliders)
        self.s_scale.pack(side=tk.LEFT)
        self.s_entry = tk.Entry(s_frame, width=4)
        self.s_entry.pack(side=tk.LEFT, padx=5)
        self.s_entry.insert(0, str(self.s_tolerance.get()))
        self.s_entry.bind("<Return>", lambda e: self.update_tolerance_from_entry('s'))

        # Tolerance V
        tk.Label(self.right_frame, text="Tolerance V:").pack()
        v_frame = tk.Frame(self.right_frame)
        v_frame.pack()
        self.v_scale = tk.Scale(v_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.v_tolerance, command=self.update_mask_from_sliders)
        self.v_scale.pack(side=tk.LEFT)
        self.v_entry = tk.Entry(v_frame, width=4)
        self.v_entry.pack(side=tk.LEFT, padx=5)
        self.v_entry.insert(0, str(self.v_tolerance.get()))
        self.v_entry.bind("<Return>", lambda e: self.update_tolerance_from_entry('v'))

        mask_menu = tk.LabelFrame(self.right_frame, text="Mask")
        mask_menu.pack(pady=10, fill="x")

        save_button = tk.Button(mask_menu, text="Save Mask", command=self.save_mask)
        save_button.pack(fill="x")

        load_button = tk.Button(mask_menu, text="Load Mask", command=self.load_mask)
        load_button.pack(fill="x")

        menubar = tk.Menu(master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="open image", command=self.load_image)
        file_menu.add_separator()
        file_menu.add_command(label="quit", command=master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        master.config(menu=menubar)
        master.bind("<Configure>", self.on_resize)

    def update_tolerance_from_entry(self, channel):
        try:
            if channel == 'h':
                value = int(self.h_entry.get())
                if 0 <= value <= 180:
                    self.h_tolerance.set(value)
            elif channel == 's':
                value = int(self.s_entry.get())
                if 0 <= value <= 255:
                    self.s_tolerance.set(value)
            elif channel == 'v':
                value = int(self.v_entry.get())
                if 0 <= value <= 255:
                    self.v_tolerance.set(value)
            self.update_binary_mask()
        except ValueError:
            pass  # ignore errors

    def on_resize(self, event):
        if self.original_image is not None:
            self.display_original_image()
            self.update_binary_mask()

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                height, width = self.original_image.shape[:2]
                self.original_canvas.config(width=width, height=height)
                self.binary_canvas.config(width=int(width * 0.1 / 0.9), height=int(height * 0.1 / 0.9)) # Adjust binary canvas size
                self.display_original_image()
                self.update_binary_mask()

    def display_original_image(self):
        if self.original_image is not None:
            canvas_width = self.original_canvas.winfo_width()
            canvas_height = self.original_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                img_height, img_width = self.original_image.shape[:2]
                scale = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)

                # Offset to center image if canvas is bigger
                self.img_offset_x = (canvas_width - new_width) // 2
                self.img_offset_y = (canvas_height - new_height) // 2
                self.img_scale = scale

                resized = cv2.resize(self.original_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                self.original_image_tk = self.convert_cv2_to_tkinter(resized)
                self.original_canvas.delete("all")
                self.original_canvas.create_image(self.img_offset_x, self.img_offset_y, anchor=tk.NW, image=self.original_image_tk)


    def pick_color(self, event):
        if self.original_image is not None and hasattr(self, 'img_scale'):
            x = int((event.x - self.img_offset_x) / self.img_scale)
            y = int((event.y - self.img_offset_y) / self.img_scale)
            h, w = self.original_image.shape[:2]
            if 0 <= x < w and 0 <= y < h:
                b, g, r = self.original_image[y, x]
                hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
                self.hsv_value.set(f"H: {hsv[0]}, S: {hsv[1]}, V: {hsv[2]}")
                self.update_binary_mask()


    def update_mask_from_sliders(self, event=None):
        # update text field values
        self.h_entry.delete(0, tk.END)
        self.h_entry.insert(0, str(self.h_tolerance.get()))

        self.s_entry.delete(0, tk.END)
        self.s_entry.insert(0, str(self.s_tolerance.get()))

        self.v_entry.delete(0, tk.END)
        self.v_entry.insert(0, str(self.v_tolerance.get()))

        self.update_binary_mask()

    def update_binary_mask(self):
        if self.original_image is not None:
            try:
                hsv_str = self.hsv_value.get()
                h = int(hsv_str.split(',')[0].split(':')[1].strip())
                s = int(hsv_str.split(',')[1].split(':')[1].strip())
                v = int(hsv_str.split(',')[2].split(':')[1].strip())
                h_tol = self.h_tolerance.get()
                s_tol = self.s_tolerance.get()
                v_tol = self.v_tolerance.get()

                lower_bound = np.array([max(0, h - h_tol), max(0, s - s_tol), max(0, v - v_tol)])
                upper_bound = np.array([min(180, h + h_tol), min(255, s + s_tol), min(255, v + v_tol)])

                hsv_img = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv_img, lower_bound, upper_bound)
                binary_image = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                canvas_width = self.binary_canvas.winfo_width()
                canvas_height = self.binary_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    img_resized = self.resize_image(binary_image, canvas_width, canvas_height)
                    self.binary_image_tk = self.convert_cv2_to_tkinter(img_resized)
                    self.binary_canvas.create_image(0, 0, anchor=tk.NW, image=self.binary_image_tk)

            except ValueError:
                pass

    def save_mask(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
        if file_path:
            try:
                hsv_str = self.hsv_value.get()
                h = int(hsv_str.split(',')[0].split(':')[1].strip())
                s = int(hsv_str.split(',')[1].split(':')[1].strip())
                v = int(hsv_str.split(',')[2].split(':')[1].strip())
                h_tol = self.h_tolerance.get()
                s_tol = self.s_tolerance.get()
                v_tol = self.v_tolerance.get()

                lower_bound = [max(0, h), max(0, s), max(0, v)]
                upper_bound = [min(180, h_tol), min(255, s_tol), min(255, v_tol)]

                with open(file_path, 'w') as f:
                    f.write(f"{lower_bound[0]},{lower_bound[1]},{lower_bound[2]}\n")
                    f.write(f"{upper_bound[0]},{upper_bound[1]},{upper_bound[2]}\n")

                messagebox.showinfo("Success", "The mask has been saved.")
            except ValueError:
                messagebox.showerror("Error", "No color selected yet.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while saving the mask: {e}")

    def load_mask(self):
        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    if len(lines) == 2:
                        lower_str = lines[0].strip().split(',')
                        upper_str = lines[1].strip().split(',')
                        if len(lower_str) == 3 and len(upper_str) == 3:
                            lower_hsv = [int(x) for x in lower_str]
                            upper_hsv = [int(x) for x in upper_str]
                            self.hsv_value.set(f"H: {lower_hsv[0]}, S: {lower_hsv[1]}, V: {lower_hsv[2]}")
                            self.h_tolerance.set(upper_hsv[0])
                            self.s_tolerance.set(upper_hsv[1])
                            self.v_tolerance.set(upper_hsv[2])
                            self.update_binary_mask()
                            messagebox.showinfo("Success", "The mask has been loaded.")
                        else:
                            messagebox.showerror("Error", "Nieprawidłowy format wartości HSV.")
                    else:
                        messagebox.showerror("Error", "Invalid HSV value format.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while loading the mask: {e}")

    def resize_image(self, img, target_width, target_height):
        if img is not None:
            img_height, img_width = img.shape[:2]

            # Set maximum allowed width and height based on the window size
            max_width = target_width
            max_height = target_height

            # Calculate the scaling factors for width and height
            scale_w = max_width / img_width
            scale_h = max_height / img_height

            # Keep the aspect ratio by taking the minimum of both scaling factors
            scale = min(scale_w, scale_h, 1.0)

            # Compute the new dimensions while preserving aspect ratio
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            # Resize image with the calculated dimensions
            return cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return None


    def convert_cv2_to_tkinter(self, img):
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            return ImageTk.PhotoImage(image=img_pil)
        return None
    def set_manual_hsv(self):
        try:
            h = int(self.h_manual.get())
            s = int(self.s_manual.get())
            v = int(self.v_manual.get())
            if 0 <= h <= 180 and 0 <= s <= 255 and 0 <= v <= 255:
                self.hsv_value.set(f"H: {h}, S: {s}, V: {v}")
                self.update_binary_mask()
            else:
                messagebox.showwarning("Incorrect values", "H must be 0-180, S and V must be 0-255.")
        except ValueError:
            messagebox.showwarning("Error", "Enter valid integers for H, S, and V.")


    def open_binary_image_in_viewer(self, event=None):
        if self.original_image is None:
            return

        def update_preview(*args):
            h = int(h_slider.get())
            s = int(s_slider.get())
            v = int(v_slider.get())
            h_tol = int(h_tol_slider.get())
            s_tol = int(s_tol_slider.get())
            v_tol = int(v_tol_slider.get())

            lower = np.array([max(0, h - h_tol), max(0, s - s_tol), max(0, v - v_tol)])
            upper = np.array([min(180, h + h_tol), min(255, s + s_tol), min(255, v + v_tol)])

            hsv_img = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_img, lower, upper)
            mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)

            nonlocal current_mask_rgb
            current_mask_rgb = mask_rgb

            resize_image_to_fit()

        def resize_image_to_fit():
            if current_mask_rgb is None:
                return

            frame_width = image_frame.winfo_width()
            frame_height = image_frame.winfo_height()
            if frame_width < 10 or frame_height < 10:
                return

            img_height, img_width = current_mask_rgb.shape[:2]
            aspect_ratio = img_width / img_height

            # Calculate dimensions to fit the window without changing proportions
            if frame_width / frame_height > aspect_ratio:
                # Window is wider than image - adjust by height
                new_height = frame_height
                new_width = int(new_height * aspect_ratio)
            else:
                # The window is narrower or perfectly matched - adjust by width
                new_width = frame_width
                new_height = int(new_width / aspect_ratio)

            resized = cv2.resize(current_mask_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
            img_pil = Image.fromarray(resized)
            mask_tk = ImageTk.PhotoImage(img_pil)

            mask_label.configure(image=mask_tk)
            mask_label.image = mask_tk

        def on_resize(event):
            resize_image_to_fit()

        # === INTERFEJS ===
        viewer = tk.Toplevel(self.master)
        viewer.title("Interactive Mask Viewer")
        viewer.geometry("1000x700")

        viewer.grid_rowconfigure(0, weight=1)
        viewer.grid_columnconfigure(1, weight=1)

        controls_frame = tk.Frame(viewer)
        controls_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)

        hsv_str = self.hsv_value.get()
        h = int(hsv_str.split(',')[0].split(':')[1].strip())
        s = int(hsv_str.split(',')[1].split(':')[1].strip())
        v = int(hsv_str.split(',')[2].split(':')[1].strip())

        h_slider = tk.Scale(controls_frame, from_=0, to=180, label="H", orient=tk.HORIZONTAL)
        h_slider.set(h)
        h_slider.pack(fill="x")

        s_slider = tk.Scale(controls_frame, from_=0, to=255, label="S", orient=tk.HORIZONTAL)
        s_slider.set(s)
        s_slider.pack(fill="x")

        v_slider = tk.Scale(controls_frame, from_=0, to=255, label="V", orient=tk.HORIZONTAL)
        v_slider.set(v)
        v_slider.pack(fill="x")

        h_tol_slider = tk.Scale(controls_frame, from_=0, to=180, label="H tol", orient=tk.HORIZONTAL)
        h_tol_slider.set(self.h_tolerance.get())
        h_tol_slider.pack(fill="x")

        s_tol_slider = tk.Scale(controls_frame, from_=0, to=255, label="S tol", orient=tk.HORIZONTAL)
        s_tol_slider.set(self.s_tolerance.get())
        s_tol_slider.pack(fill="x")

        v_tol_slider = tk.Scale(controls_frame, from_=0, to=255, label="V tol", orient=tk.HORIZONTAL)
        v_tol_slider.set(self.v_tolerance.get())
        v_tol_slider.pack(fill="x")
        tk.Label(controls_frame, text="Zapis / Wczytaj maskę:").pack(pady=(10, 0))
        def save_mask_from_viewer():
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
            if file_path:
                try:
                    h_val = h_slider.get()
                    s_val = s_slider.get()
                    v_val = v_slider.get()
                    h_tol_val = h_tol_slider.get()
                    s_tol_val = s_tol_slider.get()
                    v_tol_val = v_tol_slider.get()

                    lower_bound = [max(0, h_val), max(0, s_val), max(0, v_val)]
                    upper_bound = [min(180, h_tol_val), min(255, s_tol_val), min(255, v_tol_val)]

                    with open(file_path, 'w') as f:
                        f.write(f"{lower_bound[0]},{lower_bound[1]},{lower_bound[2]}\n")
                        f.write(f"{upper_bound[0]},{upper_bound[1]},{upper_bound[2]}\n")
                    
                    messagebox.showinfo("Success", "The mask has been saved.")
                except Exception as e:
                    messagebox.showerror("Error", f"There was a problem saving the mask: {e}")

        def load_mask_into_viewer():
            file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
            if file_path:
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) == 2:
                            lower = list(map(int, lines[0].strip().split(',')))
                            upper = list(map(int, lines[1].strip().split(',')))

                            h_slider.set(lower[0])
                            s_slider.set(lower[1])
                            v_slider.set(lower[2])

                            h_tol_slider.set(upper[0])
                            s_tol_slider.set(upper[1])
                            v_tol_slider.set(upper[2])

                            update_preview()
                            messagebox.showinfo("Success", "The mask has been loaded.")
                        else:
                            messagebox.showerror("Error", "Invalid mask file format.")
                except Exception as e:
                    messagebox.showerror("Error", f"There was a problem loading the mask: {e}")
        tk.Button(controls_frame, text="Save mask", command=save_mask_from_viewer).pack(fill="x")
        tk.Button(controls_frame, text="Load mask", command=load_mask_into_viewer).pack(fill="x")

        for slider in [h_slider, s_slider, v_slider, h_tol_slider, s_tol_slider, v_tol_slider]:
            slider.bind("<B1-Motion>", update_preview)
            slider.bind("<ButtonRelease-1>", update_preview)

        image_frame = tk.Frame(viewer, bg="black")
        image_frame.grid(row=0, column=1, sticky="nsew")
        image_frame.bind("<Configure>", on_resize)

        mask_label = tk.Label(image_frame, bg="black")
        mask_label.pack(expand=True)

        current_mask_rgb = None

        update_preview()



if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.state('zoomed')
    except:
        root.attributes('-zoomed', True)
    app = ColorCalibrationApp(root)
    root.mainloop()