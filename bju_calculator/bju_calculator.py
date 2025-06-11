import tkinter as tk
from tkinter import ttk, messagebox, Entry, Text, Button, Label
from PIL import Image, ImageTk
from datetime import datetime
import os
import smtplib  # Для отправки email через SMTP
import ssl  # Для безопасного соединения
from email.message import EmailMessage  # Для создания email-сообщения

# ---------- УПРАВЛЕНИЕ ДАННЫМИ ----------
PRODUCTS_FILE = "products.txt"  # Файл для хранения данных о пищевой ценности продуктов
MEALS_FILE = "meals.txt"  # Файл для хранения истории всех трапез

# ---------- УПРАВЛЕНИЕ ФОНОМ ----------
def set_background(parent, image_path):
    """
    Устанавливает фоновое изображение для заданного виджета Tkinter.

    Аргументы:
        parent: Виджет Tkinter, для которого устанавливается фон (например, main_frame).
        image_path: Путь к файлу фонового изображения.

    Возвращает:
        Виджет tk.Label, содержащий фоновое изображение.
    """
    image = Image.open(image_path)
    image = image.resize((500, 600))  # Изменяем размер изображения под окно
    bg_image = ImageTk.PhotoImage(image)

    bg_label = tk.Label(parent, image=bg_image)
    bg_label.image = bg_image  # Сохраняем ссылку на изображение, чтобы избежать сборки мусора
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    return bg_label

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def load_product_data(filepath=PRODUCTS_FILE):
    """
    Загружает данные о продуктах (название, белки, жиры, углеводы) из указанного файла.

    Аргументы:
        filepath: Путь к файлу, содержащему данные о продуктах.

    Возвращает:
        Словарь, где ключами являются названия продуктов (в нижнем регистре),
        а значениями - кортежи (белки, жиры, углеводы) на 100 г продукта.
    """
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
        # Если файл не найден, возвращаем пустой словарь
        pass
    return data

def get_bju_for_product(data, name):
    """
    Получает данные о белках, жирах и углеводах для конкретного продукта.

    Аргументы:
        data: Словарь с данными о продуктах (полученный из load_product_data).
        name: Название продукта для поиска (в нижнем регистре).

    Возвращает:
        Кортеж (белки, жиры, углеводы), если продукт найден, иначе None.
    """
    return data.get(name)

def save_meal_to_file(entries, protein, fat, carb, filepath=MEALS_FILE):
    """
    Сохраняет детали завершенной трапезы в файл истории трапез.

    Аргументы:
        entries: Список кортежей (name_var, weight_var) из полей ввода продуктов для трапезы.
        protein: Общее количество белков, рассчитанное для трапезы.
        fat: Общее количество жиров, рассчитанное для трапезы.
        carb: Общее количество углеводов, рассчитанное для трапезы.
        filepath: Путь к файлу, где сохраняется история трапез.

    Возвращает:
        Строку, содержащую отформатированные детали сохраненной трапезы,
        подходящую для отправки по электронной почте.
    """
    meal_record = []
    meal_record.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") # Добавляем текущую дату и время
    for name_var, weight_var in entries:
        name = name_var.get().strip()
        weight = weight_var.get().strip()
        if name and weight:  # Добавляем продукт только если заполнены оба поля
            meal_record.append(f"{name},{weight} г")
    meal_record.append(f"Итого: Б: {protein:.2f} Ж: {fat:.2f} У: {carb:.2f}")
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n".join(meal_record) + "\n\n")  # Записываем трапезу в файл, добавляя двойной перенос строки для разделения
    
    return "\n".join(meal_record) + "\n"  # Возвращаем отформатированное содержимое трапезы

def add_product_to_file(name, protein, fat, carb, filepath=PRODUCTS_FILE):
    """
    Добавляет данные о новом продукте в файл продуктов.

    Аргументы:
        name: Название продукта.
        protein: Содержание белков на 100 г.
        fat: Содержание жиров на 100 г.
        carb: Содержание углеводов на 100 г.
        filepath: Путь к файлу, где хранятся данные о продуктах.
    """
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{name},{protein},{fat},{carb}\n")

