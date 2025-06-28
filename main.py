import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk


class ImageApp:
  """
  Графическое приложение для базовой обработки изображений.
  """

  def __init__(self, root):
    """
    Инициализация и построение UI.
    """
    self.root = root
    self.root.title("Image Processing App")
    self.root.geometry("800x600")

    # текущее изображение в формате OpenCV (BGR)
    self.img = None
    # PhotoImage для отображения
    self.tkimg = None

    # Строим UI
    self._build_menu()  # в нём же привязаны хоткеи
    self._build_canvas()
    self._build_statusbar()

  def _build_menu(self):
    """
    Создаёт меню и сразу же навешивает сочетания клавиш.
    """
    menubar = tk.Menu(self.root)

    # --- Меню Файл ---
    fm = tk.Menu(menubar, tearoff=False)
    fm.add_command(label="Открыть...", command=self.load_image, accelerator="Ctrl+O")
    fm.add_command(label="Сделать фото", command=self.capture_camera, accelerator="Ctrl+P")
    fm.add_separator()
    fm.add_command(label="Выход", command=self.root.quit, accelerator="Ctrl+Q")
    menubar.add_cascade(label="Файл", menu=fm)

    # --- Меню Обработка ---
    om = tk.Menu(menubar, tearoff=False)
    om.add_command(label="Показать канал", command=self.show_channel)
    om.add_command(label="Усреднение (Blur)", command=self.blur_image)
    om.add_command(label="Повысить резкость", command=self.sharpen_image)
    om.add_command(label="Нарисовать прямоугольник", command=self.draw_rectangle)
    menubar.add_cascade(label="Обработка", menu=om)

    # --- Меню Помощь ---
    hm = tk.Menu(menubar, tearoff=False)
    hm.add_command(label="О программе", command=self.show_about)
    menubar.add_cascade(label="Помощь", menu=hm)

    # Устанавливаем меню в окно
    self.root.config(menu=menubar)

    # Привязка горячих клавиш сразу после создания меню
    shortcuts = {
      "<Control-KeyPress-o>": self.load_image,
      "<Control-KeyPress-p>": self.capture_camera,
      "<Control-KeyPress-q>": self.root.quit,
    }
    for seq, func in shortcuts.items():
      # Захватываем func в f=func, чтобы корректно работало при цикле
      self.root.bind_all(seq, lambda e, f=func: f())

    # Делаем окно активным, чтобы точно было в фокусе
    self.root.focus_force()

  def _build_canvas(self):
    """
    Создаёт Canvas для вывода изображения.
    """
    self.canvas = tk.Canvas(self.root, bg="darkgray")
    self.canvas.pack(fill=tk.BOTH, expand=True)

  def _build_statusbar(self):
    """
    Создаёт строку состояния.
    """
    self.status = tk.Label(self.root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    self.status.pack(side=tk.BOTTOM, fill=tk.X)

  def _update_status(self, text):
    """
    Обновляет текст statusbar.
    """
    self.status.config(text=text)
    self.status.update_idletasks()

  def _show_on_canvas(self, img_bgr):
    """
    Переводим BGR->RGB, масштабируем под Canvas и рисуем.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img_rgb)

    cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
    if cw > 1 and ch > 1:
      pil.thumbnail((cw, ch), Image.Resampling.LANCZOS)

    self.tkimg = ImageTk.PhotoImage(pil)
    self.canvas.delete("all")
    self.canvas.create_image(cw // 2, ch // 2, image=self.tkimg, anchor=tk.CENTER)

  def load_image(self):
    """Загрузить изображение из файла."""
    path = filedialog.askopenfilename(
      filetypes=[("PNG/JPG", "*.png;*.jpg;*.jpeg"), ("Все файлы", "*.*")]
    )
    if not path:
      return
    img = cv2.imread(path)
    if img is None:
      messagebox.showerror("Ошибка", "Не удалось загрузить изображение.")
      return

    self.img = img
    self._update_status(f"Загружено: {path}")
    self._show_on_canvas(self.img)

  def capture_camera(self):
    """Сделать снимок с веб-камеры."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
      messagebox.showerror("Ошибка", "Не удалось подключиться к веб-камере.")
      return
    ret, frame = cap.read()
    cap.release()
    if not ret:
      messagebox.showerror("Ошибка", "Не удалось снять кадр с камеры.")
      return

    self.img = frame
    self._update_status("Снимок с веб-камеры")
    self._show_on_canvas(self.img)

  def show_channel(self):
    """Показать только один цветовой канал (R/G/B)."""
    if self.img is None:
      messagebox.showwarning("Внимание", "Сначала загрузите изображение.")
      return
    ch = simpledialog.askstring("Канал", "Введите канал (R/G/B):")
    if not ch:
      return
    ch = ch.strip().upper()
    idx = {"B": 0, "G": 1, "R": 2}.get(ch)
    if idx is None:
      messagebox.showerror("Ошибка", "Неверный канал. Введите R, G или B.")
      return

    blank = np.zeros_like(self.img)
    blank[:, :, idx] = self.img[:, :, idx]
    self._update_status(f"Показан {ch}-канал")
    self._show_on_canvas(blank)

  def blur_image(self):
    """Применить размытие с ядром k×k."""
    if self.img is None:
      messagebox.showwarning("Внимание", "Сначала загрузите изображение.")
      return
    k = simpledialog.askinteger("Усреднение", "Размер ядра (нечётное число):", minvalue=1)
    if k is None or k % 2 == 0:
      messagebox.showerror("Ошибка", "Размер ядра должен быть нечётным.")
      return

    self.img = cv2.blur(self.img, (k, k))
    self._update_status(f"Усреднение, k={k}")
    self._show_on_canvas(self.img)

  def sharpen_image(self):
    """Повысить резкость через свёртку."""
    if self.img is None:
      messagebox.showwarning("Внимание", "Сначала загрузите изображение.")
      return
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    self.img = cv2.filter2D(self.img, -1, kernel)
    self._update_status("Повышена резкость")
    self._show_on_canvas(self.img)

  def draw_rectangle(self):
    """Нарисовать прямоугольник по координатам."""
    if self.img is None:
      messagebox.showwarning("Внимание", "Сначала загрузите изображение.")
      return
    x1 = simpledialog.askinteger("Прямоугольник", "x1:")
    y1 = simpledialog.askinteger("Прямоугольник", "y1:")
    x2 = simpledialog.askinteger("Прямоугольник", "x2:")
    y2 = simpledialog.askinteger("Прямоугольник", "y2:")
    if None in (x1, y1, x2, y2):
      return

    img2 = self.img.copy()
    cv2.rectangle(img2, (x1, y1), (x2, y2), (255, 0, 0), thickness=2)
    self.img = img2
    self._update_status(f"Нарисован прямоугольник ({x1},{y1})–({x2},{y2})")
    self._show_on_canvas(self.img)

  def show_about(self):
    """Окно 'О программе'."""
    messagebox.showinfo(
      "О программе",
      "Image Processing App\n"
      "Реализовано на Python, OpenCV и Tkinter\n"
      "Автор: Карцев Ж.Д.\n"
      "Группа: ЗКИ24-18Б"
    )


if __name__ == "__main__":
  root = tk.Tk()
  app = ImageApp(root)
  root.mainloop()
