# 3D Audio-Reactive Sphere Visualizer

This project is an interactive 3D audio-visual experience where a large sphere, composed of many smaller spheres, responds dynamically to an audio file's frequency spectrum. When the audio plays, the small spheres move in response to the audio, creating an immersive visual effect. When the audio stops, the small spheres freeze, while the large sphere continues to rotate.

## Features
- **Audio-Responsive Movement**: The small spheres react to FFT (Fast Fourier Transform) values derived from the audio input.
- **Continuous Rotation**: The large sphere rotates continuously, even when the audio stops.
- **Customizable Particle Count**: Easily adjust the number of small spheres to suit your desired visual density and performance needs.

## Requirements
- Python 3.x
- `pygame`
- OpenGL (via `PyOpenGL`)
- `numpy`
- `sounddevice`
- `soundfile`
- `tkinter` (typically included with Python installations)

## Installation
1. Clone the repository or download the project files.
2. Install the required libraries:

    ```bash
    pip install pygame PyOpenGL numpy sounddevice soundfile
    ```

## Usage
1. Run the script: The music.wav file can be any audio file in .wav format:

    ```bash
    python 3D.py music.wav
    ```

2. Upon starting, a GUI window will appear for controlling the audio playback. You can pause, play, and seek through the audio file.
3. Adjust the number of small spheres by modifying the `self.particle_count` variable in the `MusicVisualizer` class in the script.

## Customizing Particle Count
To change the number of small spheres:

1. Open `3D.py` and locate this line in the `MusicVisualizer` class:

    ```python
    self.particle_count = self.chunk_size // 4
    ```

2. Modify the divisor (e.g., `self.chunk_size // 2`) to increase the particle count.

## Audio Format
The visualizer accepts common audio file formats (e.g., `.wav`, `.flac`). If the audio has multiple channels, it will be averaged to mono.

## Controls
- **⏸️ / ▶️ Button**: Toggle play/pause
- **Progress Bar**: Seek to a specific point in the audio

## How It Works
- **Audio Processing**: The script uses `sounddevice` and `soundfile` to load and analyze the audio file in real time.
- **FFT Transformation**: `numpy.fft` processes the audio signal to extract frequency information that drives the particles' movement.
- **3D Rendering**: `pygame` and OpenGL handle the real-time rendering of the large sphere and its particles, allowing smooth movement and rotation.

## Future Enhancements
- Support for additional audio effects and visualization modes.
- Performance optimizations for handling higher particle counts.