# ---------- ФУНКЦИОНАЛ ОТПРАВКИ ПОЧТЫ ----------
def send_email_page(parent, email_content=""):
    """
    Создает новое всплывающее окно Tkinter для отправки электронного письма с информацией о трапезе.

    Аргументы:
        parent: Родительский виджет Tkinter.
        email_content: Предварительно заполненный текст для сообщения электронной почты
                       (например, детали одной трапезы).
    """
    email_window = tk.Toplevel(parent)
    email_window.title("Отправить информацию о трапезе")
    email_window.geometry("550x450")  # Устанавливаем размер окна
    email_window.resizable(False, False)  # Запрещаем изменение размера окна
    email_window.configure(bg="#F0F8FF")  # Устанавливаем светло-голубой фон

    # Цветовая палитра для окна отправки письма
    bg_color_label = "#4682B4"  # Стальной синий для меток
    fg_color_label = "white"
    entry_bg = "#E0FFFF"  # Светло-голубой для полей ввода
    btn_color = "#32CD32"  # Ярко-зеленый для кнопки "Отправить"
    btn_color_close = "#FF6347"  # Томатный для кнопки "Закрыть"
    btn_fg = "white"
    font_large_btn = ("Arial", 14, "bold")  # Увеличенный шрифт для кнопок

    # Метки для полей ввода
    labels_text = ["EMAIL:", "ТЕМА:", "СООБЩЕНИЕ:"]
    for i, text in enumerate(labels_text):
        label = Label(email_window, text=text, bg=bg_color_label, fg=fg_color_label,
                      font=("Arial", 12, "bold"), width=12, anchor="w", relief="flat", bd=2)
        label.grid(row=i*2, column=0, padx=10, pady=(10, 2), sticky="nw")

    # Поля ввода
    email_entry = Entry(email_window, width=50, font=("Arial", 11), bg=entry_bg, relief="solid", bd=1)
    email_entry.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="ew")

    subject_entry = Entry(email_window, width=50, font=("Arial", 11), bg=entry_bg, relief="solid", bd=1)
    subject_entry.grid(row=2, column=1, padx=10, pady=(10, 2), sticky="ew")
    subject_entry.insert(0, "Информация о моей трапезе из Калькулятора БЖУ")  # Тема письма по умолчанию

    message_text_widget = Text(email_window, width=50, height=12, font=("Arial", 11), bg=entry_bg, relief="solid", bd=1)
    message_text_widget.grid(row=4, column=1, padx=10, pady=(10, 10), sticky="nsew")
    message_text_widget.insert("1.0", email_content)  # Заполняем поле сообщения содержимым трапезы

    # Кнопки
    send_btn = Button(email_window, text="ОТПРАВИТЬ ПИСЬМО", bg=btn_color, fg=btn_fg,
                      font=font_large_btn, command=lambda: send_email(email_window, email_entry, subject_entry, message_text_widget))
    send_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="ew")

    close_btn = Button(email_window, text="ЗАКРЫТЬ", bg=btn_color_close, fg=btn_fg,
                       font=font_large_btn, command=email_window.destroy)
    close_btn.grid(row=8, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="ew")

    # Настраиваем сетку, чтобы текстовое поле сообщения и вторая колонка могли растягиваться
    email_window.grid_rowconfigure(4, weight=1)
    email_window.grid_columnconfigure(1, weight=1)

