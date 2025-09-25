"""
Audio Speaker Interface for Educational Games

This module provides a simple, high-level interface for playing audio in educational
games and interactive projects. It supports both generated tones and WAV file playback,
with preloading capabilities for better performance in real-time applications.

The Speaker class is designed to be used in button-based games, providing immediate
audio feedback for user interactions and game events.
"""

from glob import glob
import numpy as np
import simpleaudio as sa
import os


class Speaker:
    """
    A simple audio interface for playing tones and WAV files.
    
    This class provides methods for generating and playing audio tones,
    loading and playing WAV files, and preloading sound files for better
    performance in interactive applications.
    
    The Speaker automatically preloads all WAV files from a sounds directory
    for quick access during gameplay, and manages audio playback to prevent
    overlapping sounds.
    
    Attributes:
        sample_rate (int): Audio sample rate in Hz (default: 44100)
        preloaded_wavs (dict): Dictionary of preloaded WAV file objects
        active_play_obj: Currently playing audio object for stop control
    
    Example:
        >>> speaker = Speaker()
        >>> speaker.play_tone(440, 1.0, 0.5)  # Play 440Hz for 1 second
        >>> speaker.play_wav("sounds/beep.wav")  # Play a WAV file
        >>> speaker.play_preloaded_wav("beep")  # Play preloaded sound
    """
    
    def __init__(self, sample_rate=44100):
        """
        Initialize the Speaker with specified sample rate.
        
        Args:
            sample_rate (int): Audio sample rate in Hz. Higher values provide
                             better quality but use more memory. Standard rates
                             are 22050, 44100 (CD quality), or 48000 Hz.
        
        Note:
            The constructor automatically preloads all WAV files from the
            'sounds' directory if it exists, making them available for
            immediate playback during the game.
        """
        self.sample_rate = sample_rate
        self.preloaded_wavs = {}
        self.active_play_obj = None
        self.preload_wav_files()

    def play_tone(self, freq_hz=440, duration_sec=1, volume=0.5, wait_until_done=True):
        """
        Generate and play a sine wave tone.
        
        This method creates a pure sine wave tone at the specified frequency
        and plays it through the system audio. It's useful for creating
        simple sound effects, notifications, or musical tones.
        
        Args:
            freq_hz (float): Frequency of the tone in Hertz. Common values:
                           - 440 Hz: Musical note A4
                           - 523 Hz: Musical note C5
                           - 1000 Hz: High-pitched beep
            duration_sec (float): Duration of the tone in seconds
            volume (float): Volume level from 0.0 (silent) to 1.0 (maximum)
            wait_until_done (bool): If True, blocks until playback finishes.
                                  If False, returns immediately and plays in background.
        
        Example:
            >>> speaker.play_tone(440, 0.5, 0.8)  # A4 note for half second
            >>> speaker.play_tone(1000, 0.1, 1.0)  # Quick high beep
            >>> speaker.play_tone(200, 2.0, 0.3, False)  # Low tone, non-blocking
        
        Note:
            Any currently playing audio will be stopped before the new tone plays.
            Volume values above 1.0 may cause distortion or clipping.
        """
        if self.active_play_obj is not None:
            self.active_play_obj.stop()
        
        t = np.linspace(0, duration_sec, int(self.sample_rate * duration_sec), False)
        wave = np.sin(2 * np.pi * freq_hz * t) * volume
        audio = (wave * 32767).astype(np.int16)  # Convert to 16-bit PCM
        play_obj = sa.play_buffer(audio, 1, 2, self.sample_rate)
        self.active_play_obj = play_obj
        if wait_until_done:
            play_obj.wait_done()

    def preload_wav_files(self, directory="sounds"):
        """
        Preload all WAV files from a directory into memory.
        
        This method scans the specified directory for WAV files and loads
        them into memory for faster playback. This is especially useful
        for games where quick audio feedback is important.
        
        Args:
            directory (str): Directory path containing WAV files to preload.
                           Defaults to "sounds" in the current working directory.
        
        Note:
            - Files are stored using their filename (without .wav extension) as the key
            - If a file fails to load, it's skipped and an error message is printed
            - This method is automatically called during Speaker initialization
            - Preloaded files can be played using play_preloaded_wav()
        
        Example:
            >>> speaker.preload_wav_files("audio")  # Load from 'audio' directory
            >>> speaker.preload_wav_files("/path/to/sounds")  # Absolute path
        
        Performance:
            Preloading uses more memory but provides much faster playback,
            making it ideal for interactive games with immediate audio feedback.
        """
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return
        
        wav_files = glob(os.path.join(directory, "*.wav"))
        
        for wav_path in wav_files:
            try:
                wave_obj = sa.WaveObject.from_wave_file(wav_path)
                # Use filename without extension as key
                filename = os.path.splitext(os.path.basename(wav_path))[0]
                self.preloaded_wavs[filename] = wave_obj
            except Exception as e:
                print(f"Failed to preload {wav_path}: {e}")
        
        print(f"Preloaded {len(self.preloaded_wavs)} WAV files")

    def play_preloaded_wav(self, filename, wait_until_done=True):
        """
        Play a preloaded WAV file by filename.
        
        This method plays a WAV file that was previously loaded into memory
        by preload_wav_files(). This provides much faster playback than
        loading files from disk each time.
        
        Args:
            filename (str): Name of the preloaded file (without .wav extension).
                          For example, if "beep.wav" was preloaded, use "beep".
            wait_until_done (bool): If True, blocks until playback finishes.
                                  If False, returns immediately and plays in background.
        
        Example:
            >>> # Assuming "correct_answer.wav" was preloaded
            >>> speaker.play_preloaded_wav("correct_answer")
            >>> speaker.play_preloaded_wav("incorrect", wait_until_done=False)
        
        Note:
            - If the filename is not found in preloaded files, an error message is printed
            - Any currently playing audio will be stopped before the new sound plays
            - Use list_preloaded_files() to see available preloaded sounds
        
        Performance:
            This method is much faster than play_wav() for frequently used sounds,
            making it ideal for immediate game feedback and rapid audio sequences.
        """
        if self.active_play_obj is not None:
            self.active_play_obj.stop()
        
        if filename in self.preloaded_wavs:
            play_obj = self.preloaded_wavs[filename].play()
            self.active_play_obj = play_obj
            if wait_until_done:
                play_obj.wait_done()
        else:
            print(f"WAV file not preloaded: {filename}")

    def list_preloaded_files(self):
        """
        Return a list of preloaded WAV filenames.
        
        This method provides a way to check which sound files are available
        for immediate playback via play_preloaded_wav().
        
        Returns:
            list: List of filenames (without .wav extension) that are preloaded
                 and ready for playback.
        
        Example:
            >>> available_sounds = speaker.list_preloaded_files()
            >>> print("Available sounds:", available_sounds)
            >>> # Output: ['correct_answer', 'incorrect', 'beep', 'chime']
            >>> 
            >>> if "victory" in available_sounds:
            ...     speaker.play_preloaded_wav("victory")
        
        Note:
            The returned filenames can be used directly with play_preloaded_wav().
            This is useful for debugging audio issues or creating dynamic sound selection.
        """
        return list(self.preloaded_wavs.keys())

        
