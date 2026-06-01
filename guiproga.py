import tkinter as tk
from tkinter import messagebox
import json
import os


class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Список дел")
        self.root.geometry("450x500")

        # Список задач: [{"текст": "...", "выполнено": False}, ...]
        self.tasks = []
        self.file = "tasks.json"

        self.load_tasks()  # загружаем сохранённые задачи
        self.create_ui()  # создаём кнопки, поле ввода, список
        self.update_list()  # показываем задачи на экране

        # Горячие клавиши
        self.root.bind("<Return>", lambda e: self.add_task())  # Enter - добавить
        self.root.bind("<Delete>", lambda e: self.delete_task())  # Delete - удалить
        self.root.bind("<Control-s>", lambda e: self.save_tasks())  # Ctrl+S - сохранить

    def create_ui(self):
        # Поле ввода и кнопка "Добавить"
        self.entry = tk.Entry(self.root, font=("Arial", 12))
        self.entry.pack(pady=10, padx=10, fill=tk.X)

        btn_add = tk.Button(self.root, text="Добавить", command=self.add_task, bg="lightgreen")
        btn_add.pack(pady=5)

        # Список задач (с прокруткой)
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scroll = tk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame, font=("Arial", 11), yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.listbox.yview)

        # Двойной клик по задаче - отметить как выполненную
        self.listbox.bind("<Double-Button-1>", lambda e: self.toggle_task())

        # Кнопки управления
        btn_done = tk.Button(self.root, text="Отметить выполненной", command=self.toggle_task)
        btn_done.pack(side=tk.LEFT, padx=10, pady=5)

        btn_delete = tk.Button(self.root, text="Удалить", command=self.delete_task, bg="lightcoral")
        btn_delete.pack(side=tk.LEFT, padx=10, pady=5)

    def add_task(self):
        """Добавляем новую задачу"""
        text = self.entry.get().strip()
        if not text:
            messagebox.showwarning("Ошибка", "Введите текст задачи")
            return

        self.tasks.append({"текст": text, "выполнено": False})
        self.entry.delete(0, tk.END)
        self.update_list()
        self.save_tasks()

    def delete_task(self):
        """Удаляем выбранную задачу"""
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу для удаления")
            return

        del self.tasks[selected[0]]
        self.update_list()
        self.save_tasks()

    def toggle_task(self):
        """Отмечаем задачу выполненной / снимаем отметку"""
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу")
            return

        # Меняем статус на противоположный
        self.tasks[selected[0]]["выполнено"] = not self.tasks[selected[0]]["выполнено"]
        self.update_list()
        self.save_tasks()

    def update_list(self):
        """Обновляем отображение списка"""
        self.listbox.delete(0, tk.END)
        for task in self.tasks:
            text = task["текст"]
            if task["выполнено"]:
                # выполненные задачи показываем с галочкой и серым цветом
                self.listbox.insert(tk.END, f"✓ {text}")
                self.listbox.itemconfig(tk.END, fg="gray")
            else:
                self.listbox.insert(tk.END, f"○ {text}")
                self.listbox.itemconfig(tk.END, fg="black")

    def save_tasks(self):
        """Сохраняем в файл"""
        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не сохранилось: {e}")

    def load_tasks(self):
        """Загружаем из файла"""
        if not os.path.exists(self.file):
            return

        try:
            with open(self.file, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
        except:
            self.tasks = []  # если файл битый - начинаем с пустого списка


# Запуск программы
if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)
    root.mainloop()