def send_email(email_window, email_entry, subject_entry, message_text_widget):
    """
    Выполняет фактическую отправку электронного письма. Эта функция вызывается при нажатии кнопки "Отправить письмо".

    Аргументы:
        email_window: Всплывающее окно для отправки письма.
        email_entry: Виджет Entry, содержащий адреса получателей.
        subject_entry: Виджет Entry, содержащий тему письма.
        message_text_widget: Виджет Text, содержащий тело письма.
    """
    recipients = email_entry.get().split(",")  # Получаем список получателей, разделенных запятыми
    subject = subject_entry.get()  # Получаем тему письма
    message = message_text_widget.get("1.0", tk.END).strip()  # Получаем содержимое письма

    # Данные SMTP-сервера для Gmail
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "denielkruusman@gmail.com"  # Ваш адрес отправителя (ДОЛЖЕН БЫТЬ ВЕРНЫМ)
    password = "nafm ojez sqpx mgon"  # Ваш пароль приложения Google (ДОЛЖЕН БЫТЬ ВЕРНЫМ)

    # Базовая проверка ввода
    if not recipients[0] or not message:
        messagebox.showerror("Ошибка", "Пожалуйста, введите адрес электронной почты и сообщение!", parent=email_window)
        return

    # Создаем объект EmailMessage
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)

    # Попытка отправить письмо
    try:
        context = ssl.create_default_context()  # Создаем безопасный SSL-контекст
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)  # Переводим соединение на безопасное TLS
            server.login(sender_email, password)  # Входим на SMTP-сервер
            server.send_message(msg)  # Отправляем письмо
        messagebox.showinfo("Информация", "Письмо успешно отправлено!", parent=email_window)
        email_window.destroy()  # Закрываем окно отправки письма после успешной отправки
    except Exception as e:
        messagebox.showerror("Произошла ошибка!", f"Ошибка при отправке письма: {e}", parent=email_window)

# ---------- ИНТЕРФЕЙСЫ ПРИЛОЖЕНИЯ ----------
def create_welcome_page(parent):
    """
    Создает главную страницу приветствия с кнопками навигации.

    Аргументы:
        parent: Основной виджет-фрейм, куда будут помещены элементы страницы приветствия.
    """
    # Удаляем все виджеты из родительского элемента, кроме фонового изображения
    for widget in parent.winfo_children():
        if isinstance(widget, tk.Label) and widget.place_info(): # Проверяем, является ли это фоновым изображением
            continue
        widget.destroy()

    ttk.Label(parent, text="Калькулятор употребления БЖУ", font=("Arial", 14)).pack(pady=20)
    ttk.Button(parent, text="📄 Просмотр продуктов", command=lambda: show_product_list(parent)).pack(pady=10)
    ttk.Button(parent, text="🍽 Добавить трапезу", command=lambda: add_meal_page(parent)).pack(pady=10)
    ttk.Button(parent, text="🕓 История трапез", command=lambda: show_meal_history(parent)).pack(pady=10)
    ttk.Button(parent, text="➕ Добавить продукт", command=lambda: add_product_page(parent)).pack(pady=10)

def show_product_list(parent):
    """
    Отображает список всех продуктов и их пищевую ценность.

    Аргументы:
        parent: Основной виджет-фрейм, куда будут помещены элементы списка продуктов.
    """
    # Удаляем все виджеты из родительского элемента, кроме фонового изображения
    for widget in parent.winfo_children():
        if isinstance(widget, tk.Label) and widget.place_info():
            continue
        widget.destroy()

    ttk.Label(parent, text="Список продуктов", font=("Arial", 14)).pack(pady=10)
    text_box = tk.Text(parent, width=60, height=15)
    text_box.pack(pady=10)

    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            text_box.insert("1.0", f.read())
    except FileNotFoundError:
        text_box.insert("1.0", "Файл с продуктами не найден.")

    ttk.Button(parent, text="Назад", command=lambda: create_welcome_page(parent)).pack(pady=10)

def show_meal_history(parent):
    """
    Отображает историю всех записанных трапез.

    Аргументы:
        parent: Основной виджет-фрейм, куда будут помещены элементы истории трапез.
    """
    # Удаляем все виджеты из родительского элемента, кроме фонового изображения
    for widget in parent.winfo_children():
        if isinstance(widget, tk.Label) and widget.place_info():
            continue
        widget.destroy()

    ttk.Label(parent, text="История трапез", font=("Arial", 14)).pack(pady=10)
    text_box = tk.Text(parent, width=60, height=15)
    text_box.pack(pady=10)

    try:
        with open(MEALS_FILE, "r", encoding="utf-8") as f:
            text_box.insert("1.0", f.read())
    except FileNotFoundError:
        text_box.insert("1.0", "История пока пуста.")
    
    ttk.Button(parent, text="Назад", command=lambda: create_welcome_page(parent)).pack(pady=5)

