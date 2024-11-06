import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from numpy.fft import fft
import math
import sounddevice as sd
import soundfile as sf
import sys
from threading import Thread, Lock
import time
import tkinter as tk
from tkinter import ttk
from queue import Queue

class AudioController(tk.Tk):
    def __init__(self, audio_length):
        super().__init__()
        
        self.title("Audio Controls")
        self.geometry("400x100")
        
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10)
        
        self.is_playing = True
        self.play_button = ttk.Button(control_frame, text="⏸️", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Scale(self, from_=0, to=audio_length, orient=tk.HORIZONTAL)
        self.progress.pack(fill=tk.X, padx=10)
        self.progress.bind("<ButtonRelease-1>", self.seek)
        
        self.current_position = 0
        self.seek_position = None
        self.update_queue = Queue()
        
    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_button.config(text="⏸️" if self.is_playing else "▶️")
    
    def seek(self, event):
        self.seek_position = self.progress.get()
    
    def update_progress(self, position):
        self.update_queue.put(position)
    
    def process_events(self):
        while not self.update_queue.empty():
            try:
                position = self.update_queue.get_nowait()
                if not self.progress.instate(['pressed']):
                    self.current_position = position
                    self.progress.set(position)
            except Queue.Empty:
                break
        
        self.update_idletasks()
        self.update()

class Particle:
    def __init__(self, phi, theta, radius):
        self.base_phi = phi
        self.base_theta = theta
        self.base_radius = radius
        self.radius = radius
        self.current_fft = 0
        self.target_fft = 0
        self.smooth_factor = 0.3  # Controls how smoothly particles react
        self.update_position()

    def update_position(self):
        self.x = self.radius * math.sin(self.base_theta) * math.cos(self.base_phi)
        self.y = self.radius * math.sin(self.base_theta) * math.sin(self.base_phi)
        self.z = self.radius * math.cos(self.base_theta)

    def smooth_transition(self):
        # Smoothly interpolate between current and target FFT values
        self.current_fft += (self.target_fft - self.current_fft) * self.smooth_factor
        self.radius = self.base_radius * (1 + 1.0 * self.current_fft)  # Increased scale for more visible effect
        self.update_position()

    def apply_fft(self, fft_value, is_playing):
        if is_playing:
            self.target_fft = fft_value
        else:
            self.target_fft = 0  # When paused, gradually return to base position
        self.smooth_transition()

class MusicVisualizer:
    def __init__(self, music_file):
        pygame.init()
        self.display = (1200, 800)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Music Visualizer")

        self.setup_gl()
        
        self.chunk_size = 8192
        self.particle_count = self.chunk_size // 8
        self.particles = self.create_particles()
        self.fft_data = np.zeros(self.particle_count)
        
        self.setup_audio(music_file)
        
        self.lock = Lock()
        
        # Slower rotation speed
        self.rotation = 0
        self.rotation_speed = 0.09  # Reduced from 0.2 to 0.05
        self.smoothing = 0.3
        
        self.audio_length = len(self.audio_data) / self.sample_rate
        self.controller = AudioController(self.audio_length)

    def setup_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Enhanced lighting for better visibility
        glLightfv(GL_LIGHT0, GL_POSITION, (10.0, 10.0, 10.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(0.0, 0.0, -15)

    def setup_audio(self, music_file):
        try:
            self.audio_data, self.sample_rate = sf.read(music_file)
            if len(self.audio_data.shape) > 1:
                self.audio_data = self.audio_data.mean(axis=1)
            
            self.current_frame = 0
            
        except Exception as e:
            print(f"Error loading audio file: {e}")
            sys.exit(1)
        
        self.audio_thread = Thread(target=self.play_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()

    def play_audio(self):
        try:
            with sd.OutputStream(channels=1, callback=self.audio_callback,
                               samplerate=self.sample_rate):
                while True:
                    if hasattr(self, 'controller'):
                        with self.lock:
                            if self.controller.seek_position is not None:
                                self.current_frame = int(self.controller.seek_position * self.sample_rate)
                                self.controller.seek_position = None
                            
                            if not self.controller.is_playing:
                                time.sleep(0.1)
                                continue
                    
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error playing audio: {e}")

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        
        with self.lock:
            if hasattr(self, 'controller') and not self.controller.is_playing:
                outdata.fill(0)
                return
            
            start = self.current_frame
            end = start + frames
            
            if end > len(self.audio_data):
                remaining = end - len(self.audio_data)
                data = np.concatenate((self.audio_data[start:], self.audio_data[:remaining]))
                self.current_frame = remaining
            else:
                data = self.audio_data[start:end]
                self.current_frame = end
            
            # Enhanced FFT processing for better visualization
            fft_temp = np.abs(fft(data))[:self.particle_count]
            fft_temp = fft_temp / np.max(fft_temp) if np.max(fft_temp) > 0 else fft_temp
            
            # Apply frequency weighting to emphasize certain ranges
            freq_weights = np.linspace(1.5, 0.5, len(fft_temp))  # Emphasize lower frequencies
            fft_temp = fft_temp * freq_weights
            
            self.fft_data = (1 - self.smoothing) * self.fft_data + self.smoothing * fft_temp
            
            if hasattr(self, 'controller'):
                current_time = self.current_frame / self.sample_rate
                self.controller.update_progress(current_time)
            
            outdata[:] = data.reshape(-1, 1)

    def create_particles(self):
        particles = []
        phi_count = int(np.sqrt(self.particle_count))
        theta_count = phi_count * 2

        for i in range(phi_count):
            phi = (i / phi_count) * math.pi
            for j in range(theta_count):
                theta = (j / theta_count) * 2 * math.pi
                particles.append(Particle(phi, theta, 5.0))

        return particles

    def draw_particle(self, particle):
        glPushMatrix()
        glTranslatef(particle.x, particle.y, particle.z)
        
        # Dynamic color based on radius change
        intensity = (particle.radius - particle.base_radius) / (0.3 * particle.base_radius)
        glColor3f(1.0, 1.0 - intensity * 0.5, 1.0 - intensity * 0.7)  # Subtle color variation
        
        sphere = gluNewQuadric()
        gluSphere(sphere, 0.08, 8, 8)
        glPopMatrix()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -15)
        
        # Constant rotation regardless of audio state
        self.rotation += self.rotation_speed
        glRotatef(self.rotation, 0, 1, 0)
        
        # Update and draw particles
        for i, particle in enumerate(self.particles):
            fft_index = i % len(self.fft_data)
            particle.apply_fft(self.fft_data[fft_index], self.controller.is_playing)
            self.draw_particle(particle)

    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    if hasattr(self, 'controller'):
                        self.controller.destroy()
                    return

            self.draw()
            pygame.display.flip()
            if hasattr(self, 'controller'):
                self.controller.process_events()
            clock.tick(60)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <music_file>")
        return
        
    music_file = sys.argv[1]
    visualizer = MusicVisualizer(music_file)
    visualizer.run()

if __name__ == '__main__':
    main()