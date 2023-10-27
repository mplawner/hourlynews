import subprocess

def play_audio(filename, volume=100):
    # Ensure volume is within the range [0, 100]
    volume = max(0, min(volume, 100))
    subprocess.run(["/usr/bin/mplayer", "-volume", str(volume), filename])

