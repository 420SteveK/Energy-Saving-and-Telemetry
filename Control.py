import socket
import tkinter as tk
from tkinter import messagebox

# =================================================================
# CONFIGURACIÓN DE RED
# =================================================================
IP_PICO = "10.125.175.164"
PUERTO = 5000

cliente_socket = None


def conectar_carro():
    global cliente_socket
    try:
        cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente_socket.connect((IP_PICO, PUERTO))
        lbl_status.config(text="Estado: CONECTADO", fg="green")
        messagebox.showinfo(
            "Éxito", "Conexión establecida con el carro de Fórmula E.")
    except Exception as e:
        lbl_status.config(text="Estado: ERROR", fg="red")
        messagebox.showerror("Error de Conexión",
                             f"No se pudo conectar a {IP_PICO}:\n{e}")


def enviar_comando(comando):
    global cliente_socket
    if cliente_socket:
        try:
            # Se añade \n por seguridad si se envían varios comandos seguidos
            cliente_socket.sendall((comando + "\n").encode('utf-8'))
        except Exception as e:
            lbl_status.config(text="Estado: DESCONECTADO", fg="orange")
            print(f"Error al enviar comando: {e}")
    else:
        print(f"Simulación (Desconectado) -> {comando}")


def mostrar_about():
    messagebox.showinfo(
        "About - Formula E CES Tec",
        "Proyecto II: Telemetría y Circuito Decrementador\n"
        "Institución: Tecnológico de Costa Rica (TEC)\n"
        "Curso: Fundamentos de Sistemas Computacionales\n"
        "Versión: 2.0\n\n"
        "Integrantes:\n"
        "- Kendall Mena Arias 2025095924\n"
        "- Julian Arrieta Ibarra 2022116242\n\n"
        "Guía rápida:\n"
        "1. Presionar el boton de conexión.\n"
        "2. Usar controles de dirección/marchas para conducir.\n"
        "3. En el Panel, activar modo LDR o presionar los bits (000-111) para probar el decrementador."
        "4. En el Panel, activar modo Luces Automaticas o usarlas manualmente."
    )


# =================================================================
# DISEÑO DE LA INTERFAZ GRÁFICA (GUI)
# =================================================================
root = tk.Tk()
root.title("Panel de Control - Formula E CES Tec")
root.geometry("480x820")
root.configure(bg="#212121")

# Barra superior con título y botón About
frame_top = tk.Frame(root, bg="#212121")
frame_top.pack(fill="x", padx=20, pady=10)

lbl_titulo = tk.Label(frame_top, text="TELEMETRÍA Y CONTROL", font=(
    "Arial", 14, "bold"), fg="#00E5FF", bg="#212121")
lbl_titulo.pack(side="left")

btn_about = tk.Button(frame_top, text="ℹ️ About", font=(
    "Arial", 9, "bold"), bg="#0277BD", fg="white", command=mostrar_about)
btn_about.pack(side="right")

btn_conectar = tk.Button(root, text="🔌 ESTABLECER ENLACE WI-FI", font=(
    "Arial", 11, "bold"), bg="#2E7D32", fg="white", command=conectar_carro)
btn_conectar.pack(pady=5, fill="x", padx=20)

lbl_status = tk.Label(root, text="Estado: DESCONECTADO", font=(
    "Arial", 10, "italic"), fg="red", bg="#212121")
lbl_status.pack(pady=2)

