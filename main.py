# ✅ CONFIG FIRST (before importing Kivy)
from kivy import Config
Config.set('graphics', 'multisamples', '0')  # Disable multisampling for better mobile performance
Config.set('kivy', 'exit_on_escape', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# ✅ MAIN LIBRARIES
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen

# ✅ UI Components
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDTimePicker, MDDatePicker
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import (
    OneLineAvatarIconListItem, TwoLineAvatarIconListItem,
    OneLineListItem, TwoLineListItem, ThreeLineListItem
)
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.spinner import MDSpinner
from kivy.uix.modalview import ModalView

# ✅ PROPERTIES
from kivy.properties import (
    StringProperty, BooleanProperty, ObjectProperty,
    NumericProperty
)

# ✅ TOOLS & UTILS
from kivy.metrics import dp
from kivy.utils import get_color_from_hex, platform
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.animation import Animation

# ✅ SYSTEM / EXTERNAL
import os
import json
import random
import warnings
import sqlite3
from datetime import datetime, timedelta
from plyer import notification, filechooser
from PIL import Image as PILImage

# ✅ WARNINGS
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ✅ CONSTANTS
DATA_FILE = os.path.join(os.path.dirname(__file__), "study_buddy.json")
Window.size = (360, 640)  # Mobile screen emulation (remove if not needed)

import threading

_data_cache = {}
_data_lock = threading.Lock()

def load_data(use_cache=False):
    """
    Safely loads app data from JSON. Optionally uses cached data for performance.
    """
    global _data_cache

    if use_cache and _data_cache:
        return _data_cache

    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            default_data = {
                "schedules": [],
                "tasks": [],
                "profile": {
                    "name": "",
                    "title": "",
                    "avatar_path": "data/logo/kivy-icon-256.png"
                },
                "settings": {
                    "notifications_enabled": True,
                    "theme": "Light",
                    "primary_color": "Indigo"
                },
                "motivation": {
                    "last_studied": "",
                    "current_streak": 0,
                    "last_sent_date": "",
                    "time": "09:00"
                }
            }
            save_data(default_data)
            return default_data
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}
    
def save_data(data):
    """
    Safely writes app data to JSON. Updates cache and ensures atomic write.
    """
    global _data_cache

    try:
        with _data_lock:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
                _data_cache = data
    except Exception as e:
        print(f"[ERROR] Failed to save data: {e}")



# Custom Tab class
class Tab(MDFloatLayout, MDTabsBase):
    pass

# Motivational quotes and tips
MOTIVATIONAL_QUOTES = [
    "The secret of getting ahead is getting started. - Mark Twain",
    "You don't have to be great to start, but you have to start to be great. - Zig Ziglar",
    "The expert in anything was once a beginner. - Helen Hayes",
    "Success is the sum of small efforts, repeated day in and day out. - Robert Collier",
    "The only way to learn mathematics is to do mathematics. - Paul Halmos"
]

PRODUCTIVITY_TIPS = [
    "Use the Pomodoro Technique: 25 minutes of focused work, then 5-minute break.",
    "Prioritize your tasks using the Eisenhower Matrix (Urgent/Important).",
    "Break large tasks into smaller, manageable chunks.",
    "Review your notes within 24 hours to improve retention.",
    "Get enough sleep - it's essential for memory consolidation."
]


# Custom Widgets
class CustomListItem(OneLineAvatarIconListItem):
    icon = StringProperty()

class ScheduleCard(MDCard):
    name = StringProperty()
    subject = StringProperty()
    time = StringProperty()
    description = StringProperty()
    has_notification = BooleanProperty(False)
    schedule_data = ObjectProperty()
    is_done = BooleanProperty(False)  # ✅ Completion based on time


class TaskCard(MDCard):
    name = StringProperty()
    due_date = StringProperty()
    description = StringProperty()
    task_type = StringProperty()
    status = StringProperty()
    task_data = ObjectProperty()
    icon = StringProperty()  # ✅ NEW property

    def on_status(self, instance, value):
        self.icon = self.get_status_icon()  # ✅ auto-update icon when status changes

    def get_status_icon(self):
        if self.status == 'Done':
            return 'check-circle'
        elif self.status == 'In Progress':
            return 'progress-check'
        else:
            return 'clock'


class StatusMenuItem(OneLineAvatarIconListItem):
    icon = StringProperty()

class StreakCard(MDCard):
    current_streak = NumericProperty(0)

