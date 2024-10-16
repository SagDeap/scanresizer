import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from ttkthemes import ThemedTk
from psd_tools import PSDImage
import os
import threading
import datetime
import configparser

CONFIG_FILE = "image_resizer_config.ini"

def is_valid_image_file(filename):
    return any(filename.lower().endswith(ext) for ext in ['.psd', '.png', '.jpg'])

def draw_done(canvas):
    canvas.delete("all")
    img_path = "done.png"  
    img = Image.open(img_path)

    
    target_size = (60, 60)

  
    img = img.resize(target_size, Image.LANCZOS)
    img = ImageTk.PhotoImage(img)

    
    center_x = canvas.winfo_reqwidth() // 2
    center_y = canvas.winfo_reqheight() // 2

   
    canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=img)
    canvas.image = img

def resize_image(img, new_width):
    width_percent = (new_width / float(img.size[0]))
    new_height = int(round(float(img.size[1]) * float(width_percent)))
    return img.resize((new_width, new_height), Image.LANCZOS)

def resize_images(input_folder, output_folder, new_width, progress_var, log, root, canvas):
    images = [file for file in os.listdir(input_folder) if is_valid_image_file(file)]
    total_images = len(images)

    if total_images == 0:
        log.config(text="Нет изображений для обработки.")
        return

    log.config(text="Processing...")  
    root.update_idletasks()  

    def update_progress(i):
        progress_var.set(i / total_images * 100)
        log.config(text=f"Обработано {i} из {total_images} изображений.")
        root.update_idletasks()

    for i, image_file in enumerate(images, 1):
        input_path = os.path.join(input_folder, image_file)
        output_file, output_format = os.path.splitext(image_file)
        output_format = 'PNG' if output_format.lower() == '.psd' else output_format.upper()[1:]
        output_path = os.path.join(output_folder, f"{output_file}.{output_format.lower()}")

        if image_file.lower().endswith('.psd'):
            psd_image = PSDImage.open(input_path)
            psd_image.compose().save(output_path, 'PNG')
            img = Image.open(output_path)  
        else:
            img = Image.open(input_path)

        img_resized = resize_image(img, new_width)
        img_resized.save(output_path, format=output_format)

        if i % 10 == 0 or i == total_images:
            update_progress(i)
            root.after(1, update_progress, i)  

    log.config(text="Изменение размера изображений завершено.")
    root.after(1, lambda: draw_done(canvas))  

def start_resizing(input_folder, output_folder, new_width, progress_var, log, root, canvas):
    if not input_folder or not output_folder or not new_width:
        log.config(text="Ошибка: убедитесь, что все поля заполнены.")
        return
    try:
        new_width = int(new_width)
    except ValueError:
        log.config(text="Ошибка: ширина должна быть числом.")
        return

    session_folder = os.path.join(output_folder, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M'))
    os.makedirs(session_folder, exist_ok=True)

    config['Settings'] = {
        'InputFolder': input_folder,
        'OutputFolder': output_folder,
        'NewWidth': str(new_width)
    }

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

    threading.Thread(target=resize_images, args=(input_folder, session_folder, new_width, progress_var, log, root, canvas)).start()

def select_folder(entry):
    folder_selected = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, folder_selected)

def select_folder_with_files(entry, tree):
    folder_selected = filedialog.askdirectory()
    entry.delete(0, tk.END)
    entry.insert(0, folder_selected)

    tree.delete(*tree.get_children())
    for item in os.listdir(folder_selected):
        tree.insert("", "end", values=(item,))

def load_settings(config, entry_input, entry_output, entry_width):
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        input_folder = config.get('Settings', 'InputFolder', fallback='')
        output_folder = config.get('Settings', 'OutputFolder', fallback='')
        new_width = config.get('Settings', 'NewWidth', fallback='')

        
        entry_input.delete(0, tk.END)
        entry_input.insert(0, input_folder)

        entry_output.delete(0, tk.END)
        entry_output.insert(0, output_folder)

        entry_width.delete(0, tk.END)
        entry_width.insert(0, new_width)

def init_gui():
    root = ThemedTk(theme="arc")
    root.title("Изменение размера изображений by Yukich")
    root.resizable(False, False)

    input_tree = ttk.Treeview(root, columns=("Files",))
    input_tree.heading("#1", text="Файлы и папки")
    input_tree.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    input_folder_entry = ttk.Entry(root, width=50)
    input_folder_entry.grid(row=0, column=1, padx=10, pady=10)
    ttk.Button(root, text="Выбрать папку input", command=lambda: select_folder_with_files(input_folder_entry, input_tree)).grid(row=0, column=0, padx=10, pady=10)

    output_folder_entry = ttk.Entry(root, width=50)
    output_folder_entry.grid(row=1, column=1, padx=10, pady=10)
    ttk.Button(root, text="Выбрать папку output", command=lambda: select_folder(output_folder_entry)).grid(row=1, column=0, padx=10, pady=10)

    width_entry = ttk.Entry(root, width=20)
    width_entry.grid(row=2, column=1, padx=10, pady=10)
    ttk.Label(root, text="Желаемая ширина:").grid(row=2, column=0)

    load_settings(config, input_folder_entry, output_folder_entry, width_entry)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, length=400, variable=progress_var)
    progress_bar.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    canvas = tk.Canvas(root, width=60, height=60, bg="white")  
    canvas.grid(row=3, column=2, padx=10, pady=10)

    log_label = ttk.Label(root, text="")
    log_label.grid(row=4, column=0, columnspan=2)

    ttk.Button(root, text="Начать изменение размера", command=lambda: start_resizing(
        input_folder_entry.get(), output_folder_entry.get(), width_entry.get(), progress_var, log_label, root, canvas)).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    
    label = ttk.Label(root, text="Ashbysld <3", font=("Arial", 7), foreground="#808080")
    label.place(relx=1, rely=1, anchor='se')

    root.mainloop()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    init_gui_thread = threading.Thread(target=init_gui)
    init_gui_thread.start()
