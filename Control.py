import socket
import tkinter as tk
from tkinter import messagebox

# =================================================================
# CONFIGURACIÓN DE RED 
# =================================================================
IP_PICO = "172.26.7.164"
PUERTO = 5000

# Conexión Socket Global
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
            cliente_socket.sendall(comando.encode('utf-8'))
        except Exception as e:
            lbl_status.config(text="Estado: DESCONECTADO", fg="orange")
            print(f"Error al enviar comando: {e}")
    else:
        print("No conectado al servidor del vehículo.")


# =================================================================
# DISEÑO DE LA INTERFAZ GRÁFICA (GUI)
# =================================================================
root = tk.Tk()
root.title("Panel de Control - Formula E CES Tec")
root.geometry("450x650")
root.configure(bg="#212121")

# Etiquetas de estado
lbl_titulo = tk.Label(root, text="TELEMETRÍA Y CONTROL CENTRAL", font=(
    "Arial", 14, "bold"), fg="#00E5FF", bg="#212121")
lbl_titulo.pack(pady=10)

btn_conectar = tk.Button(root, text="🔌 ESTABLECER ENLACE WI-FI", font=(
    "Arial", 11, "bold"), bg="#2E7D32", fg="white", command=conectar_carro)
btn_conectar.pack(pady=5, fill="x", padx=20)

lbl_status = tk.Label(root, text="Estado: DESCONECTADO", font=(
    "Arial", 10, "italic"), fg="red", bg="#212121")
lbl_status.pack(pady=5)

# -----------------------------------------------------------------
# PANEL 1: CONTROL DE DIRECCIÓN Y MOTORES (Requerimiento 4)
# -----------------------------------------------------------------
frame_motores = tk.LabelFrame(root, text=" Control de Motores (Manual) ",
                              fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_motores.pack(pady=10, fill="x", padx=20)

btn_adelante = tk.Button(frame_motores, text="▲ ADELANTE", width=12,
                         bg="#424242", fg="white", command=lambda: enviar_comando("adelante"))
btn_adelante.grid(row=0, column=1, pady=5, padx=5)

btn_izq = tk.Button(frame_motores, text="◀ IZQUIERDA", width=12,
                    bg="#424242", fg="white", command=lambda: enviar_comando("izquierda"))
btn_izq.grid(row=1, column=0, pady=5, padx=5)

btn_freno = tk.Button(frame_motores, text="🛑 FRENAR", width=12,
                      bg="#D32F2F", fg="white", command=lambda: enviar_comando("frenar"))
btn_freno.grid(row=1, column=1, pady=5, padx=5)

btn_der = tk.Button(frame_motores, text="DERECHA ▶", width=12,
                    bg="#424242", fg="white", command=lambda: enviar_comando("derecha"))
btn_der.grid(row=1, column=2, pady=5, padx=5)

btn_atras = tk.Button(frame_motores, text="▼ ATRÁS", width=12,
                      bg="#424242", fg="white", command=lambda: enviar_comando("atras"))
btn_atras.grid(row=2, column=1, pady=5, padx=5)

btn_centrar = tk.Button(frame_motores, text="🔄 Centrar Dirección", width=15,
                        bg="#555555", fg="white", command=lambda: enviar_comando("centrar"))
btn_centrar.grid(row=3, column=1, pady=5, padx=5)

# -----------------------------------------------------------------
# PANEL 2: SELECCIÓN DE MARCHAS (Requerimiento 3)
# -----------------------------------------------------------------
frame_marchas = tk.LabelFrame(root, text=" Caja de Cambios (PWM) ",
                              fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_marchas.pack(pady=10, fill="x", padx=20)

for m in range(1, 5):
    btn_m = tk.Button(frame_marchas, text=f"M{m}", width=6, font=("Arial", 10, "bold"), bg="#1565C0", fg="white",
                      command=lambda idx=m: enviar_comando(f"marcha {idx}"))
    btn_m.pack(side="left", expand=True, pady=10, padx=5)

# -----------------------------------------------------------------
# PANEL 3: SISTEMA DE ILUMINACIÓN (Requerimiento 2)
# -----------------------------------------------------------------
frame_luces = tk.LabelFrame(root, text=" Módulo de Iluminación ",
                            fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_luces.pack(pady=10, fill="x", padx=20)

# Variables booleanas de interfaz para simular interruptores (toggle)
var_full_luces = tk.BooleanVar(value=False)
var_ldr = tk.BooleanVar(value=False)


def toggle_todas_las_luces():
    estado = 1 if var_full_luces.get() else 0
    enviar_comando(f"lf {estado}")
    enviar_comando(f"lb {estado}")


def toggle_ldr():
    estado = 1 if var_ldr.get() else 0
    enviar_comando(f"ldr {estado}")


chk_luces = tk.Checkbutton(frame_luces, text="Encender todas las luces", variable=var_full_luces,
                           bg="#212121", fg="white", selectcolor="#424242", command=toggle_todas_las_luces)
chk_luces.pack(anchor="w", padx=10, pady=2)

chk_ldr = tk.Checkbutton(frame_luces, text="Activar modo automático (Fotorresistencia)",
                         variable=var_ldr, bg="#212121", fg="white", selectcolor="#424242", command=toggle_ldr)
chk_ldr.pack(anchor="w", padx=10, pady=2)

btn_l_izq = tk.Button(frame_luces, text="⬅ Direccional Izq On",
                      bg="#E65100", fg="white", command=lambda: enviar_comando("ll 1"))
btn_l_izq.pack(side="left", expand=True, pady=5)

btn_l_der = tk.Button(frame_luces, text="Direccional Der On ➡",
                      bg="#E65100", fg="white", command=lambda: enviar_comando("lr 1"))
btn_l_der.pack(side="left", expand=True, pady=5)

btn_l_off = tk.Button(frame_luces, text="Apagar Direccionales", bg="#37474F",
                      fg="white", command=lambda: {enviar_comando("ll 0"), enviar_comando("lr 0")})
btn_l_off.pack(side="left", expand=True, pady=5)

# -----------------------------------------------------------------
# PANEL 4: RUTINAS DE RECORRIDOS (Requerimiento 2)
# -----------------------------------------------------------------
frame_rutinas = tk.LabelFrame(root, text=" Trayectorias y Patrones Autónomos ",
                              fg="white", bg="#212121", font=("Arial", 10, "bold"))
frame_rutinas.pack(pady=10, fill="x", padx=20)

btn_linea = tk.Button(frame_rutinas, text="Straight (Línea Recta)", width=18, bg="#6A1B9A", fg="white", command=lambda: {
                      enviar_comando("adelante"), root.after(2000, lambda: enviar_comando("frenar"))})
btn_linea.grid(row=0, column=0, pady=5, padx=5)

btn_circulo = tk.Button(frame_rutinas, text="Circle (Círculo)", width=18,
                        bg="#6A1B9A", fg="white", command=lambda: enviar_comando("circulo"))
btn_circulo.grid(row=0, column=1, pady=5, padx=5)

btn_infinito = tk.Button(frame_rutinas, text="Infinite (En Ocho)", width=18,
                         bg="#6A1B9A", fg="white", command=lambda: enviar_comando("infinito"))
btn_infinito.grid(row=1, column=0, pady=5, padx=5)

btn_zigzag = tk.Button(frame_rutinas, text="Zig-Zag", width=18,
                       bg="#6A1B9A", fg="white", command=lambda: enviar_comando("zigzag"))
btn_zigzag.grid(row=1, column=1, pady=5, padx=5)

root.mainloop()
