```text
 ███  ███ █████████          ██████   ██████ ███    ███  █████████ ███  █████████ 
░░███░███░░░░███░░░         ░░██████ ██████ ░███   ░███ ░███░░░░░░ ░███ ░███░░░░░░  
 ░░█████     ░███            ░███░█████░███ ░███   ░███ ░███       ░███ ░███        
  ░░███      ░███   ███████  ░███░░███ ░███ ░███   ░███ ░█████████ ░███ ░███        
   ░███      ░███  ░░░░░░░   ░███ ░░░  ░███ ░███   ░███ ░░░░░░░███ ░███ ░███        
   ░███      ░███            ░███      ░███ ░░███ ███░  █████████  ░███ ░███        
   █████     █████           █████     █████ ░░█████░  ░█████████  █████░█████████  
  ░░░░░     ░░░░░     ░░░░░   ░░░░░    ░░░░░ ░░░░░ ░░░░░░░░░   
```

# YT-Music CLI (Pro Edition)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Textual](https://img.shields.io/badge/UI-Textual-red?logo=gnometerminal&logoColor=white)](https://textual.textualize.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Un reproductor de música **ligero, potente y minimalista** para la terminal. Disfruta de YouTube Music con una interfaz industrial moderna, gestión de colas avanzada y soporte para transparencias.

---

## ✨ Características Actuales

- 🔍 **Búsqueda Inteligente:** Resultados instantáneos con columnas de Título y Artista.
- 🏠 **Search Home:** Acceso directo a recomendaciones personalizadas de YouTube Music.
- 🖼️ **Arte de Álbum en Alta Resolución:** Visualización de portadas mediante bloques ANSI de alta calidad (compatible con cualquier terminal moderna).
- 📂 **Gestión de Colas (Queue):** Añade canciones a tu sesión sin interrumpir la actual. Categoría dedicada en la barra lateral.
- 🔐 **Gestión de Cuenta:** Pantalla centralizada para verificar sesión, cambiar de usuario o cerrar sesión (`Esc`).
- 🔊 **Control de Volumen Dinámico:** Ajuste fino con feedback visual en porcentaje.
- ❤️ **Sistema de Favoritos:** Añade o elimina canciones de tus "Liked Music" instantáneamente.
- 🌓 **Transparencia Nativa:** Respeta la configuración de transparencia y blur de tu terminal (Ghostty, Kitty, etc.).
- 🛡️ **Anti-Bot Bypass:** Integración avanzada con `yt-dlp` usando cookies de navegador e impersonación de Chrome.

---

## ⌨️ Atajos de Teclado (Master List)

| Tecla | Acción |
|-------|--------|
| `Enter` | Reproducir canción seleccionada |
| `Espacio` | Pausar / Reanudar |
| `Alt + Enter` | **Añadir a la cola** |
| `Alt + Backspace` | **Eliminar última de la cola** (Muestra siguiente) |
| `Alt + → / ←` | **Siguiente / Anterior** canción en cola |
| `→ / ←` | Adelantar / Retrasar **10 segundos** |
| `Alt + ↑ / ↓` | **Subir / Bajar volumen** (5%) |
| `Alt + F` | **Like / Unlike** (Añadir/Quitar favoritos) |
| `Alt + H` | **Search Home** (Recomendaciones) |
| `Alt + S` | Enfocar barra de búsqueda |
| `Esc` | Volver a Gestión de Cuenta / Menú Principal |
| `Q` | Salir de la aplicación |

---

## 🛠️ Requisitos del Sistema

- **Python 3.10+**
- **mpv:** Motor de audio recomendado (debe estar en el PATH).
- **yt-dlp:** Instalado automáticamente en el entorno virtual.
- **Navegador Chrome:** Recomendado para el bypass de cookies anti-bot.

## 🚀 Instalación Rápida

1. **Clonar e instalar:**
   ```bash
   git clone https://github.com/tu-usuario/ytmusic-cli.git
   cd yt-music-cli
   python3 -m venv .venv
   source .venv/bin/activate  # En Linux
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Ejecutar:**
   ```bash
   yt-music
   ```

---

Desarrollado con ❤️ para amantes de la terminal.
MIT License © 2026