class StatsTab(MDBoxLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Statistics"  # ✅ Add this line
        self.icon = "chart-bar"


class QuoteTab(MDBoxLayout, MDTabsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Motivation"  # ✅ Add this line

class MainScreen(Screen):
    app_name = StringProperty("Study Planner")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ScheduleScreen(Screen):
    def on_pre_enter(self):
        self.load_schedules()


    def load_schedules(self):
        app = MDApp.get_running_app()

        self.ids.schedule_list.clear_widgets()
        self.ids.week_strip.clear_widgets()

        # Reset scroll to top
        self.ids.schedule_scroll.scroll_y = 1
        Animation.cancel_all(self.ids.schedule_scroll, 'scroll_y')
        Animation(scroll_y=1, duration=0.2, t='out_quad').start(self.ids.schedule_scroll)

        selected_date = getattr(self, "selected_date", datetime.now().strftime("%d-%m-%Y"))
        schedules = [s for s in app.get_all_schedules() if s.get("date") == selected_date]

        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        self.ids.week_range.text = f"{start_of_week.strftime('%B %d')} – {end_of_week.strftime('%d, %Y')}"

        # Build the week strip
        for i in range(7):
            date_obj = start_of_week + timedelta(days=i)
            date_str = date_obj.strftime('%d-%m-%Y')

            box = self.build_day_box(date_obj, selected_date, today, app)
            Clock.schedule_once(lambda dt, b=box, d=date_obj: b.bind(on_touch_down=lambda w, t: self.build_day_box(date_obj, selected_date, today, app)), 0.05)
            box.bind(on_touch_up=lambda widget, touch, d=date_obj: self.on_day_click(widget, touch, d))
            self.ids.week_strip.add_widget(box)

        now = datetime.now()

        # Sort and display today's schedule only
        schedules.sort(key=lambda s: datetime.strptime(s["time"], "%H:%M"))
        
        for schedule in schedules:
            try:
                schedule_datetime = datetime.strptime(
                    f"{schedule['date']} {schedule['time']}", "%d-%m-%Y %H:%M"
                )
                is_done = schedule_datetime < now
            except:
                is_done = False

            item = ScheduleCard(
                name=schedule['name'],
                subject=schedule['subject'],
                time=schedule['time'],
                description=schedule['description'],
                has_notification=schedule['notification'],
                schedule_data=schedule,
                is_done=is_done  # Set completion status for each schedule individually
            )
            item.bind(on_release=lambda x, s=schedule: app.show_schedule_dialog(s))
            self.ids.schedule_list.add_widget(item)


    def build_day_box(self, date_obj, selected_date, today, app):
        date_str = date_obj.strftime('%d-%m-%Y')
        day_label = date_obj.strftime('%a')
        day_number = date_obj.day

        box = MDBoxLayout(orientation="vertical", size_hint_x=None, width=dp(48), spacing="2dp")
        box.radius = [10, 10, 10, 10]

        all_schedules = load_data(use_cache=True).get("schedules", [])
        daily_schedules = [s for s in all_schedules if s.get("date") == date_str]
        total = len(daily_schedules)
        done = 0

        now = datetime.now()
        for s in daily_schedules:
            try:
                t = datetime.strptime(s["time"], "%H:%M").time()
                full_dt = datetime.combine(date_obj.date(), t)
                if full_dt < now:
                    done += 1
            except:
                continue

        progress = int((done / total) * 100) if total else 0
        label_text = f"{done}/{total}" if total else "0/0"


        # ✅ Style based on today/selected
        if date_obj.date() == today.date():
            box.md_bg_color = app.theme_cls.primary_color
        elif date_str == selected_date:
            box.md_bg_color = (app.theme_cls.primary_color[0], app.theme_cls.primary_color[1], app.theme_cls.primary_color[2], 0.5) if app.theme_cls.theme_style == "Dark" else (240/255, 250/255, 1, 1)
            box.line_color = app.theme_cls.primary_color
            box.line_width = dp(1.2)
            box.radius = [10, 10, 10, 10]
        else:
            box.md_bg_color = (240 / 255, 250 / 255, 1, 1)

        # ✅ Add elements to box
        box.add_widget(MDLabel(text=day_label, halign="center", font_style="Caption",
                               theme_text_color="Custom", text_color=(1, 1, 1, 1) if date_obj.date() == today.date() else (0, 0, 0, 1)))
        box.add_widget(MDLabel(text=str(day_number), halign="center", font_style="H6",
                               theme_text_color="Custom", text_color=(1, 1, 1, 1) if date_obj.date() == today.date() else (0, 0, 0, 1)))
        box.add_widget(MDProgressBar(value=progress, color=(34/255, 197/255, 94/255, 1) if progress == 100 else (234/255, 179/255, 8/255, 1),
                                     height="4dp", size_hint_x=0.6, size_hint_y=None, pos_hint={"center_x": 0.5}))
        box.add_widget(MDLabel(text=label_text, halign="center", font_style="Caption",
                               theme_text_color="Custom", text_color=(1, 1, 1, 1) if date_obj.date() == today.date() else (0, 0, 0, 1)))
        return box


    def on_day_click(self, widget, touch, date_obj):
        if widget.collide_point(*touch.pos):
            date_str = date_obj.strftime('%d-%m-%Y')
            if getattr(self, "selected_date", "") == date_str:
                return  # Avoid reloading if same date tapped again

            self.selected_date = date_str
            self.ids.schedule_label.text = (
                "Today's Schedule" if date_obj.date() == datetime.now().date()
                else f"Schedule of {date_obj.strftime('%B %d, %Y, %A')}"
            )

            # 🟡 Defer actual loading to avoid UI freeze
            Clock.schedule_once(lambda dt: self.load_schedules(), 0.05)



    def go_back(self):
        self.manager.current = "main_screen"
        self.manager.transition.direction = "right"

    def add_schedule(self):
        self.manager.current = "add_schedule_screen"
        self.manager.transition.direction = "left"

    def set_selected_date(self, date_obj):
        self.selected_date = date_obj.strftime("%d-%m-%Y")
        self.load_schedules()


class TasksScreen(Screen):
    def on_pre_enter(self):
        self.refresh_screen()

    def refresh_screen(self):
        self.load_tasks()

    def load_tasks(self):
        app = MDApp.get_running_app()

        self.ids.daily_tasks.clear_widgets()
        self.ids.weekly_tasks.clear_widgets()
        self.ids.monthly_tasks.clear_widgets()

        tasks = app.get_all_tasks()

        for task in tasks:
            item = TaskCard(
                name=task['name'],
                due_date=task['due_date'],
                description=task['description'],
                task_type=task['task_type'],
                status=task['status'],
                task_data=task,
                icon=self.get_icon_for_status(task['status']),
            )
            item.bind(on_release=lambda x, t=task: app.show_task_dialog(t))

            self.add_task_to_section(item, task['task_type'])

    def update_task_lists(self):
        self.ids.daily_tasks.clear_widgets()
        self.ids.weekly_tasks.clear_widgets()
        self.ids.monthly_tasks.clear_widgets()

        app = MDApp.get_running_app()
        tasks = app.get_all_tasks()

        for task in tasks:
            item = TaskCard(
                name=task['name'],
                due_date=task['due_date'],
                description=task['description'],
                task_type=task['task_type'],
                status=task['status'],
                task_data=task,
                icon=self.get_icon_for_status(task['status']),
            )
            item.bind(on_release=lambda x, t=task: app.show_task_dialog(t))
            self.add_task_to_section(item, task['task_type'])

    def add_task_to_section(self, item, task_type):
        if task_type == "Daily":
            self.ids.daily_tasks.add_widget(item)
        elif task_type == "Weekly":
            self.ids.weekly_tasks.add_widget(item)
        elif task_type == "Monthly":
            self.ids.monthly_tasks.add_widget(item)

    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        self.update_task_lists()

    def get_icon_for_status(self, status):
        if status == 'Done':
            return 'check-circle'
        elif status == 'In Progress':
            return 'progress-check'
        else:
            return 'clock'

    def go_back(self):
        self.manager.current = "main_screen"
        self.manager.transition.direction = "right"

    def add_task(self):
        self.manager.current = "add_task_screen"
        self.manager.transition.direction = "left"


class AddScheduleScreen(Screen):
    def on_pre_enter(self):
        self.refresh_screen()

    def refresh_screen(self):
        self.ids.schedule_name.text = ""
        self.ids.schedule_subject.text = ""
        self.ids.schedule_desc.text = ""
        self.ids.schedule_time.text = ""
        self.ids.schedule_day.text = ""
        self.ids.notification_toggle.active = True
        self.week_dates = self.get_week_dates()

    def get_week_dates(self):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return [(start_of_week + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(7)]

    def show_day_menu(self):
        today = datetime.now().date()
        items = []

        for date_str in self.week_dates:
            date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
            if date_obj < today:
                continue

            day_name = date_obj.strftime('%A')
            display_text = (
                f"Today ({day_name})" if date_obj == today else
                f"Tomorrow ({day_name})" if date_obj == today + timedelta(days=1) else
                f"{date_obj.strftime('%b %d')} ({day_name})"
            )

            items.append({
                "text": display_text,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=date_str: self.set_day(x)
            })

        if not items:
            items.append({
                "text": "Today",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=self.week_dates[0]: self.set_day(x)
            })

        self.day_menu = MDDropdownMenu(
            caller=self.ids.schedule_day,
            items=items,
            position="bottom",
            width_mult=4,
            max_height=dp(200),
            ver_growth="down",
        )
        self.day_menu.open()

    def set_day(self, date_str):
        date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
        today = datetime.now().date()

        display_text = (
            "Today" if date_obj == today else
            "Tomorrow" if date_obj == today + timedelta(days=1) else
            date_obj.strftime('%b %d (%A)')
        )

        self.ids.schedule_day.text = display_text
        self.selected_date = date_str
        self.day_menu.dismiss()

    def show_time_picker(self):
        picker = MDTimePicker()
        picker.bind(time=self.set_time)
        picker.open()

    def set_time(self, instance, time):
        self.ids.schedule_time.text = time.strftime("%H:%M")

    def save_schedule(self):
        name = self.ids.schedule_name.text
        subject = self.ids.schedule_subject.text
        desc = self.ids.schedule_desc.text
        time = self.ids.schedule_time.text
        notification = self.ids.notification_toggle.active

        if not name or not subject or not time or not hasattr(self, 'selected_date'):
            self.show_error_dialog("Please fill all required fields including date")
            return

        if len(desc) > 150:
            self.show_error_dialog("Description cannot exceed 150 characters")
            return

        app = MDApp.get_running_app()
        schedule = {
            "name": name,
            "subject": subject,
            "description": desc,
            "time": time,
            "notification": notification,
            "date": self.selected_date
        }
        app.add_schedule(schedule)

        if notification:
            self.schedule_notification(name, time, self.selected_date)

        self.show_success_dialog("Schedule added successfully!")
        self.go_back()

    def schedule_notification(self, name, time_str, date_str):
        try:
            notify_time = datetime.combine(
                datetime.strptime(date_str, "%d-%m-%Y").date(),
                datetime.strptime(time_str, "%H:%M").time()
            )
            now = datetime.now()
            if notify_time < now:
                return
            seconds = (notify_time - now).total_seconds()
            Clock.schedule_once(lambda dt: self.send_notification(name), seconds)
        except Exception as e:
            print(f"Error scheduling notification: {e}")

    def send_notification(self, name):
        notification.notify(
            title="Study Planner Reminder",
            message=f"It's time for: {name}",
            app_name="Study Planner"
        )

    def show_error_dialog(self, text):
        dialog = MDDialog(
            title="[color=ff3333]Error[/color]",
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_success_dialog(self, text):
        dialog = MDDialog(
            title="[color=4CAF50]Success[/color]",
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def go_back(self):
        self.manager.current = "schedule_screen"
        self.manager.transition.direction = "right"


class AddTaskScreen(Screen):
    def on_pre_enter(self):
        self.refresh_screen()

    def refresh_screen(self):
        self.ids.task_name.text = ""
        self.ids.task_desc.text = ""
        self.ids.task_date.text = ""
        self.ids.task_type.text = ""
        self.ids.task_status.text = ""

    def show_date_picker(self):
        picker = MDDatePicker()
        picker.bind(on_save=self.set_date)
        picker.open()

    def set_date(self, instance, value, date_range):
        if value:
            try:
                self.ids.task_date.text = value.strftime("%d-%m-%Y")
            except Exception as e:
                print(f"Date format error: {e}")
                self.ids.task_date.text = ""

    def show_task_type_menu(self):
        types = ["Daily", "Weekly", "Monthly"]
        items = [{
            "text": t,
            "viewclass": "CustomListItem",
            "icon": "calendar",
            "height": dp(56),
            "on_release": lambda x=t: self.set_task_type(x)
        } for t in types]

        self.menu = MDDropdownMenu(
            caller=self.ids.task_type,
            items=items,
            position="bottom",
            width_mult=4
        )
        self.menu.open()

    def set_task_type(self, text):
        self.ids.task_type.text = text
        self.menu.dismiss()

    def show_status_menu(self):
        statuses = ["Pending", "In Progress", "Done"]
        icons = ["clock", "progress-check", "check-circle"]

        items = [{
            "text": statuses[i],
            "viewclass": "StatusMenuItem",
            "icon": icons[i],
            "height": dp(56),
            "on_release": lambda x=statuses[i]: self.set_status(x)
        } for i in range(len(statuses))]

        self.status_menu = MDDropdownMenu(
            caller=self.ids.task_status,
            items=items,
            position="bottom",
            width_mult=4
        )
        self.status_menu.open()

    def set_status(self, text):
        self.ids.task_status.text = text
        self.status_menu.dismiss()

    def save_task(self):
        name = self.ids.task_name.text
        desc = self.ids.task_desc.text
        due_date = self.ids.task_date.text
        task_type = self.ids.task_type.text
        status = self.ids.task_status.text

        if not name or not desc or not due_date or not task_type or not status:
            self.show_error_dialog("Please fill all required fields")
            return

        app = MDApp.get_running_app()
        task = {
            "name": name,
            "description": desc,
            "due_date": due_date,
            "task_type": task_type,
            "status": status
        }
        app.add_task(task)

        # Reset inputs
        self.refresh_screen()

        self.show_success_dialog("Task added successfully!")
        self.go_back()

    def show_error_dialog(self, text):
        dialog = MDDialog(
            title="[color=ff3333]Error[/color]",
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_success_dialog(self, text):
        dialog = MDDialog(
            title="[color=4CAF50]Success[/color]",
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def go_back(self):
        self.manager.current = "tasks_screen"
        self.manager.transition.direction = "right"


class ProfileScreen(Screen):
    profile_name = StringProperty("")
    profile_title = StringProperty("")
    avatar_path = StringProperty("data/logo/kivy-icon-256.png")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.load_profile_data()

    def on_pre_enter(self):
        self.refresh_screen()

    def refresh_screen(self):
        app = MDApp.get_running_app()
        data = load_data()

        profile = data.get("profile", {})
        self.profile_name = profile.get("name", "")
        self.profile_title = profile.get("title", "")
        self.avatar_path = profile.get("avatar_path", "data/logo/kivy-icon-256.png")

        settings = data.get("settings", {})
        app.theme_cls.theme_style = settings.get("theme", "Light")
        app.theme_cls.primary_palette = settings.get("primary_color", "Indigo")

        app.update_task_stats()
        gpa, tasks_done, study_hours = app.gpa, app.tasks_done, app.study_hours

        if self.ids.get("gpa_label"):
            self.ids.gpa_label.text = f"{gpa}"
        if self.ids.get("tasks_done_label"):
            self.ids.tasks_done_label.text = f"{tasks_done}"
        if self.ids.get("study_hours_label"):
            self.ids.study_hours_label.text = f"{study_hours:.1f}"

        app.check_streak()
        if self.ids.get("streak_label"):
            self.ids.streak_label.text = f"{app.current_streak} days"

    def load_profile_data(self):
        profile = load_data().get("profile", {})
        self.profile_name = profile.get("name", "")
        self.profile_title = profile.get("title", "")
        self.avatar_path = profile.get("avatar_path", "data/logo/kivy-icon-256.png")

    def choose_avatar(self):
        filechooser.open_file(on_selection=self.set_avatar)

    def set_avatar(self, selection):
        if selection:
            selected_path = selection[0]
            self.avatar_path = selected_path

            data = load_data()
            data.setdefault("profile", {})["avatar_path"] = selected_path
            save_data(data)

            app = MDApp.get_running_app()
            app.avatar_path = selected_path

    def edit_profile(self):
        app = MDApp.get_running_app()

        name_field = MDTextField(
            hint_text="Name",
            text=self.profile_name,
            mode="fill",
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5}
        )
        title_field = MDTextField(
            hint_text="Title",
            text=self.profile_title,
            mode="fill",
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5}
        )

        content = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None, height="160dp")
        content.add_widget(name_field)
        content.add_widget(title_field)

        self.edit_dialog = MDDialog(
            title="Edit Profile",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", text_color=app.theme_cls.primary_color, on_release=lambda x: self.edit_dialog.dismiss()),
                MDRaisedButton(text="SAVE", on_release=lambda x: self.save_profile(name_field.text, title_field.text))
            ]
        )
        self.edit_dialog.open()

    def save_profile(self, name, title):
        if not name or not title:
            self.show_error_dialog("Please fill all required fields")
            return

        self.profile_name = name
        self.profile_title = title

        data = load_data()
        data["profile"] = {
            "name": name,
            "title": title,
            "avatar_path": self.avatar_path
        }
        save_data(data)

        self.edit_dialog.dismiss()
        self.show_success_dialog("Profile updated successfully!")

    def open_app_settings(self):
        app = MDApp.get_running_app()

        theme_buttons = MDBoxLayout(spacing="10dp")
        theme_buttons.add_widget(MDRectangleFlatButton(text="Light", on_release=lambda x: self.set_theme("Light")))
        theme_buttons.add_widget(MDRectangleFlatButton(text="Dark", on_release=lambda x: self.set_theme("Dark")))

        color_buttons = MDBoxLayout(spacing="10dp")
        color_buttons.add_widget(MDRectangleFlatButton(text="Indigo", on_release=lambda x: self.set_color("Indigo")))
        color_buttons.add_widget(MDRectangleFlatButton(text="Teal", on_release=lambda x: self.set_color("Teal")))
        color_buttons.add_widget(MDRectangleFlatButton(text="Red", on_release=lambda x: self.set_color("Red")))

        content = MDBoxLayout(orientation="vertical", spacing="20dp", size_hint_y=None, height="150dp")
        content.add_widget(MDLabel(text="Select Theme", halign="left"))
        content.add_widget(theme_buttons)
        content.add_widget(MDLabel(text="Primary Color", halign="left"))
        content.add_widget(color_buttons)

        self.app_settings_dialog = MDDialog(
            title="App Settings",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="Done", on_release=lambda x: self.app_settings_dialog.dismiss())
            ]
        )
        self.app_settings_dialog.open()

    def set_theme(self, style):
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = style
        current_color = app.theme_cls.primary_palette
        self.save_settings(theme=style, primary_color=current_color,
                           notifications_enabled=self.load_settings().get("notifications_enabled", True))

    def set_color(self, palette):
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = palette
        current_theme = app.theme_cls.theme_style
        self.save_settings(primary_color=palette, theme=current_theme,
                           notifications_enabled=self.load_settings().get("notifications_enabled", True))

    def open_notification_settings(self):
        settings = self.load_settings()
        self.notification_switch = MDSwitch()
        self.notification_switch.active = settings.get("notifications_enabled", True)

        layout = MDBoxLayout(orientation="horizontal", spacing="10dp", padding="10dp", size_hint_y=None, height="60dp")
        layout.add_widget(MDIcon(icon="bell", halign="left", pos_hint={"center_y": 0.85}))
        layout.add_widget(MDLabel(text="Notifications", halign="left", pos_hint={"center_y": 0.85}, font_style="H6"))
        layout.add_widget(self.notification_switch)

        self.notification_dialog = MDDialog(
            title="Notification Settings",
            type="custom",
            content_cls=layout,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.notification_dialog.dismiss()),
                MDRaisedButton(text="SAVE", on_release=lambda x: self.save_notification_setting())
            ]
        )
        self.notification_dialog.open()

    def save_notification_setting(self):
        enabled = self.notification_switch.active
        current = self.load_settings()

        self.save_settings(
            notifications_enabled=enabled,
            theme=current.get("theme", "Light"),
            primary_color=current.get("primary_color", "Indigo")
        )
        self.notification_dialog.dismiss()

        app = MDApp.get_running_app()
        if not enabled:
            app.cancel_all_notifications()
        else:
            app.reschedule_all_notifications()
            app.daily_motivation_event = Clock.schedule_once(app.send_daily_motivation, 5)

    def load_settings(self):
        return load_data().get("settings", {
            "notifications_enabled": True,
            "theme": "Light",
            "primary_color": "Indigo"
        })

    def save_settings(self, notifications_enabled=True, theme="Light", primary_color="Indigo"):
        data = load_data()
        data["settings"] = {
            "notifications_enabled": notifications_enabled,
            "theme": theme,
            "primary_color": primary_color
        }
        save_data(data)

    def show_error_dialog(self, text):
        app = MDApp.get_running_app()
        dialog = MDDialog(
            title="[color=ff3333]Error[/color]",
            text=text,
            buttons=[
                MDFlatButton(text="OK", text_color=app.theme_cls.primary_color,
                             theme_text_color="Custom", on_release=lambda x: dialog.dismiss())
            ]
        )
        dialog.open()

    def show_success_dialog(self, text):
        dialog = MDDialog(
            title="[color=4CAF50]Success[/color]",
            text=text,
            buttons=[MDRaisedButton(text="OK", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()


class StatsScreen(Screen):
    def on_pre_enter(self):
        self.refresh_screen()

    def refresh_screen(self):
        self.update_stats()

    def update_stats(self):
        app = MDApp.get_running_app()

        # ✅ Update streak display
        if self.ids.get("streak_widget"):
            self.ids.streak_widget.current_streak = app.current_streak

        # ✅ Update daily quote and tip
        if self.ids.get("daily_quote"):
            self.ids.daily_quote.text = app.daily_quote
        if self.ids.get("daily_tip"):
            self.ids.daily_tip.text = app.daily_tip

    def go_back(self):
        self.manager.current = "main_screen"
        self.manager.transition.direction = "right"

class StudyPlannerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduled_notifications = []
        self.daily_motivation_event = None

        # Stats
        self.current_streak = 0
        self.total_tasks = 0
        self.completed_tasks = 0
        self.task_completion_percentage = 0

        # Tips & Quotes
        self.daily_quote = random.choice(MOTIVATIONAL_QUOTES)
        self.daily_tip = random.choice(PRODUCTIVITY_TIPS)

        # Load once at init
        self.load_profile_data()
        self.load_settings()
        self.check_streak()
        self.update_task_stats()

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        return Builder.load_file("optimize.kv")

    def on_start(self):
        settings = self.load_settings()
        self.theme_cls.theme_style = settings.get("theme", "Light")
        self.theme_cls.primary_palette = settings.get("primary_color", "Indigo")

        if settings.get("notifications_enabled", True):
            self.daily_motivation_event = Clock.schedule_once(self.send_daily_motivation, 5)
            for s in self.get_all_schedules():
                if s.get("notification"):
                    self.schedule_notification(s["name"], s["time"])

        self.update_streak()
        Clock.schedule_once(lambda dt: self.clean_old_schedules(), 1)  # ✅ defer heavy task

    # ---------------- Profile ----------------
    def load_profile_data(self):
        profile = load_data().get("profile", {})
        self.profile_name = profile.get("name", "")
        self.profile_title = profile.get("title", "")
        self.avatar_path = profile.get("avatar_path", "data/logo/kivy-icon-256.png")

    def load_settings(self):
        return load_data().get("settings", {
            "notifications_enabled": True,
            "theme": "Light",
            "primary_color": "Indigo"
        })

    def save_streak(self, date, streak_count):
        data = load_data()
        data["motivation"] = {
            "last_studied": date.strftime("%d-%m-%Y"),
            "current_streak": streak_count
        }
        save_data(data)

    def update_streak(self):
        today_str = datetime.now().strftime("%d-%m-%Y")
        data = load_data()
        if data.get("motivation", {}).get("last_studied") != today_str:
            self.save_streak(datetime.now(), self.current_streak)

    def check_streak(self):
        data = load_data()
        streak = data.get("motivation", {"last_studied": "", "current_streak": 0})
        today = datetime.now().date()

        if streak["last_studied"]:
           last_date = datetime.strptime(streak["last_studied"], "%d-%m-%Y").date()
           day = (today - last_date).days
           if day == 0:
               self.current_streak = streak["current_streak"]
           elif day == 1:
               self.current_streak = streak["current_streak"] + 1
               self.save_streak(today, self.current_streak)
           else:
               self.current_streak = 1
               self.save_streak(today, 1)
        else:
            self.current_streak = 1
            self.save_streak(today, 1)

    # ---------------- Schedule ----------------
    def get_all_schedules(self):
        return sorted(load_data(use_cache=True).get("schedules", []), key=lambda x: x["time"])

    def add_schedule(self, schedule):
        data = load_data()
        schedules = data.get("schedules", [])
        schedules.append(schedule)

        # ✅ Sort by time ASC within same date
        schedules.sort(key=lambda s: datetime.strptime(s["time"], "%H:%M"))

        # ✅ Sort by date DESC (latest first)
        schedules.sort(key=lambda s: datetime.strptime(s["date"], "%d-%m-%Y"), reverse=True)

        data["schedules"] = schedules
        save_data(data)

        if schedule.get("notification"):
            self.schedule_notification(schedule["name"], schedule["time"])


    def delete_schedule(self, name):
        data = load_data()
        data["schedules"] = [s for s in data.get("schedules", []) if s.get("name") != name]
        save_data(data)

    def clean_old_schedules(self):
        data = load_data()
        if not data.get("schedules"):
            return

        today = datetime.now()
        start = today - timedelta(days=today.weekday())
        week_dates = [(start + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(7)]

        data["schedules"] = [s for s in data["schedules"] if s.get("date") in week_dates]
        save_data(data)

    # ---------------- Tasks ----------------
    def get_all_tasks(self):
        return load_data(use_cache=True).get("tasks", [])

    def add_task(self, task):
        task["created_at"] = datetime.now().strftime("%d-%m-%Y")
        data = load_data()
        data.setdefault("tasks", []).append(task)
        save_data(data)
        self.update_task_stats()

        if "stats_screen" in self.root.screen_names:
            self.root.get_screen("stats_screen").update_stats()

    def update_task(self, name, updates):
        data = load_data()
        for task in data.get("tasks", []):
            if task.get("name") == name:
                task.update(updates)
                break
        save_data(data)
        self.update_task_stats()

    def delete_task(self, name):
        data = load_data()
        data["tasks"] = [t for t in data.get("tasks", []) if t.get("name") != name]
        save_data(data)
        self.update_task_stats()

    def update_task_stats(self):
        tasks = load_data(use_cache=True).get("tasks", [])
        self.total_tasks = len(tasks)
        self.completed_tasks = len([t for t in tasks if t.get("status") == "Done"])
        self.task_completion_percentage = (self.completed_tasks / self.total_tasks) * 100 if self.total_tasks else 0

    # ---------------- GPA & Time ----------------
    @property
    def gpa(self):
        return round((self.completed_tasks / self.total_tasks), 1) if self.total_tasks else 0.0

    @property
    def tasks_done(self):
        return self.completed_tasks

    @property
    def study_hours(self):
        return self.completed_tasks * 0.5

    # ---------------- Notifications ----------------
    def send_daily_motivation(self, dt):
        if not self.load_settings().get("notifications_enabled", True):
            return

        data = load_data()
        today = datetime.now().strftime("%d-%m-%Y")
        if data.get("motivation", {}).get("last_sent_date") == today:
            return

        notification.notify(
            title="Daily Study Motivation",
            message=self.daily_quote,
            app_name="Study Planner"
        )

        data.setdefault("motivation", {})["last_sent_date"] = today
        save_data(data)

    def schedule_notification(self, name, time_str):
        if not self.load_settings().get("notifications_enabled", True):
            return

        try:
            now = datetime.now()
            target_time = datetime.strptime(time_str, "%H:%M").time()
            notify_at = datetime.combine(now.date(), target_time)

            if notify_at < now:
                notify_at += timedelta(days=1)

            seconds = (notify_at - now).total_seconds()
            event = Clock.schedule_once(lambda dt: self.send_notification(name), seconds)
            self.scheduled_notifications.append(event)
        except Exception as e:
            print(f"[ERROR] Failed to schedule: {e}")

    def send_notification(self, name):
        if self.load_settings().get("notifications_enabled", True):
            notification.notify(
                title="Study Reminder",
                message=f"It's time for: {name}",
                app_name="Study Planner"
            )

    def cancel_all_notifications(self):
        for event in self.scheduled_notifications:
            if event:
                event.cancel()
        self.scheduled_notifications.clear()

        if self.daily_motivation_event:
            self.daily_motivation_event.cancel()
            self.daily_motivation_event = None

    def reschedule_all_notifications(self):
        for schedule in self.get_all_schedules():
            if schedule.get("notification"):
                self.schedule_notification(schedule["name"], schedule["time"])

    # ---------------- Dialogs ----------------
    def show_schedule_dialog(self, schedule):
        dialog = MDDialog(
            title=f"[b]{schedule['name']}[/b] - {schedule['subject']}",
            text=f"Time: {schedule['time']}\nDescription: {schedule['description']}\nDate: {schedule['date']}\nNotification: {'On' if schedule['notification'] else 'Off'}",
            buttons=[
                MDFlatButton(text="Delete", theme_text_color="Custom",text_color=self.theme_cls.primary_color,
                             on_release=lambda x: self.delete_schedule_dialog(schedule, dialog)),
                MDRaisedButton(text="Close", on_release=lambda x: dialog.dismiss())
            ]
        )
        dialog.open()

    def delete_schedule_dialog(self, schedule, dialog):
        self.delete_schedule(schedule["name"])
        dialog.dismiss()
        self.root.get_screen("schedule_screen").load_schedules()

    def show_task_dialog(self, task):
        dialog = MDDialog(
            title=f"[b]{task['name']}[/b]",
            text=f"Description: {task['description']}\nDue: {task['due_date']}\nType: {task['task_type']}\nStatus: {task['status']}",
            buttons=[
                MDFlatButton(text="Edit", theme_text_color="Custom",text_color=self.theme_cls.primary_color,
                             on_release=lambda x: self.edit_task_dialog(task, dialog)),
                MDFlatButton(text="Delete", theme_text_color="Custom",text_color=self.theme_cls.primary_color,
                             on_release=lambda x: self.delete_task_dialog(task, dialog)),
                MDRaisedButton(text="Close", on_release=lambda x: dialog.dismiss())
            ]
        )
        dialog.open()

    def edit_task_dialog(self, task, dialog):
        dialog.dismiss()
        self.show_edit_task_screen(task)

    def delete_task_dialog(self, task, dialog):
        self.delete_task(task["name"])
        dialog.dismiss()
        self.root.get_screen("tasks_screen").load_tasks()

    def show_edit_task_screen(self, task):
        pass  # Reserved for future
    
    def delete_task_dialog(self, task, dialog):
        self.delete_task(task['name'])
        dialog.dismiss()
        tasks_screen = self.root.get_screen("tasks_screen")
        tasks_screen.load_tasks()
    
    def task_status_changed(self, list_item, active):
        task = list_item.task_data
        new_status = "Done" if active else "In Progress"
        self.update_task(task['name'], {"status": new_status})

        # Update both data and UI
        list_item.status = new_status
        list_item.task_data["status"] = new_status
        list_item.icon = list_item.get_status_icon()  # ✅ update icon

        if active:
            self.update_streak()

        # Optional: update stats
        if "stats_screen" in self.root.screen_names:
            stats_screen = self.root.get_screen("stats_screen")
            stats_screen.update_stats()

if __name__ == "__main__":
    StudyPlannerApp().run()
