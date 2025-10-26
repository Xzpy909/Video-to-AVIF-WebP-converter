import os
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import configparser

# --- Configuration File Setup ---
CONFIG_FILE = 'video_converter_settings.ini'
CONFIG_SECTION = 'Settings'

def load_settings():
    """Load settings from the INI file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    defaults = {
        'ffmpeg_path': '',
        'last_video_path': str(Path.home()),
        'format': 'AVIF', # Default format
        'crf': '30',
        'frame_rate_avif': '16',
        'max_width_avif': '720',
        'scale_filter_avif': 'lanczos',
        'cpu_used': '8',
        'output_quality_webp': '30',
        'frame_rate_webp': '15',
        'max_width_webp': '720',
        'scale_filter_webp': 'lanczos',
        'compression_level': '6',
        'preset': 'default',
    }

    if not config.has_section(CONFIG_SECTION):
        return defaults
        
    # Overwrite defaults with values from the INI file
    settings = {}
    for key, default_value in defaults.items():
        settings[key] = config.get(CONFIG_SECTION, key, fallback=default_value)
        
    return settings

def save_settings(settings):
    """Save settings to the INI file."""
    config = configparser.ConfigParser()
    config[CONFIG_SECTION] = settings
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# --- Core Conversion Logic ---
def convert_video(input_file, output_file, format_type, params, ffmpeg_path):
    """
    Convert a single video file to AVIF or WebP using ffmpeg.
    Uses two-pass encoding for both formats.
    """
    
    # Common parameters
    scale_filter = params.get('scale_filter_avif') if format_type == 'AVIF' else params.get('scale_filter_webp')
    max_width = params.get('max_width_avif') if format_type == 'AVIF' else params.get('max_width_webp')
    frame_rate = params.get('frame_rate_avif') if format_type == 'AVIF' else params.get('frame_rate_webp')
    
    # Format-specific parameters and encoder
    if format_type == 'AVIF':
        encoder_config = {
            'c:v': 'libaom-av1',
            'param1_key': '-crf',
            'param1_val': params.get('crf'),
            'param2_key': '-cpu-used',
            'param2_val': params.get('cpu_used'),
            'extra_args': ['-b:v', '0', '-pix_fmt', 'yuv420p'],
        }
    else: # WebP
        encoder_config = {
            'c:v': 'libwebp',
            'param1_key': '-quality',
            'param1_val': params.get('output_quality_webp'),
            'param2_key': '-compression_level',
            'param2_val': params.get('compression_level'),
            'extra_args': ['-preset', params.get('preset')],
        }

    # First pass: Analyze the video
    first_pass = [
        ffmpeg_path,
        '-i', input_file,
        '-vf', f'scale={max_width}:-2:flags={scale_filter}',
        '-r', frame_rate,
        '-c:v', encoder_config['c:v'],
        encoder_config['param1_key'], encoder_config['param1_val'],
        encoder_config['param2_key'], encoder_config['param2_val'],
        *encoder_config['extra_args'],
        '-pass', '1',
        '-f', 'null',
        '-'
    ]
    
    # Second pass: Generate the output
    second_pass = [
        ffmpeg_path,
        '-i', input_file,
        '-vf', f'scale={max_width}:-2:flags={scale_filter}',
        '-r', frame_rate,
        '-c:v', encoder_config['c:v'],
        encoder_config['param1_key'], encoder_config['param1_val'],
        encoder_config['param2_key'], encoder_config['param2_val'],
        *encoder_config['extra_args'],
        '-pass', '2',
        '-loop', '0',
        output_file
    ]
    
    try:
        # Run first pass
        print(f"Starting first pass for {input_file}...")
        subprocess.run(first_pass, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Run second pass
        print(f"Starting second pass for {input_file}...")
        subprocess.run(second_pass, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        messagebox.showinfo("Success", f"Successfully converted {Path(input_file).name} to {Path(output_file).name}")
        return True
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Conversion Error", f"Error converting {Path(input_file).name}: {e.stderr}")
        return False
    except FileNotFoundError:
        messagebox.showerror("Error", f"Error: ffmpeg not found at {ffmpeg_path}. Please ensure the path is correct.")
        return False
    except Exception as e:
        messagebox.showerror("Unknown Error", f"An unexpected error occurred: {e}")
        return False

# --- Tkinter GUI Application ---
class VideoConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Video to AVIF/WebP Converter")

        self.settings = load_settings()
        self.variables = {}
        
        self.setup_variables()
        self.create_widgets()
        self.update_format_fields()

    def setup_variables(self):
        """Initialize Tkinter variables from loaded settings."""
        self.variables['ffmpeg_path'] = tk.StringVar(value=self.settings['ffmpeg_path'])
        self.variables['input_video_path'] = tk.StringVar(value="")
        self.variables['format'] = tk.StringVar(value=self.settings['format'])

        # AVIF Variables
        self.variables['crf'] = tk.StringVar(value=self.settings['crf'])
        self.variables['frame_rate_avif'] = tk.StringVar(value=self.settings['frame_rate_avif'])
        self.variables['max_width_avif'] = tk.StringVar(value=self.settings['max_width_avif'])
        self.variables['scale_filter_avif'] = tk.StringVar(value=self.settings['scale_filter_avif'])
        self.variables['cpu_used'] = tk.StringVar(value=self.settings['cpu_used'])

        # WebP Variables
        self.variables['output_quality_webp'] = tk.StringVar(value=self.settings['output_quality_webp'])
        self.variables['frame_rate_webp'] = tk.StringVar(value=self.settings['frame_rate_webp'])
        self.variables['max_width_webp'] = tk.StringVar(value=self.settings['max_width_webp'])
        self.variables['scale_filter_webp'] = tk.StringVar(value=self.settings['scale_filter_webp'])
        self.variables['compression_level'] = tk.StringVar(value=self.settings['compression_level'])
        self.variables['preset'] = tk.StringVar(value=self.settings['preset'])
        
        self.variables['format'].trace_add('write', self.format_change_callback)

    def create_widgets(self):
        """Create and lay out all GUI components."""
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- I/O Configuration Section ---
        io_frame = ttk.LabelFrame(main_frame, text="Input/Output Configuration", padding="10")
        io_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E, pady=10)

        # 1. FFmpeg Path
        ttk.Label(io_frame, text="FFmpeg Path:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(io_frame, textvariable=self.variables['ffmpeg_path'], width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(io_frame, text="Browse (ffmpeg.exe)", command=self.browse_ffmpeg).grid(row=0, column=2, padx=5, pady=5)

        # 2. Video File
        ttk.Label(io_frame, text="Video File:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(io_frame, textvariable=self.variables['input_video_path'], width=50, state='readonly').grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(io_frame, text="Browse (Video)", command=self.browse_video).grid(row=1, column=2, padx=5, pady=5)
        
        # 3. Output Format
        ttk.Label(io_frame, text="Output Format:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(io_frame, text="AVIF", variable=self.variables['format'], value="AVIF").grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(io_frame, text="WebP", variable=self.variables['format'], value="WebP").grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)

        # --- Parameters Section ---
        self.param_frame = ttk.LabelFrame(main_frame, text="Conversion Parameters", padding="10")
        self.param_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E, pady=10)
        
        self.create_avif_widgets(self.param_frame)
        self.create_webp_widgets(self.param_frame)

        # --- Convert Button ---
        ttk.Button(main_frame, text="Convert Video", command=self.run_conversion).grid(row=2, column=0, columnspan=2, pady=20)
        
    def create_avif_widgets(self, parent_frame):
        """Create and hide/show AVIF-specific widgets."""
        self.avif_widgets = {}
        row = 0
        
        # CRF (Constant Rate Factor)
        ttk.Label(parent_frame, text="CRF (0-63):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.avif_widgets['crf'] = ttk.Entry(parent_frame, textvariable=self.variables['crf'], width=15)
        self.avif_widgets['crf'].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1

        # Frame Rate
        ttk.Label(parent_frame, text="Frame Rate (AVIF FPS):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.avif_widgets['frame_rate_avif'] = ttk.Entry(parent_frame, textvariable=self.variables['frame_rate_avif'], width=15)
        self.avif_widgets['frame_rate_avif'].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1

        # Max Width
        ttk.Label(parent_frame, text="Max Width (AVIF px):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.avif_widgets['max_width_avif'] = ttk.Entry(parent_frame, textvariable=self.variables['max_width_avif'], width=15)
        self.avif_widgets['max_width_avif'].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Scale Filter
        ttk.Label(parent_frame, text="Scale Filter (AVIF):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.avif_widgets['scale_filter_avif'] = ttk.Combobox(parent_frame, textvariable=self.variables['scale_filter_avif'], values=['lanczos', 'bilinear', 'bicubic'], width=13)
        self.avif_widgets['scale_filter_avif'].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # CPU Used
        ttk.Label(parent_frame, text="CPU Used (0-8):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.avif_widgets['cpu_used'] = ttk.Entry(parent_frame, textvariable=self.variables['cpu_used'], width=15)
        self.avif_widgets['cpu_used'].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1

    def create_webp_widgets(self, parent_frame):
        """Create and hide/show WebP-specific widgets."""
        self.webp_widgets = {}
        row = 0
        
        # Output Quality
        ttk.Label(parent_frame, text="Output Quality (0-100):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        self.webp_widgets['output_quality_webp'] = ttk.Entry(parent_frame, textvariable=self.variables['output_quality_webp'], width=15)
        self.webp_widgets['output_quality_webp'].grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        row += 1

        # Frame Rate
        ttk.Label(parent_frame, text="Frame Rate (WebP FPS):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        self.webp_widgets['frame_rate_webp'] = ttk.Entry(parent_frame, textvariable=self.variables['frame_rate_webp'], width=15)
        self.webp_widgets['frame_rate_webp'].grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Max Width
        ttk.Label(parent_frame, text="Max Width (WebP px):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        self.webp_widgets['max_width_webp'] = ttk.Entry(parent_frame, textvariable=self.variables['max_width_webp'], width=15)
        self.webp_widgets['max_width_webp'].grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Scale Filter
        ttk.Label(parent_frame, text="Scale Filter (WebP):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        self.webp_widgets['scale_filter_webp'] = ttk.Combobox(parent_frame, textvariable=self.variables['scale_filter_webp'], values=['lanczos', 'bilinear', 'bicubic'], width=13)
        self.webp_widgets['scale_filter_webp'].grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        row += 1

        # Compression Level
        ttk.Label(parent_frame, text="Compression Level (0-6):").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        self.webp_widgets['compression_level'] = ttk.Entry(parent_frame, textvariable=self.variables['compression_level'], width=15)
        self.webp_widgets['compression_level'].grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Preset
        ttk.Label(parent_frame, text="Preset:").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
        self.webp_widgets['preset'] = ttk.Combobox(parent_frame, textvariable=self.variables['preset'], values=['none', 'default', 'photo', 'picture', 'drawing', 'icon', 'text'], width=13)
        self.webp_widgets['preset'].grid(row=row, column=3, sticky=tk.W, padx=5, pady=2)
        row += 1

    def format_change_callback(self, *args):
        """Update displayed parameter fields when the format radio button changes."""
        self.update_format_fields()

    def update_format_fields(self):
        """Show only the relevant parameter fields based on selected format."""
        selected_format = self.variables['format'].get()
        
        # Show/Hide AVIF widgets
        for widget in self.avif_widgets.values():
            if selected_format == 'AVIF':
                # Widgets are managed by grid, so re-grid to show
                widget.grid()
                widget.master.grid_columnconfigure(1, weight=1)
            else:
                widget.grid_remove()
                
        # Show/Hide WebP widgets
        for widget in self.webp_widgets.values():
            if selected_format == 'WebP':
                # Widgets are managed by grid, so re-grid to show
                widget.grid()
                widget.master.grid_columnconfigure(3, weight=1)
            else:
                widget.grid_remove()

    def browse_ffmpeg(self):
        """Open a file dialog to select the ffmpeg executable."""
        initial_dir = Path(self.variables['ffmpeg_path'].get()).parent if self.variables['ffmpeg_path'].get() else str(Path.home())
        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select ffmpeg executable",
            filetypes=(("Executable files", "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"), ("All files", "*.*"))
        )
        if filepath:
            self.variables['ffmpeg_path'].set(filepath)

    def browse_video(self):
        """Open a file dialog to select the input video file."""
        initial_dir = self.settings.get('last_video_path', str(Path.home()))
        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Video File",
            filetypes=(("Video files", "*.mp4 *.mkv"), ("All files", "*.*"))
        )
        if filepath:
            self.variables['input_video_path'].set(filepath)
            # Update last_video_path for the next browse operation
            self.settings['last_video_path'] = str(Path(filepath).parent)

    def save_current_settings(self):
        """Update and save all current settings from the GUI to the INI file."""
        # Update settings dict from StringVar values
        for key, var in self.variables.items():
            if key != 'input_video_path': # Don't save the transient input video path
                self.settings[key] = var.get()
                
        save_settings(self.settings)

    def run_conversion(self):
        """Validate inputs, save settings, and start the video conversion."""
        self.save_current_settings() # Save settings before conversion

        ffmpeg_path = self.variables['ffmpeg_path'].get()
        input_video_path = self.variables['input_video_path'].get()
        format_type = self.variables['format'].get()

        if not Path(ffmpeg_path).is_file():
            messagebox.showerror("Validation Error", "Please provide a valid path to the FFmpeg executable.")
            return

        if not Path(input_video_path).is_file():
            messagebox.showerror("Validation Error", "Please select a valid input video file.")
            return
            
        # Determine output file path
        input_path = Path(input_video_path)
        output_suffix = '.avif' if format_type == 'AVIF' else '.webp'
        output_file_path = str(input_path.with_suffix(output_suffix))

        # Collect all parameters for the conversion function
        params_to_pass = {k: v.get() for k, v in self.variables.items()}
        
        # Execute conversion in a non-blocking way (simple version for this GUI)
        self.master.config(cursor="wait")
        try:
            convert_video(input_video_path, output_file_path, format_type, params_to_pass, ffmpeg_path)
        finally:
            self.master.config(cursor="")
            
if __name__ == '__main__':
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()