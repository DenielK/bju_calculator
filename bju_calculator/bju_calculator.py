import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk as pilt
from datetime import datetime
import os

# ---------- ДАННЫЕ ----------
PRODUCTS_FILE = "products.txt"
MEALS_FILE = "meals.txt"

# ---------- УТИЛИТЫ ----------
def set_background(root, image_path):
    image = Image.open(image_path)
    image = image.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
    bg_image = pilt.PhotoImage(image)

    bg_label = tk.Label(root, image=bg_image)
    bg_label.image = bg_image  # чтобы не удалялся сборщиком мусора
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    return bg_label


def load_product_data(filepath=PRODUCTS_FILE):
    data = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 4:
                    name = parts[0].strip().lower()
                    protein = float(parts[1])
                    fat = float(parts[2])
                    carb = float(parts[3])
                    data[name] = (protein, fat, carb)
    except FileNotFoundError:
        pass
    return data

def get_bju_for_product(data, name):
    return data.get(name)

def save_meal_to_file(entries, protein, fat, carb, filepath=MEALS_FILE):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        for name_var, weight_var in entries:
            name = name_var.get().strip()
            weight = weight_var.get().strip()
            f.write(f"{name},{weight} г\n")
        f.write(f"Итого: Б: {protein:.2f} Ж: {fat:.2f} У: {carb:.2f}\n\n")

def add_product_to_file(name, protein, fat, carb, filepath=PRODUCTS_FILE):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{name},{protein},{fat},{carb}\n")

# ---------- ИНТЕРФЕЙСЫ ----------
def create_welcome_page(root):
    for widget in root.winfo_children():
        widget.destroy()

    ttk.Label(root, text="Калькулятор употребления БЖУ", font=("Arial", 14)).pack(pady=20)
    ttk.Button(root, text="📄 Просмотр продуктов", command=lambda: show_product_list(root)).pack(pady=10)
    ttk.Button(root, text="🍽 Добавить трапезу", command=lambda: add_meal_page(root)).pack(pady=10)
    ttk.Button(root, text="🕓 История трапез", command=lambda: show_meal_history(root)).pack(pady=10)
    ttk.Button(root, text="➕ Добавить продукт", command=lambda: add_product_page(root)).pack(pady=10)

def show_product_list(root):
    for widget in root.winfo_children():
        widget.destroy()

    ttk.Label(root, text="Список продуктов", font=("Arial", 14)).pack(pady=10)
    text_box = tk.Text(root, width=60, height=15)
    text_box.pack(pady=10)

    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            text_box.insert("1.0", f.read())
    except FileNotFoundError:
        text_box.insert("1.0", "Файл с продуктами не найден.")

    ttk.Button(root, text="Назад", command=lambda: create_welcome_page(root)).pack(pady=10)

def show_meal_history(root):
    for widget in root.winfo_children():
        widget.destroy()

    ttk.Label(root, text="История трапез", font=("Arial", 14)).pack(pady=10)
    text_box = tk.Text(root, width=60, height=20)
    text_box.pack(pady=10)

    try:
        with open(MEALS_FILE, "r", encoding="utf-8") as f:
            text_box.insert("1.0", f.read())
    except FileNotFoundError:
        text_box.insert("1.0", "История пока пуста.")

    ttk.Button(root, text="Назад", command=lambda: create_welcome_page(root)).pack(pady=10)