def add_meal_page(parent):
    """
    Создает интерфейс для добавления новой трапезы, позволяя пользователям вводить продукты и вес,
    рассчитывать БЖУ, сохранять трапезу и отправлять ее детали по электронной почте.

    Аргументы:
        parent: Основной виджет-фрейм, куда будут помещены элементы ввода трапезы.
    """
    # Удаляем все виджеты из родительского элемента, кроме фонового изображения
    for widget in parent.winfo_children():
        if isinstance(widget, tk.Label) and widget.place_info():
            continue
        widget.destroy()

    ttk.Label(parent, text="Добавление трапезы", font=("Arial", 14)).pack(pady=10)

    product_data = load_product_data()
    product_names = sorted(product_data.keys()) # Получаем отсортированный список названий продуктов

    frame = ttk.Frame(parent)
    frame.pack(pady=5)
    entries = [] # Список для хранения пар (StringVar для названия, StringVar для веса)

    def add_input_row():
        """Добавляет новую строку полей ввода (комбобокс для названия продукта и поле для веса) для трапезы."""
        row_frame = ttk.Frame(frame)
        row_frame.pack(pady=2)

        name_var = tk.StringVar()
        weight_var = tk.StringVar()

        combo = ttk.Combobox(row_frame, textvariable=name_var, values=product_names, width=25)
        combo.pack(side="left", padx=5)
        ttk.Entry(row_frame, textvariable=weight_var, width=10).pack(side="left", padx=5)
        ttk.Label(row_frame, text="грамм").pack(side="left")

        entries.append((name_var, weight_var))

    add_input_row() # Добавляем первую строку ввода по умолчанию

    ttk.Button(parent, text="Добавить ещё продукт", command=add_input_row).pack(pady=5)

    def calculate_bju():
        """
        Рассчитывает общее количество белков, жиров и углеводов для введенной трапезы.
        Показывает результат, сохраняет трапезу и активирует/настраивает кнопку отправки письма.
        """
        total_protein = total_fat = total_carb = 0
        has_valid = False # Флаг для проверки наличия хотя бы одного корректного продукта

        for name_var, weight_var in entries:
            name = name_var.get().strip().lower()
            weight_str = weight_var.get().strip()

            # Пропускаем полностью пустые строки, но требуем оба поля, если одно заполнено
            if not name and not weight_str:
                continue
            if not name or not weight_str:
                messagebox.showerror("Ошибка", "Заполните все поля для каждого продукта или удалите пустые строки.")
                return

            try:
                weight = float(weight_str)
            except ValueError:
                messagebox.showerror("Ошибка", f"Некорректный вес у продукта '{name}'")
                return

            bju = get_bju_for_product(product_data, name)
            if bju:
                protein, fat, carb = bju
                factor = weight / 100 # Коэффициент для расчета БЖУ на заданный вес
                total_protein += protein * factor
                total_fat += fat * factor
                total_carb += carb * factor
                has_valid = True
            else:
                messagebox.showwarning("Не найдено", f"Продукт '{name}' не найден в базе. Добавьте его через главное меню.")
                return

        if not has_valid:
            messagebox.showwarning("Внимание", "Введите хотя бы один продукт.")
            return

        result_text = f"Суммарно за трапезу:\nБелки: {total_protein:.2f} г\nЖиры: {total_fat:.2f} г\nУглеводы: {total_carb:.2f} г"
        messagebox.showinfo("Результат", result_text)
        
        # Сохраняем трапезу и получаем ее содержимое для отправки по почте
        last_meal_content_for_email = save_meal_to_file(entries, total_protein, total_fat, total_carb)
        
        # Теперь активируем кнопку отправки письма и устанавливаем ее команду
        email_meal_btn.config(state=tk.NORMAL, command=lambda: send_email_page(parent, email_content=last_meal_content_for_email))

    ttk.Button(parent, text="Рассчитать БЖУ", command=calculate_bju).pack(pady=10)
    
    # Кнопка для отправки текущей трапезы по почте, изначально отключена до расчета трапезы
    email_meal_btn = ttk.Button(parent, text="📧 Отправить эту трапезу по почте", state=tk.DISABLED)
    email_meal_btn.pack(pady=5)

    ttk.Button(parent, text="Назад", command=lambda: create_welcome_page(parent)).pack(pady=5)

