import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
from pynput import keyboard
import pygame
import pystray
from PIL import Image, ImageTk
import sys
import os
import psutil

# Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(SCRIPT_DIR, "soundkey.lock")
icon_path = os.path.join(SCRIPT_DIR, "icon.png")

# Ensure single instance
if os.path.exists(LOCK_FILE):
    try:
        with open(LOCK_FILE, "r") as f:
            pid = int(f.read().strip())
        if psutil.pid_exists(pid):
            messagebox.showerror("Error", "Another instance is already running.")
            sys.exit(0)
        else:
            os.remove(LOCK_FILE)
    except:
        os.remove(LOCK_FILE)

try:
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
except Exception as e:
    messagebox.showerror("Error", f"Cannot create lock file: {e}")
    sys.exit(1)

# Pygame mixer
pygame.mixer.init()

if os.path.exists(icon_path):
    tray_icon_image = Image.open(icon_path)
else:
    tray_icon_image = Image.new("RGB", (64, 64), "black")

selected_key = None
listener = None
listening_for_bind = False
sound = None
volume_value_label = None  # Define early

# GUI Setup
root = tk.Tk()
root.title("SoundKey Binder")
root.geometry("320x280")
root.resizable(False, False)

if os.path.exists(icon_path):
    tk_icon = ImageTk.PhotoImage(tray_icon_image)
    root.iconphoto(True, tk_icon)

def load_sound(path):
    global sound
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume_slider.get())
        return s
    except pygame.error as e:
        messagebox.showerror("Error", f"Could not load sound:\n{e}")
        return None

def on_key_press_global(key):
    global listening_for_bind
    if listening_for_bind:
        set_key(key)
    elif selected_key:
        try:
            if key == selected_key and sound:
                sound.play()
        except:
            pass

def start_listener():
    global listener
    if listener:
        listener.stop()
    listener = keyboard.Listener(on_press=on_key_press_global)
    listener.start()

def bind_key():
    global listening_for_bind
    listening_for_bind = True
    status_label.config(text="Press any key to bind...", foreground="blue")

def set_key(key):
    global selected_key, listening_for_bind
    selected_key = key
    listening_for_bind = False
    try:
        key_str = key.char
    except AttributeError:
        key_str = str(key).replace("Key.", "")
    status_label.config(text=f"Bound to key: {key_str.upper()}", foreground="green")
    start_listener()

def quit_app(icon=None, item=None):
    global listener
    try:
        if listener:
            listener.stop()
        if icon:
            icon.stop()
        root.quit()
    finally:
        if os.path.exists(LOCK_FILE):
            try:
                os.remove(LOCK_FILE)
            except:
                pass

def hide_to_tray():
    root.withdraw()
    icon = pystray.Icon("SoundKey", tray_icon_image, "SoundKey", pystray.Menu(
        pystray.MenuItem("Show", lambda icon, item: root.after(0, show_window)),
        pystray.MenuItem("Quit", quit_app)
    ))
    Thread(target=icon.run, daemon=True).start()

def show_window():
    root.deiconify()

def browse_sound():
    filetypes = [
        ("WAV files", "*.wav"),
        ("MP3 files", "*.mp3"),
        ("OGG files", "*.ogg"),
        ("All files", "*.*"),
    ]
    path = filedialog.askopenfilename(title="Select sound file", initialdir=SCRIPT_DIR, filetypes=filetypes)
    if path:
        global sound
        s = load_sound(path)
        if s:
            sound = s
            sound_label.config(text=f"Sound: {os.path.basename(path)}")
        else:
            sound_label.config(text="No sound loaded")

# Widgets
ttk.Label(root, text="Click below to bind a key:").pack(pady=(15, 5))
ttk.Button(root, text="Bind Key", command=bind_key).pack(pady=5)

status_label = ttk.Label(root, text="No key bound.", foreground="red")
status_label.pack(pady=5)

ttk.Button(root, text="Select Sound File", command=browse_sound).pack(pady=(15, 5))
sound_label = ttk.Label(root, text="No sound loaded.")
sound_label.pack()

ttk.Label(root, text="Volume").pack(pady=(15, 2))
volume_frame = ttk.Frame(root)
volume_frame.pack()
volume_slider = ttk.Scale(volume_frame, from_=0.1, to=2.0, orient="horizontal")
volume_slider.set(1.0)
volume_slider.pack(side="left", padx=(5, 5))

volume_value_label = ttk.Label(volume_frame, text="1.0x")
volume_value_label.pack(side="left")

def update_volume(val):
    vol = float(val)
    if sound:
        sound.set_volume(vol)
    volume_value_label.config(text=f"{vol:.1f}x")

volume_slider.config(command=update_volume)

ttk.Button(root, text="Hide to Tray", command=hide_to_tray).pack(pady=5)
ttk.Button(root, text="Quit", command=quit_app).pack(pady=5)

root.protocol("WM_DELETE_WINDOW", hide_to_tray)

start_listener()
root.mainloop()

# Cleanup lock file
if os.path.exists(LOCK_FILE):
    try:
        os.remove(LOCK_FILE)
    except:
        pass
