
import sys
import traceback
import os

# 1. Base Imports for Error Handling
try:
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.image import Image
except ImportError:
    # If even Kivy is missing, we can't do much on Android GUI
    # But let's try to print to logcat at least
    traceback.print_exc()
    sys.exit(1)

# 2. Crash Reporter App
class ErrorApp(App):
    def __init__(self, error_msg, **kwargs):
        super().__init__(**kwargs)
        self.error_msg = error_msg

    def build(self):
        scroll = ScrollView()
        label = Label(text=self.error_msg, font_size='20sp', size_hint_y=None, halign='left', valign='top')
        label.bind(texture_size=label.setter('size'))
        scroll.add_widget(label)
        return scroll

# 3. Safe Import Wrapper
# We will try to import the Heavy dependencies. If they fail, we launch ErrorApp immediately.

safe_start = False
err_msg = ""

try:
    import threading
    import sqlite3
    import time
    import re
    import subprocess
    import shlex
    from datetime import datetime
    
    from kivy.core.window import Window
    from kivy.utils import platform
    from kivy.metrics import dp
    from kivy.clock import Clock
    
    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.screenmanager import MDScreenManager
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.floatlayout import MDFloatLayout
    from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFloatingActionButton
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.label import MDLabel
    from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget, OneLineIconListItem
    from kivymd.uix.progressbar import MDProgressBar
    from kivymd.uix.card import MDCard
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
    from kivymd.uix.scrollview import MDScrollView
    from kivymd.toast import toast
    from kivymd.uix.relativelayout import MDRelativeLayout
    from kivy.animation import Animation
    
    # Native Notification Helper for Android 12+
    def init_notification_channel():
        if platform == 'android':
            try:
                from jnius import autoclass
                Build = autoclass('android.os.Build$VERSION')
                if Build.SDK_INT < 26: return
                
                Context = autoclass('android.content.Context')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                channel_id = "download_channel"
                
                NotificationChannel = autoclass('android.app.NotificationChannel')
                NotificationManager = autoclass('android.app.NotificationManager')
                
                importance = NotificationManager.IMPORTANCE_HIGH
                channel = NotificationChannel(channel_id, "Downloads", importance)
                channel.setDescription("Download progress notifications")
                
                notification_manager = activity.getSystemService(Context.NOTIFICATION_SERVICE)
                notification_manager.createNotificationChannel(channel)
            except Exception as e:
                print(f"Channel Creation Error: {e}")

    def send_notification(title, message, progress=-1, notif_id=1):
        if platform == 'android':
            try:
                from jnius import autoclass
                Context = autoclass('android.content.Context')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                channel_id = "download_channel"
                
                # Ensure context is valid
                if not activity:
                    print("Notification Error: No Activity Context")
                    return

                # Use Native Builder (API 26+)
                NotificationBuilder = autoclass('android.app.Notification$Builder')
                builder = NotificationBuilder(activity, channel_id)
                builder.setContentTitle(title)
                builder.setContentText(message)
                builder.setOnlyAlertOnce(True) # Prevent spamming popups on update

                # Icon handling - Use App Icon
                try:
                    app_icon = activity.getApplicationInfo().icon
                    builder.setSmallIcon(app_icon)
                except Exception as e:
                    print(f"Icon Error: {e}")
                    builder.setSmallIcon(17301633) # Fallback
                
                if progress >= 0:
                    builder.setProgress(100, int(progress), False)
                    builder.setOngoing(True)
                else:
                    builder.setProgress(0, 0, False)
                    builder.setAutoCancel(True)
                    builder.setOngoing(False)
                
                # PendingIntent to open app
                try:
                    Intent = autoclass('android.content.Intent')
                    PendingIntent = autoclass('android.app.PendingIntent')
                    intent = Intent(activity, PythonActivity)
                    intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                    FLAG_IMMUTABLE = 67108864 # PendingIntent.FLAG_IMMUTABLE
                    pending_intent = PendingIntent.getActivity(activity, 0, intent, FLAG_IMMUTABLE)
                    builder.setContentIntent(pending_intent)
                except Exception as e:
                    print(f"PendingIntent Error: {e}")
                
                notification_service = activity.getSystemService(Context.NOTIFICATION_SERVICE)
                notification_service.notify(notif_id, builder.build())
            except Exception as e:
                print(f"Notification Error: {e}")
                import traceback
                traceback.print_exc()

    def share_file_native(filepath):
        if platform == 'android':
            android_intent_logic(filepath, "ACTION_SEND")
        else:
            toast(f"Sharing {filepath}")

    def open_file_native(filepath):
        if platform == 'android':
            android_intent_logic(filepath, "ACTION_VIEW")
        else:
            toast(f"Opening {filepath}")

    def android_intent_logic(filepath, action_type):
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            activity = PythonActivity.mActivity
            
            myfile = File(filepath)
            if not myfile.exists():
                toast("File not found")
                return

            Build = autoclass('android.os.Build$VERSION')
            sdk_version = Build.SDK_INT
            uri = None

            # Fallback chain for URI
            if sdk_version >= 24:
                try:
                    FileProvider = autoclass('androidx.core.content.FileProvider')
                    authority = f"{activity.getPackageName()}.fileprovider"
                    uri = FileProvider.getUriForFile(activity, authority, myfile)
                except: pass

            if uri is None:
                try:
                    StrictMode = autoclass('android.os.StrictMode')
                    VmPolicyBuilder = autoclass('android.os.StrictMode$VmPolicy$Builder')
                    StrictMode.setVmPolicy(VmPolicyBuilder().build())
                    uri = Uri.fromFile(myfile)
                except: pass

            action = Intent.ACTION_SEND if action_type == "ACTION_SEND" else Intent.ACTION_VIEW
            intent = Intent(action)
            
            if action_type == "ACTION_SEND":
                intent.setType("*/*")
                intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', uri))
            else:
                MimeTypeMap = autoclass('android.webkit.MimeTypeMap')
                ext = filepath.split('.')[-1].lower()
                mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext) or "*/*"
                intent.setDataAndType(uri, mime)
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            
            # Refined createChooser with explicit casting
            String = autoclass('java.lang.String')
            title = String("Share" if action_type == "ACTION_SEND" else "Open with")
            chooser = Intent.createChooser(cast('android.content.Intent', intent), cast('java.lang.CharSequence', title))
            activity.startActivity(chooser)
        except Exception as e:
            toast(f"Error: {e}")

    # Fix SSL on Android
    import certifi
    try:
        os.environ['SSL_CERT_FILE'] = certifi.where()
    except: pass

    safe_start = True

