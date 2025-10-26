# 🎥 Video to AVIF/WebP converter

This is a Python GUI application for converting video files (MP4, MKV) into animated AVIF or WebP files, optimized for web use and small file sizes. It utilizes **ffmpeg** with two-pass encoding for optimal quality and compression.

## 🌟 Features

* **Graphical User Interface (GUI):** Easy-to-use interface built with Python's built-in **Tkinter** library.
* **Format Selection:** Choose between modern **AVIF** (using libaom-av1) or **WebP** (using libwebp) output formats.
* **Custom Parameters:** Selectable encoding parameters specific to each format (e.g., CRF/CPU-Used for AVIF, Quality/Compression Level for WebP).
* **INI Configuration:** Automatically saves and loads the **FFmpeg path** and all **encoding parameters** to `video_converter_settings.ini` for persistence.
* **Two-Pass Encoding:** Uses two-pass encoding for both AVIF and WebP to ensure better quality and accurate file size control.

## 🛠️ Prerequisites

1.  **Python 3:** The script requires Python 3.x to run.
2.  **FFmpeg:** You must have the `ffmpeg` executable installed and provide the correct path in the application.
    * **Download FFmpeg:** [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
3.  **Required Libraries (built-in):** `tkinter`, `subprocess`, `pathlib`, `configparser`. No external `pip` packages are needed.

## ⚙️ Key Parameters

| Format | Parameter | Description |
| :--- | :--- | :--- |
| **AVIF** | **CRF** | Constant Rate Factor: **Lower** value = **Higher** quality (0 is lossless, 63 is worst). |
| **AVIF** | **CPU Used** | CPU-intensive setting: **Higher** value (up to 8) = **Better** compression/smaller size (but slower). |
| **WebP** | **Output Quality** | Quality setting: **Lower** value = **Better** quality (0 is best, 100 is worst). |
| **WebP** | **Compression Level** | Defines the encoding speed/effort (0 is fastest, 6 is best compression). |
| **Both** | **Max Width** | The video will be scaled to this width (height is auto-scaled). |
| **Both** | **Frame Rate** | Frames per second (FPS) of the output animation. Lowering this drastically reduces file size. |

---