# -----------------------------------------------------------------
# PANEL 1: CONTROL DE DIRECCIÓN Y MOTORES
# -----------------------------------------------------------------
frame_motores = tk.LabelFrame(root, text=" Control de Motores (Manual) ",
                              fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_motores.pack(pady=8, fill="x", padx=20)

tk.Button(frame_motores, text="▲ ADELANTE", width=12, bg="#424242", fg="white",
          command=lambda: enviar_comando("adelante")).grid(row=0, column=1, pady=4, padx=5)
tk.Button(frame_motores, text="◀ IZQUIERDA", width=12, bg="#424242", fg="white",
          command=lambda: enviar_comando("izquierda")).grid(row=1, column=0, pady=4, padx=5)
tk.Button(frame_motores, text="🛑 FRENAR", width=12, bg="#D32F2F", fg="white",
          command=lambda: enviar_comando("frenar")).grid(row=1, column=1, pady=4, padx=5)
tk.Button(frame_motores, text="DERECHA ▶", width=12, bg="#424242", fg="white",
          command=lambda: enviar_comando("derecha")).grid(row=1, column=2, pady=4, padx=5)
tk.Button(frame_motores, text="▼ ATRÁS", width=12, bg="#424242", fg="white",
          command=lambda: enviar_comando("atras")).grid(row=2, column=1, pady=4, padx=5)
tk.Button(frame_motores, text="🔄 Centrar Dirección", width=15, bg="#555555", fg="white",
          command=lambda: enviar_comando("centrar")).grid(row=3, column=1, pady=4, padx=5)

# -----------------------------------------------------------------
# PANEL 2: SELECCIÓN DE MARCHAS
# -----------------------------------------------------------------
frame_marchas = tk.LabelFrame(root, text=" Caja de Cambios (PWM) ",
                              fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_marchas.pack(pady=8, fill="x", padx=20)

for m in range(1, 5):
    tk.Button(frame_marchas, text=f"M{m}", width=6, font=("Arial", 10, "bold"), bg="#1565C0", fg="white",
              command=lambda idx=m: enviar_comando(f"marcha {idx}")).pack(side="left", expand=True, pady=8, padx=5)

# -----------------------------------------------------------------
# PANEL 3: SISTEMA DE ILUMINACIÓN
# -----------------------------------------------------------------
frame_luces = tk.LabelFrame(root, text=" Módulo de Iluminación ",
                            fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_luces.pack(pady=8, fill="x", padx=20)

var_full_luces = tk.BooleanVar(value=False)
var_ldr = tk.BooleanVar(value=False)


def toggle_todas_las_luces():
    estado = 1 if var_full_luces.get() else 0
    enviar_comando(f"lf {estado}")
    enviar_comando(f"lb {estado}")


def toggle_ldr():
    estado = 1 if var_ldr.get() else 0
    enviar_comando(f"ldr {estado}")


tk.Checkbutton(frame_luces, text="Encender todas las luces", variable=var_full_luces, bg="#212121",
               fg="white", selectcolor="#424242", command=toggle_todas_las_luces).pack(anchor="w", padx=10, pady=2)
tk.Checkbutton(frame_luces, text="Modo automático luces (Fotorresistencia)", variable=var_ldr,
               bg="#212121", fg="white", selectcolor="#424242", command=toggle_ldr).pack(anchor="w", padx=10, pady=2)

tk.Button(frame_luces, text="⬅ Dir. Izq On", bg="#E65100", fg="white",
          command=lambda: enviar_comando("ll 1")).pack(side="left", expand=True, pady=5)
tk.Button(frame_luces, text="Dir. Der On ➡", bg="#E65100", fg="white",
          command=lambda: enviar_comando("lr 1")).pack(side="left", expand=True, pady=5)
tk.Button(frame_luces, text="Apagar Dir.", bg="#37474F", fg="white", command=lambda: [
          enviar_comando("ll 0"), enviar_comando("lr 0")]).pack(side="left", expand=True, pady=5)

# -----------------------------------------------------------------
# PANEL 4: RUTINAS DE RECORRIDOS
# -----------------------------------------------------------------
frame_rutinas = tk.LabelFrame(root, text=" Trayectorias Autónomas ",
                              fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_rutinas.pack(pady=8, fill="x", padx=20)

tk.Button(frame_rutinas, text="Straight (Línea Recta)", width=18, bg="#6A1B9A", fg="white", command=lambda: [
          enviar_comando("adelante"), root.after(2000, lambda: enviar_comando("frenar"))]).grid(row=0, column=0, pady=4, padx=5)
tk.Button(frame_rutinas, text="Circle (Círculo)", width=18, bg="#6A1B9A", fg="white",
          command=lambda: enviar_comando("circulo")).grid(row=0, column=1, pady=4, padx=5)
tk.Button(frame_rutinas, text="Infinite (En Ocho)", width=18, bg="#6A1B9A", fg="white",
          command=lambda: enviar_comando("infinito")).grid(row=1, column=0, pady=4, padx=5)
tk.Button(frame_rutinas, text="Zig-Zag", width=18, bg="#6A1B9A", fg="white",
          command=lambda: enviar_comando("zigzag")).grid(row=1, column=1, pady=4, padx=5)

# -----------------------------------------------------------------
# PANEL 5: CIRCUITO DECREMENTADOR (Parte II)
# -----------------------------------------------------------------
frame_dec = tk.LabelFrame(root, text=" Circuito Decrementador Circular de 5 ",
                          fg="#FFD54F", bg="#212121", font=("Arial", 10, "bold"))
frame_dec.pack(pady=8, fill="x", padx=20)

var_dec_auto = tk.BooleanVar(value=False)


def toggle_dec_auto():
    estado = 1 if var_dec_auto.get() else 0
    enviar_comando(f"dec_auto {estado}")


chk_dec = tk.Checkbutton(frame_dec, text="Activar Decrementador con Fotorresistencia (8 Rangos)", variable=var_dec_auto,
                         bg="#212121", fg="#FFD54F", selectcolor="#424242", font=("Arial", 9, "bold"), command=toggle_dec_auto)
chk_dec.pack(anchor="w", padx=10, pady=4)

lbl_sub_dec = tk.Label(frame_dec, text="Pruebas Manuales de Tabla de Verdad (A B C):",
                       fg="#BDBDBD", bg="#212121", font=("Arial", 9))
lbl_sub_dec.pack(anchor="w", padx=10)

frame_bits = tk.Frame(frame_dec, bg="#212121")
frame_bits.pack(pady=6, padx=10, fill="x")

# Generar los 8 botones (000 a 111) para enviar las combinaciones manuales
for i in range(8):
    b_str = f"{i:03b}"  # Ej: '000', '001', ..., '111'
    cmd_str = f"dec_man {b_str[0]} {b_str[1]} {b_str[2]}"
    btn_b = tk.Button(frame_bits, text=f"{b_str}\n({i})", width=4, bg="#00695C", fg="white", font=("Arial", 8, "bold"),
                      command=lambda c=cmd_str: [var_dec_auto.set(False), enviar_comando(c)])
    btn_b.pack(side="left", expand=True, padx=2)

btn_dec_off = tk.Button(frame_dec, text="Apagar Modo Decrementador (Volver a luces normales)", bg="#455A64", fg="white", font=("Arial", 8),
                        command=lambda: [var_dec_auto.set(False), enviar_comando("dec_auto 0")])
btn_dec_off.pack(pady=4, padx=10, fill="x")

root.mainloop()