except Exception:
    safe_start = False
    err_msg = traceback.format_exc()


# 4. Define App Classes ONLY if safe_start is True
if safe_start:
    Window.softinput_mode = "below_target"
    
    # Needs to be imported inside safe block or global
    from kivymd.uix.list import IRightBodyTouch

    # --- Database Manager ---
    class DBManager:
        def __init__(self, db_path):
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_table()

        def create_table(self):
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    status TEXT, -- Pending, Downloading, Paused, Completed, Error
                    progress INTEGER DEFAULT 0,
                    file_path TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()

        def add_task(self, url):
            self.cursor.execute('INSERT INTO downloads (url, status, progress) VALUES (?, ?, ?)', (url, 'Pending', 0))
            self.conn.commit()
            return self.cursor.lastrowid

        def update_status(self, task_id, status, progress=None):
            if progress is not None:
                self.cursor.execute('UPDATE downloads SET status = ?, progress = ? WHERE id = ?', (status, progress, task_id))
            else:
                self.cursor.execute('UPDATE downloads SET status = ? WHERE id = ?', (status, task_id))
            self.conn.commit()

        def update_file_path(self, task_id, path, title):
            self.cursor.execute('UPDATE downloads SET file_path = ?, title = ? WHERE id = ?', (path, title, task_id))
            self.conn.commit()

        def get_tasks(self, status_filter=None):
            if isinstance(status_filter, list):
                 placeholders = ','.join('?' for _ in status_filter)
                 query = f'SELECT * FROM downloads WHERE status IN ({placeholders}) ORDER BY timestamp DESC'
                 self.cursor.execute(query, status_filter)
            elif status_filter:
                self.cursor.execute('SELECT * FROM downloads WHERE status = ? ORDER BY timestamp DESC', (status_filter,))
            else:
                self.cursor.execute('SELECT * FROM downloads ORDER BY timestamp DESC')
            return self.cursor.fetchall()

        def delete_task(self, task_id):
            self.cursor.execute('DELETE FROM downloads WHERE id = ?', (task_id,))
            self.conn.commit()
        
        def get_task(self, task_id):
            self.cursor.execute('SELECT * FROM downloads WHERE id = ?', (task_id,))
            return self.cursor.fetchone()

    # --- Download Manager (Centralized Thread Management) ---
    class DownloadManager:
        def __init__(self):
            self.threads = {} # task_id: thread
            self.stop_events = {} # task_id: event

        def start_download(self, task_id, url, on_progress, on_complete, on_error):
            if task_id in self.threads and self.threads[task_id].is_alive():
                return

            stop_event = threading.Event()
            self.stop_events[task_id] = stop_event
            
            thread = threading.Thread(
                target=self._run_download,
                args=(task_id, url, stop_event, on_progress, on_complete, on_error),
                daemon=True
            )
            self.threads[task_id] = thread
            thread.start()
            
            # WAKE LOCK START
            curr_app = MDApp.get_running_app()
            if curr_app:
                curr_app.acquire_wakelock()

        def stop_download(self, task_id):
            if task_id in self.stop_events:
                self.stop_events[task_id].set()
                # We don't necessarily join here to avoid blocking UI, 
                # the thread will exit on its own check.

        def is_running(self, task_id):
            return task_id in self.threads and self.threads[task_id].is_alive()
        
        def check_active_count(self):
            # Check if any threads are still alive
            active = 0
            for t in self.threads.values():
                if t.is_alive():
                    active += 1
            return active

        def _run_download(self, task_id, url, stop_event, on_progress, on_complete, on_error):
            folder = get_download_folder()
            os.makedirs(folder, exist_ok=True)
            
            import yt_dlp
            
            class MyLogger:
                def debug(self, msg): pass
                def info(self, msg): print(f"yt-dlp: {msg}")
                def warning(self, msg): print(f"yt-dlp Warning: {msg}")
                def error(self, msg): print(f"yt-dlp Error: {msg}")

            def progress_hook(d):
                if stop_event.is_set():
                    raise Exception("Download Cancelled")
                
                if d['status'] == 'downloading':
                    p_str = d.get('_percent_str', '0%').strip().replace('%', '')
                    try: val = float(p_str)
                    except: val = 0.0
                    
                    speed = d.get('_speed_str', 'Busy...').strip()
                    # Only update DB periodically to avoid overhead
                    if int(val) % 5 == 0:
                         db.update_status(task_id, "Downloading", val)
                         if platform == 'android':
                             try:
                                 # Try to parse filename from hook
                                 fname = d.get('filename', '')
                                 if fname: fname = os.path.basename(fname)
                                 display_title = fname if fname else "Downloading..."
                                 send_notification(display_title, f"{int(val)}% - {speed}", val, task_id)
                             except: pass
                             
                         Clock.schedule_once(lambda dt: on_progress(val, speed))
                
                elif d['status'] == 'finished':
                    # This hook is called when the download of a component is finished
                    pass

            ydl_opts = {
                'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'logger': MyLogger(),
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'quiet': True,
                'no_color': True,
            }

            try:
                if platform == 'android':
                    try: send_notification("Download Started", url[:30] + "...", 0, task_id)
                    except: pass

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        filepath = ydl.prepare_filename(info)
                        final_title = info.get('title', os.path.basename(filepath))
                        db.update_status(task_id, "Completed", 100)
                        db.update_file_path(task_id, filepath, final_title)
                        Clock.schedule_once(lambda dt: on_complete(filepath, final_title))
                        
                        # Check wakelock release
                        curr_app = MDApp.get_running_app()
                        if curr_app and dm.check_active_count() <= 1: # This one is about to finish
                             curr_app.release_wakelock()
                        
                        if platform == 'android':
                            try: send_notification("Download Complete", final_title, -1, task_id)
                            except: pass
                    else:
                        raise Exception("No info extracted")

            except Exception as e:
                err_str = str(e)
                if "Download Cancelled" in err_str:
                    print(f"Task {task_id} stopped by user")
                    db.update_status(task_id, "Paused")
                    if platform == 'android':
                        try: send_notification("Download Paused", "Tap to resume in app", -1, task_id)
                        except: pass
                else:
                    print(f"Task {task_id} Error: {e}")
                    db.update_status(task_id, "Error")
                    Clock.schedule_once(lambda dt: on_error(err_str))
                    if platform == 'android':
                        try: send_notification("Download Failed", "Tap to retry", -1, task_id)
                        except: pass

                # Check wakelock release on error too
                curr_app = MDApp.get_running_app()
                if curr_app and dm.check_active_count() <= 1:
                        curr_app.release_wakelock()

    # --- Config & Helpers ---
    db = None
    dm = DownloadManager()

    def get_db_path():
        if platform == 'android':
            app = MDApp.get_running_app()
            if app:
                try:
                    path = os.path.join(app.user_data_dir, 'downloads.db')
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    return path
                except:
                    pass
        return 'downloads.db'

    def get_download_folder():
        if platform == 'android':
            try:
                from jnius import autoclass
                Environment = autoclass('android.os.Environment')
                Context = autoclass('org.kivy.android.PythonActivity').mActivity
                
                # Check if storage is mounted
                state = Environment.getExternalStorageState()
                if not state == Environment.MEDIA_MOUNTED:
                    return Context.getExternalFilesDir(None).getAbsolutePath()

                try:
                    # Preferred: Use standard Download directory via Environment
                    download_dir = Environment.getExternalStoragePublicDirectory(
                        Environment.DIRECTORY_DOWNLOADS
                    ).getAbsolutePath()
                except Exception:
                    # Fallback 1: Direct public path
                    download_dir = "/sdcard/Download"
                
                # Ensure our subfolder exists - with robustness
                try:
                    os.makedirs(download_dir, exist_ok=True)
                except:
                    pass

                final_path = os.path.join(download_dir, "downloads")
                os.makedirs(final_path, exist_ok=True)
                return final_path
                
            except Exception as e:
                print(f"Error getting download folder: {e}")
                app = MDApp.get_running_app()
                if app: return app.user_data_dir
                return '/sdcard/Download'
        return os.path.join(os.getcwd(), 'downloads')
    

    # --- UI Components ---
    class DownloadCard(MDCard):
        def __init__(self, task_id, url, title, status, progress, speed="", **kwargs):
            super().__init__(**kwargs)
            self.task_id = task_id
            self.url = url
            self.orientation = "vertical"
            self.padding = dp(15) # Increased padding
            self.spacing = dp(5)
            self.size_hint_y = None
            self.height = dp(130) # Increased height for speed
            self.elevation = 2
            self.radius = [15]
            self.line_color = (0.2, 0.2, 0.2, 0.1)

            display_text = title if title else url
            if len(display_text) > 40: display_text = display_text[:37] + "..."
            
            # Title
            title_box = MDBoxLayout(size_hint_y=None, height=dp(30))
            title_box.add_widget(MDLabel(text=display_text, font_style="Subtitle2", theme_text_color="Primary"))
            self.add_widget(title_box)
            
            # Status & Speed row
            stat_box = MDBoxLayout(size_hint_y=None, height=dp(20))
            self.status_label = MDLabel(text=f"{status} • {int(progress)}%", font_style="Caption", theme_text_color="Secondary")
            self.speed_label = MDLabel(text=speed, font_style="Caption", theme_text_color="Hint", halign="right")
            stat_box.add_widget(self.status_label)
            stat_box.add_widget(self.speed_label)
            self.add_widget(stat_box)

            # Progress
            self.progress_bar = MDProgressBar(value=progress, size_hint_y=None, height=dp(8))
            self.add_widget(self.progress_bar)
            
            # Spacer
            self.add_widget(MDLabel(size_hint_y=None, height=dp(5)))

            # Controls
            controls = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(10))
            
            curr_app = MDApp.get_running_app()
            self.action_btn = MDIconButton(icon="pause" if status == "Downloading" else "play", theme_text_color="Custom", text_color=curr_app.theme_cls.primary_color if curr_app else (0, 0.5, 0.5, 1))
            self.action_btn.bind(on_release=self.toggle_download)
            
            cancel_btn = MDIconButton(icon="close", theme_text_color="Error")
            cancel_btn.bind(on_release=self.cancel_download)

            controls.add_widget(MDBoxLayout()) # Spacer
            controls.add_widget(self.action_btn)
            controls.add_widget(cancel_btn)
            
            self.add_widget(controls)
            
            # Additional Controls Row (Copy)
            copy_btn = MDIconButton(icon="content-copy", theme_text_color="Hint", icon_size="20sp")
            copy_btn.bind(on_release=self.copy_url)
            controls.add_widget(copy_btn)

        def copy_url(self, instance):
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.url)
            toast("URL Copied")

        def update_view(self, status, progress, speed_str="", title=None):
            self.status_label.text = f"{status} • {int(progress)}%"
            if speed_str:
                self.speed_label.text = speed_str
            self.progress_bar.value = progress
            if title:
                # Update title if we learned it (e.g. from yt-dlp)
                # We need to find the label in title_box
                for child in self.children:
                    if isinstance(child, MDBoxLayout) and len(child.children) > 0 and isinstance(child.children[0], MDLabel):
                         # Note: children order might be reversed in Kivy layout logic, but let's just find the label
                         pass 
                # Simpler: just reload list if title changes or assume user doesn't strictly need real-time title update on card until refresh
                pass
            
            # Update action button based on manager state
            if dm.is_running(self.task_id):
                self.action_btn.icon = "pause"
            else:
                self.action_btn.icon = "play"

        def toggle_download(self, instance):
            if dm.is_running(self.task_id):
                dm.stop_download(self.task_id)
                self.update_view("Paused", self.progress_bar.value)
                toast("Pausing...")
            else:
                self.start_download()

        def cancel_download(self, instance):
            dm.stop_download(self.task_id)
            db.delete_task(self.task_id)
            if self.parent:
                self.parent.remove_widget(self)
            toast("Removed")

        def start_download(self):
            task = db.get_task(self.task_id)
            if not task: return
            url = task[1]
            
            self.update_view("Downloading", self.progress_bar.value, "Starting...")
            dm.start_download(
                self.task_id, 
                url, 
                on_progress=self._on_dm_progress,
                on_complete=self._on_dm_complete,
                on_error=self._on_dm_error
            )

        def _on_dm_progress(self, progress, speed):
            self.update_view("Downloading", progress, speed)

        def _on_dm_complete(self, filepath, title):
            self.update_view("Completed", 100, "")
            toast("Download Finished")
            if self.parent:
                self.parent.remove_widget(self)
            
            curr_app = MDApp.get_running_app()
            if curr_app:
                curr_app.refresh_history()

        def _on_dm_error(self, error_msg):
            self.update_view("Error", self.progress_bar.value, "Failed")
            toast(f"Error: {error_msg}")


    # ... (HistoryItem, RightActionContainer stay same) ...
    class HistoryItem(MDCard):
        def __init__(self, task_id, title, filepath, **kwargs):
            super().__init__(**kwargs)
            self.task_id = task_id
            self.filepath = filepath
            self.title = title
            
            self.orientation = "horizontal"
            self.padding = dp(15)
            self.spacing = dp(12)
            self.size_hint_y = None
            self.height = dp(90)
            self.elevation = 2
            self.radius = [15]
            self.md_bg_color = (0.12, 0.12, 0.15, 1)
            self.line_color = (0.2, 0.7, 0.8, 0.2)
            self.line_width = 1
            
            # File icon with background
            icon_container = MDRelativeLayout(size_hint=(None, None), size=(dp(50), dp(50)))
            icon_bg = MDCard(
                md_bg_color=(0.2, 0.7, 0.8, 0.2),
                radius=[12],
                size_hint=(1, 1)
            )
            icon = MDIconButton(
                icon="file-check-outline",
                theme_text_color="Custom",
                text_color=(0.2, 0.7, 0.8, 1),
                disabled=True,
                icon_size="28sp",
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            icon_container.add_widget(icon_bg)
            icon_container.add_widget(icon)
            self.add_widget(icon_container)
            
            # Text Info
            text_box = MDBoxLayout(orientation="vertical", spacing=dp(4))
            title_label = MDLabel(
                text=title,
                font_style="Subtitle2",
                theme_text_color="Primary",
                bold=True,
                shorten=True,
                shorten_from="right"
            )
            path_label = MDLabel(
                text=filepath,
                font_style="Caption",
                theme_text_color="Hint",
                shorten=True,
                shorten_from="right"
            )
            text_box.add_widget(title_label)
            text_box.add_widget(path_label)
            self.add_widget(text_box)
            
            # Actions - Fixed width issue by using adaptive_width
            actions = MDBoxLayout(
                orientation="horizontal", 
                adaptive_width=True, 
                spacing=dp(4),
                pos_hint={"center_y": .5}
            )
            
            open_btn = MDIconButton(
                icon="open-in-new", 
                theme_text_color="Custom", 
                text_color=app.theme_cls.primary_color,
                icon_size="24sp",
                size_hint=(None, None),
                size=(dp(48), dp(48)),
            )
            open_btn.bind(on_release=self.open_file)
            
            share_btn = MDIconButton(
                icon="share-variant-outline", 
                theme_text_color="Custom", 
                text_color=(0.2, 0.7, 1, 1),
                icon_size="24sp",
                size_hint=(None, None),
                size=(dp(48), dp(48)),
            )
            share_btn.bind(on_release=self.share_file)
            
            del_btn = MDIconButton(
                icon="delete-outline", 
                theme_text_color="Custom", 
                text_color=(1, 0.3, 0.3, 1),
                icon_size="24sp",
                size_hint=(None, None),
                size=(dp(48), dp(48)),
            )
            del_btn.bind(on_release=self.confirm_delete)
            
            actions.add_widget(open_btn)
            actions.add_widget(share_btn)
            actions.add_widget(del_btn)
            self.add_widget(actions)
            
            # Entrance animation
            self.opacity = 0
            anim = Animation(opacity=1, duration=0.3)
            anim.start(self)

        def open_file(self, instance):
            open_file_native(self.filepath)

        def share_file(self, instance):
            share_file_native(self.filepath)
        
        def confirm_delete(self, instance):
            from kivymd.uix.button import MDFlatButton
            self.dialog = MDDialog(
                title="Delete File?",
                text=f"Are you sure you want to delete '{self.title}'?\nThis will remove it from history and storage.",
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                    MDRaisedButton(text="DELETE", md_bg_color=(0.9, 0.1, 0.1, 1), on_release=self.delete_file),
                ],
            )
            self.dialog.open()

        def delete_file(self, instance):
            abs_path = os.path.abspath(self.filepath)
            print(f"DEBUG: Attempting to delete file at: {abs_path}")
            
            if hasattr(self, 'dialog') and self.dialog:
                self.dialog.dismiss()
            
            # 1. Delete from Database
            try:
                db.delete_task(self.task_id)
                db_deleted = True
            except Exception as e:
                print(f"DB Delete Error: {e}")
                db_deleted = False

            # 2. Delete Physical File
            file_deleted = False
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                    file_deleted = True
                except Exception as e:
                    print(f"OS Remove Error: {e}")
                    # Try Android specific if on platform
                    if platform == 'android':
                        try:
                            from jnius import autoclass
                            File = autoclass('java.io.File')
                            f = File(abs_path)
                            if f.delete():
                                file_deleted = True
                        except: pass
            
            # 3. Final Feedback
            if db_deleted and file_deleted:
                toast("Deleted from History and Storage")
            elif db_deleted:
                if os.path.exists(abs_path):
                    toast("History record removed but file deletion failed (Permission?)")
                else:
                    toast("History record removed (File was already missing)")
            else:
                toast("Failed to delete record from database")

            if self.parent:
                self.parent.remove_widget(self)

    class StartupScreen(MDScreen):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.md_bg_color = (1, 1, 1, 1) # Pure white
            
            layout = MDFloatLayout()
            # Actual App Icon
            logo = Image(
                source="assets/icon.png",
                size_hint=(None, None),
                size=(dp(120), dp(120)),
                pos_hint={"center_x": .5, "center_y": .6}
            )
            label = MDLabel(
                text="Downloads",
                halign="center",
                font_style="H4",
                bold=True,
                pos_hint={"center_x": .5, "center_y": .4},
                theme_text_color="Custom",
                text_color=(0.1, 0.5, 0.6, 1)
            )
            layout.add_widget(logo)
            layout.add_widget(label)
            self.add_widget(layout)

    class DownloadsApp(MDApp):
        def build(self):
            global db
            global app 
            app = self
            self.theme_cls.primary_palette = "Teal"
            self.theme_cls.theme_style = "Dark"
            
            try:
                db_path = get_db_path()
                db = DBManager(db_path)
            except Exception as e:
                return ErrorApp(f"DB Init Error: {e}").build()

            self.sm = MDScreenManager()
            
            # --- Splash Screen ---
            self.sm.add_widget(StartupScreen(name="startup"))
            
            # --- Main Screen ---
            main_screen = MDScreen(name="main")
            self.root_nav = MDBottomNavigation(text_color_active="white")
            
            # --- Screen 1: Home ---
            screen1 = MDBottomNavigationItem(name='screen1', text='Home', icon='home', on_tab_press=self.refresh_active)
            main_layout = MDBoxLayout(orientation='vertical', spacing=dp(15), padding=dp(15))
            
            # Input Card (Improved Padding)
            input_card = MDCard(orientation="vertical", padding=dp(20), spacing=dp(15), size_hint_y=None, height=dp(160), elevation=4, radius=[20])
            
            input_card.add_widget(MDLabel(text="Add New Download", font_style="H6", theme_text_color="Primary", bold=True))
            self.url_input = MDTextField(hint_text="Paste Link Here", mode="fill", icon_right="link", radius=[10,10,0,0])
            input_card.add_widget(self.url_input)
            
            add_btn = MDRaisedButton(text="DOWNLOAD", size_hint_x=1, elevation=2, font_size='16sp', on_release=self.add_download)
            input_card.add_widget(add_btn)
            
            main_layout.add_widget(input_card)
            
            # Active Header
            main_layout.add_widget(MDLabel(text="Active Downloads", font_style="H6", size_hint_y=None, height=dp(30), theme_text_color="Secondary"))
            
            self.active_scroll = MDScrollView()
            self.active_list = MDBoxLayout(orientation='vertical', spacing=dp(15), padding=[0, dp(5), 0, dp(15)], adaptive_height=True)
            self.active_scroll.add_widget(self.active_list)
            main_layout.add_widget(self.active_scroll)
            screen1.add_widget(main_layout)

            # --- Screen 2: Files ---
            screen2 = MDBottomNavigationItem(name='screen2', text='Files', icon='folder-multiple', on_tab_press=self.refresh_history)
            history_layout = MDBoxLayout(orientation='vertical')
            
            # History Toolbar with Clear All
            toolbar = MDBoxLayout(size_hint_y=None, height=dp(60), padding=dp(15), md_bg_color=(0.1,0.1,0.1,1))
            toolbar.add_widget(MDLabel(text="Downloaded Files", font_style="H6", theme_text_color="Primary", bold=True))
            
            clear_btn = MDIconButton(icon="delete-sweep", theme_text_color="Error", on_release=self.clear_all_history)
            toolbar.add_widget(clear_btn)
            
            history_layout.add_widget(toolbar)
            
            self.history_scroll = MDScrollView()
            self.history_list = MDBoxLayout(orientation='vertical', spacing=dp(12), padding=[dp(15), dp(5), dp(15), dp(20)], adaptive_height=True)
            self.history_scroll.add_widget(self.history_list)
            history_layout.add_widget(self.history_scroll)
            screen2.add_widget(history_layout)

            self.root_nav.add_widget(screen1)
            self.root_nav.add_widget(screen2)
            
            main_screen.add_widget(self.root_nav)
            self.sm.add_widget(main_screen)
            
            # Switch to main UI after 2.5 seconds
            Clock.schedule_once(self.switch_to_main, 2.5)
            
            return self.sm

        def switch_to_main(self, dt):
            self.sm.current = "main"
            
        def clear_all_history(self, instance):
            try:
                db.cursor.execute("DELETE FROM downloads WHERE status='Completed'")
                db.conn.commit()
                self.refresh_history()
                toast("History Cleared")
            except Exception as e:
                toast(f"Error: {e}")


        # ... (on_start, add_download, refresh_active stay same or similiar) ...
        def on_start(self):
            if platform == 'android':
                init_notification_channel()
                from android.permissions import request_permissions, Permission
                # Request permissions using strings to avoid missing Permission.POST_NOTIFICATIONS on older kivy versions
                perms = [
                     Permission.WRITE_EXTERNAL_STORAGE, 
                     Permission.READ_EXTERNAL_STORAGE, 
                     Permission.WAKE_LOCK,
                     'android.permission.POST_NOTIFICATIONS'
                ]
                request_permissions(perms)
            try:
                self.refresh_active()
                # Check for zombie tasks (Downloads that were 'Downloading' but app was killed)
                Clock.schedule_once(self.check_zombie_tasks, 1)
            except Exception as e:
                toast(f"Error: {e}")

        def on_pause(self):
            return True # Allow pause

        def on_resume(self):
            try:
                self.refresh_active()
                self.check_zombie_tasks(0)
            except Exception as e:
                print(e)
        
        def check_zombie_tasks(self, dt):
            # Recovery Logic
            try:
                tasks = db.get_tasks(['Downloading'])
                for task in tasks:
                    t_id, url, title, status, progress, path, ts = task
                    # If it says 'Downloading' in DB but NOT running in DM, it's a zombie
                    if not dm.is_running(t_id):
                        print(f"Found Zombie Task: {t_id} {url}")
                        # Option 1: Auto-Restart
                        card_found = False
                        for widget in self.active_list.children:
                            if isinstance(widget, DownloadCard) and widget.task_id == t_id:
                                widget.start_download()
                                card_found = True
                                break
                        
                        # If card was not in list (maybe refresh didn't happen yet?), try force update status
                        if not card_found:
                            # Set to paused so user can manual restart, OR auto restart
                            # Let's set it to 'Error/Interrupted' so user knows
                            db.update_status(t_id, "Paused") 
                            self.refresh_active()
            except Exception as e:
                print(f"Zombie Check Error: {e}")

        # --- WakeLock ---
        wakelock = None
        def acquire_wakelock(self):
            if platform == 'android':
                if self.wakelock:
                    return # Already has it
                try:
                    from jnius import autoclass
                    Context = autoclass('android.content.Context')
                    PowerManager = autoclass('android.os.PowerManager')
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    activity = PythonActivity.mActivity
                    pm = activity.getSystemService(Context.POWER_SERVICE)
                    self.wakelock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "DownloadsApp:WakeLock")
                    self.wakelock.acquire()
                    print("WakeLock Acquired")
                except Exception as e:
                    print(f"WakeLock Error: {e}")

        def release_wakelock(self):
            if platform == 'android' and self.wakelock:
                try:
                    if self.wakelock.isHeld():
                        self.wakelock.release()
                        self.wakelock = None
                        print("WakeLock Released")
                except Exception as e:
                    print(f"WakeLock Release Error: {e}")

        def add_download(self, instance):
            url = self.url_input.text.strip()
            if not url: 
                toast("Please enter a URL")
                return
            
            # --- URL Validation ---
            # Accept only http/https. Reject magnets and .torrent
            if not (url.startswith("http://") or url.startswith("https://")):
                toast("Invalid URL: Only HTTP/HTTPS supported")
                return
                
            if url.startswith("magnet:") or url.lower().endswith(".torrent"):
                toast("Torrent links are not supported")
                return

            try:
                task_id = db.add_task(url)
                self.url_input.text = ""
                self.refresh_active()
                toast("Added to downloads")
            except Exception as e:
                toast(f"Error: {e}")

        def refresh_active(self, *args):
            try:
                self.active_list.clear_widgets()
                tasks = db.get_tasks(['Pending', 'Downloading', 'Paused', 'Error'])
                if not tasks:
                    self.active_list.add_widget(MDLabel(text="No active downloads", halign="center", theme_text_color="Hint"))
                    return
                for task in tasks:
                    t_id, url, title, status, progress, path, ts = task
                    card = DownloadCard(t_id, url, title, status, progress) # Speed is empty initially
                    self.active_list.add_widget(card)
                    if status == 'Pending': card.start_download()
            except Exception as e:
                print(e)
                
        def refresh_history(self, *args):
            try:
                self.history_list.clear_widgets()
                tasks = db.get_tasks('Completed')
                if not tasks:
                    empty_state = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(30), size_hint_y=None, height=dp(200))
                    empty_icon = MDIconButton(icon="folder-open-outline", theme_text_color="Hint", disabled=True, icon_size="64sp", pos_hint={'center_x': 0.5})
                    empty_label = MDLabel(text="No downloads yet", halign="center", theme_text_color="Hint", font_style="Subtitle1")
                    empty_state.add_widget(empty_icon)
                    empty_state.add_widget(empty_label)
                    self.history_list.add_widget(empty_state)
                    return
                
                for task in tasks:
                    t_id, url, title, status, progress, path, ts = task
                    display_text = title if title else url
                    display_path = path if path else "Unknown"
                    item = HistoryItem(t_id, display_text, display_path)
                    self.history_list.add_widget(item)
            except Exception as e:
                print(e)
                toast(f"History Error: {e}")



# 5. Main Execution
if __name__ == '__main__':
    if safe_start:
        try:
            DownloadsApp().run()
        except Exception:
            ErrorApp(traceback.format_exc()).run()
    else:
        # If imports failed, run ErrorApp with the import error
        ErrorApp(err_msg).run()
