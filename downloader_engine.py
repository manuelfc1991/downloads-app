
import os
import subprocess
import threading
import time
from kivy.utils import platform

# If we are on Android, we might need to set specific paths
# later on. For now, we assume 'aria2c' and 'yt-dlp' are available 
# or we use the python library for yt-dlp.

class DownloaderEngine:
    def __init__(self, output_callback=None):
        self.output_callback = output_callback
        self.stop_event = threading.Event()

    def log(self, message):
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message)

    def get_download_folder(self):
        """
        Get a safe download folder.
        On Android, we'll default to app private storage or external files dir
        to avoid permission hell initially.
        """
        if platform == 'android':
            from android.storage import primary_external_storage_path
            # This is usually /storage/emulated/0
            # But writing there requires permissions.
            # Safer: app context.
            # For now, let's try a standard 'Download' folder in the app sandbox or public if permitted.
            # We'll stick to a folder inside the current working dir for simplicity in 'main.py' context
            # but on Android we really want /sdcard/Download if possible.
            
            # Using PythonActivity to get external files dir would be best practice,
            # but let's default to a 'downloads' folder in the current path
            # effectively internal storage for the app.
            return "downloads" 
        else:
            return "downloads"

    def download_torrent(self, link, folder):
        self.log(f"[Torrent] Starting: {link}")
        # aria2c needs to be present
        cmd = ['aria2c', '--enable-rpc=false', '-d', folder, link]
        self.run_cmd(cmd)

    def download_video(self, link, folder):
        self.log(f"[Video] Starting: {link}")
        # yt-dlp is best used via library if we want progress,
        # but to keep 'mostly intact' logic:
        cmd = ['yt-dlp', '-P', folder, link]
        self.run_cmd(cmd)

    def download_file(self, link, folder):
        self.log(f"[File] Starting: {link}")
        cmd = ['aria2c', '-d', folder, link]
        self.run_cmd(cmd)

    def run_cmd(self, cmd):
        try:
            # We use Popen to capture output in real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            for line in process.stdout:
                if self.stop_event.is_set():
                    process.terminate()
                    self.log("[Stopped] Download cancelled.")
                    break
                self.log(line.strip())
                
            process.wait()
        except FileNotFoundError:
            self.log(f"[Error] Command not found: {cmd[0]}")
            self.log("Please ensure the binary is installed or bundled.")
        except Exception as e:
            self.log(f"[Error] {str(e)}")

    def detect_and_download(self, url, folder):
        url = url.strip()
        if not url:
            return

        if not os.path.exists(folder):
            os.makedirs(folder)

        if url.startswith("magnet:") or url.endswith(".torrent"):
            self.download_torrent(url, folder)
        else:
            # Fallback / Default to yt-dlp which handles many generic files too if configured,
            # but the original script distinguished them.
            # The original script used 'download_video' (yt-dlp) for everything else.
            self.download_video(url, folder)

    def process_queue(self, url_queue):
        folder = self.get_download_folder()
        total = len(url_queue)
        self.log(f"Processing queue: {total} items")
        
        for idx, url in enumerate(url_queue, start=1):
            if self.stop_event.is_set():
                break
            self.log(f"--- Item {idx}/{total} ---")
            self.detect_and_download(url, folder)
            self.log(f"--- Item {idx} Finished ---")
            # time.sleep(1) # Optional pause

        self.log("All tasks completed.")