def add_meal_page(root):
    for widget in root.winfo_children():
        widget.destroy()

    ttk.Label(root, text="Добавление трапезы", font=("Arial", 14)).pack(pady=10)

    product_data = load_product_data()
    product_names = sorted(product_data.keys())

    frame = ttk.Frame(root)
    frame.pack(pady=5)
    entries = []

    def add_input_row():
        row_frame = ttk.Frame(frame)
        row_frame.pack(pady=2)

        name_var = tk.StringVar()
        weight_var = tk.StringVar()

        combo = ttk.Combobox(row_frame, textvariable=name_var, values=product_names, width=25)
        combo.pack(side="left", padx=5)
        ttk.Entry(row_frame, textvariable=weight_var, width=10).pack(side="left", padx=5)
        ttk.Label(row_frame, text="грамм").pack(side="left")

        entries.append((name_var, weight_var))

    # Добавляем только одну строку по умолчанию
    add_input_row()

    ttk.Button(root, text="Добавить ещё продукт", command=add_input_row).pack(pady=5)

    def calculate_bju():
        total_protein = total_fat = total_carb = 0
        has_valid = False

        for name_var, weight_var in entries:
            name = name_var.get().strip().lower()
            weight_str = weight_var.get().strip()

            if not name or not weight_str:
                continue  # пропускаем пустые строки

            try:
                weight = float(weight_str)
            except ValueError:
                messagebox.showerror("Ошибка", f"Некорректный вес у продукта '{name}'")
                return

            bju = get_bju_for_product(product_data, name)
            if bju:
                protein, fat, carb = bju
                factor = weight / 100
                total_protein += protein * factor
                total_fat += fat * factor
                total_carb += carb * factor
                has_valid = True
            else:
                messagebox.showwarning("Не найдено", f"Продукт '{name}' не найден в базе.")
                return

        if not has_valid:
            messagebox.showwarning("Внимание", "Введите хотя бы один продукт.")
            return

        result_text = f"Суммарно за трапезу:\nБелки: {total_protein:.2f} г\nЖиры: {total_fat:.2f} г\nУглеводы: {total_carb:.2f} г"
        messagebox.showinfo("Результат", result_text)
        save_meal_to_file(entries, total_protein, total_fat, total_carb)

    ttk.Button(root, text="Рассчитать БЖУ", command=calculate_bju).pack(pady=10)
    ttk.Button(root, text="Назад", command=lambda: create_welcome_page(root)).pack(pady=5)

def add_product_page(root):
    for widget in root.winfo_children():
        widget.destroy()

    ttk.Label(root, text="Добавить продукт", font=("Arial", 14)).pack(pady=10)

    name_var = tk.StringVar()
    protein_var = tk.StringVar()
    fat_var = tk.StringVar()
    carb_var = tk.StringVar()

    ttk.Entry(root, textvariable=name_var, width=30).pack(pady=5)
    ttk.Label(root, text="Белки (на 100 г)").pack()
    ttk.Entry(root, textvariable=protein_var, width=20).pack()
    ttk.Label(root, text="Жиры (на 100 г)").pack()
    ttk.Entry(root, textvariable=fat_var, width=20).pack()
    ttk.Label(root, text="Углеводы (на 100 г)").pack()
    ttk.Entry(root, textvariable=carb_var, width=20).pack()

    def save_product():
        name = name_var.get().strip().lower()
        try:
            protein = float(protein_var.get().strip())
            fat = float(fat_var.get().strip())
            carb = float(carb_var.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числовые значения для Б/Ж/У.")
            return

        if not name:
            messagebox.showerror("Ошибка", "Название продукта не может быть пустым.")
            return

        add_product_to_file(name, protein, fat, carb)
        messagebox.showinfo("Успех", f"Продукт '{name}' добавлен.")
        create_welcome_page(root)

    ttk.Button(root, text="Сохранить", command=save_product).pack(pady=10)
    ttk.Button(root, text="Назад", command=lambda: create_welcome_page(root)).pack(pady=5)

# ---------- ЗАПУСК ----------
def main():
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            f.write("яблоко,0.3,0.2,14\nкуриная грудка,31,3.6,0\nгречка,12.6,3.3,68\n")

    root = tk.Tk()
    root.title("Калькулятор БЖУ")
    root.geometry("500x600")
    set_background(root, "food.png")
    create_welcome_page(root)
    root.mainloop()

if __name__ == "__main__":
    main()