def add_product_page(parent):
    """
    Создает интерфейс для добавления нового продукта в базу данных.

    Аргументы:
        parent: Основной виджет-фрейм, куда будут помещены элементы ввода продукта.
    """
    # Удаляем все виджеты из родительского элемента, кроме фонового изображения
    for widget in parent.winfo_children():
        if isinstance(widget, tk.Label) and widget.place_info():
            continue
        widget.destroy()

    ttk.Label(parent, text="Добавить продукт", font=("Arial", 14)).pack(pady=10)

    name_var = tk.StringVar()
    protein_var = tk.StringVar()
    fat_var = tk.StringVar()
    carb_var = tk.StringVar()

    ttk.Label(parent, text="Название продукта").pack()
    ttk.Entry(parent, textvariable=name_var, width=30).pack(pady=5)
    ttk.Label(parent, text="Белки (на 100 г)").pack()
    ttk.Entry(parent, textvariable=protein_var, width=20).pack()
    ttk.Label(parent, text="Жиры (на 100 г)").pack()
    ttk.Entry(parent, textvariable=fat_var, width=20).pack()
    ttk.Label(parent, text="Углеводы (на 100 г)").pack()
    ttk.Entry(parent, textvariable=carb_var, width=20).pack()

    def save_product():
        """
        Сохраняет новый или обновленный продукт в файл продуктов. Выполняет проверку ввода.
        """
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
        
        # Проверяем, существует ли продукт, и перезаписываем его для простоты
        product_data = load_product_data()
        if name in product_data:
            lines = []
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    # Сохраняем строки, которые не начинаются с названия продукта, который мы собираемся перезаписать
                    if not line.strip().lower().startswith(name + ","):
                        lines.append(line)
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines)  # Записываем обратно все остальные строки
                f.write(f"{name},{protein},{fat},{carb}\n")  # Добавляем новую/обновленную строку
            messagebox.showinfo("Успех", f"Продукт '{name}' обновлен.")
        else:
            add_product_to_file(name, protein, fat, carb)
            messagebox.showinfo("Успех", f"Продукт '{name}' добавлен.")
        
        create_welcome_page(parent) # Возвращаемся на страницу приветствия после сохранения

    ttk.Button(parent, text="Сохранить", command=save_product).pack(pady=10)
    ttk.Button(parent, text="Назад", command=lambda: create_welcome_page(parent)).pack(pady=5)

# ---------- ТОЧКА ВХОДА В ПРИЛОЖЕНИЕ ----------
def main():
    """
    Основная функция для инициализации приложения Tkinter, настройки файлов и запуска графического интерфейса.
    """
    # Создаем файл продуктов с данными по умолчанию, если он не существует
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            f.write("яблоко,0.3,0.2,14\nкуриная грудка,31,3.6,0\nгречка,12.6,3.3,68\n")

    root = tk.Tk()
    root.title("Калькулятор БЖУ")
    root.geometry("500x600")
    root.resizable(False, False) # Запрещаем изменение размера окна

    main_frame = tk.Frame(root, width=500, height=600)
    main_frame.pack(fill="both", expand=True)

    set_background(main_frame, "food.png")  # Устанавливаем фоновое изображение
    create_welcome_page(main_frame)  # Показываем начальную страницу приветствия

    root.mainloop()  # Запускаем цикл событий Tkinter

if __name__ == "__main__":
    main()