# Demonstration and testing
if __name__ == "__main__":
    """
    Demonstration of the Speaker class functionality.
    
    This example shows how to:
    1. Create a Speaker instance (automatically preloads sounds)
    2. Play generated tones with different frequencies and volumes
    3. Play WAV files from disk
    4. Use preloaded sounds for faster playback
    
    To run this demonstration:
        python3 speaker.py
    
    Note: Ensure you have audio output enabled and the volume turned up.
    """
    print("Speaker Demo - Initializing...")
    speaker = Speaker()
    
    print("\n1. Playing generated tones:")
    
    # Play 440Hz tone for 1 second
    freq = 440
    duration = 1
    volume = 1
    print(f"Playing {freq}Hz tone (musical note A4) for {duration} second...")
    speaker.play_tone(freq_hz=freq, duration_sec=duration, volume=volume)
    
    # Play a higher frequency tone
    print("Playing 880Hz tone (one octave higher)...")
    speaker.play_tone(freq_hz=880, duration_sec=0.5, volume=0.8)
    
    print("\n2. Demonstrating preloaded sounds:")
    available_sounds = speaker.list_preloaded_files()
    if available_sounds:
        print(f"Available preloaded sounds: {available_sounds}")
        # Play the first available sound as an example
        example_sound = available_sounds[0]
        print(f"Playing preloaded sound: {example_sound}")
        speaker.play_preloaded_wav(example_sound)
    else:
        print("No preloaded sounds found. Create a 'sounds' directory with .wav files.")
    
    print("\n3. Attempting to play WAV file from disk:")
    # Try to play a specific WAV file if it exists
    wav_path = os.path.join(os.path.dirname(__file__), "boxing_bell.wav")
    if os.path.exists(wav_path):
        print(f"Playing WAV file: {wav_path}")
        speaker.play_wav(wav_path)
    else:
        print(f"WAV file not found: {wav_path}")
        print("To test WAV playback, place a file named 'boxing_bell.wav' in the library directory.")
    
    print("\nSpeaker demonstration complete!")
