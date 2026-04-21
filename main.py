import os, sqlite3, random
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.utils import platform

if platform not in ("android", "ios"):
    Window.size = (390, 780)
    Window.clearcolor = (1, 1, 1, 1)

KV_FILE = os.path.join(os.path.dirname(__file__), "home.kv")
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def snack(msg):
    MDSnackbar(MDSnackbarText(text=msg), y=24, pos_hint={"center_x":0.5}, size_hint_x=0.9, duration=2).open()

def get_con():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_con() as c:
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, points INTEGER DEFAULT 0, badge TEXT DEFAULT 'Newcomer')")
        c.execute("CREATE TABLE IF NOT EXISTS complaints (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, description TEXT, category TEXT, location TEXT, date TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, area TEXT, available INTEGER DEFAULT 1, rating REAL DEFAULT 5.0)")
        c.execute("CREATE TABLE IF NOT EXISTS clean_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, staff_id INTEGER, location TEXT, description TEXT, date TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS leaderboard (username TEXT PRIMARY KEY, points INTEGER DEFAULT 0, complaints INTEGER DEFAULT 0, badge TEXT DEFAULT 'Newcomer')")
        c.execute("CREATE TABLE IF NOT EXISTS community (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, likes INTEGER DEFAULT 0, date TEXT)")
        c.commit()
        if c.execute("SELECT COUNT(*) FROM staff").fetchone()[0] == 0:
            c.executemany("INSERT INTO staff (name,phone,area,available,rating) VALUES (?,?,?,?,?)", [
                ("Ramesh Kumar","9876543210","Block A",1,4.8),
                ("Sunita Devi","9812345678","Library",1,4.9),
                ("Manoj Singh","9898765432","Sports",1,4.7),
                ("Priya Sharma","9765432109","Hostel",0,4.6),
                ("Vikram Yadav","9654321098","Main Gate",1,4.5),
            ])
            c.executemany("INSERT INTO community (username,message,likes,date) VALUES (?,?,?,?)", [
                ("EcoHero_Raj","Dustbins overflowing near canteen!",12,"2024-04-18"),
                ("GreenStar_Priya","Cleanup drive tomorrow 7AM!",25,"2024-04-18"),
            ])
            c.commit()

def register_user(u, p):
    try:
        with get_con() as c:
            c.execute("INSERT INTO users (username,password) VALUES (?,?)", (u,p))
            c.execute("INSERT OR IGNORE INTO leaderboard (username) VALUES (?)", (u,))
            c.commit()
        return True
    except:
        return False

def validate_user(u, p):
    with get_con() as c:
        return c.execute("SELECT id FROM users WHERE username=? AND password=?", (u,p)).fetchone() is not None

def get_stats(u):
    with get_con() as c:
        r = c.execute("SELECT points,badge FROM users WHERE username=?", (u,)).fetchone()
        return {"points":r[0] if r else 0, "badge":r[1] if r else "Newcomer"}

def add_points(u, pts):
    with get_con() as c:
        c.execute("UPDATE users SET points=points+? WHERE username=?", (pts,u))
        c.execute("UPDATE leaderboard SET points=points+? WHERE username=?", (pts,u))
        r = c.execute("SELECT points FROM users WHERE username=?", (u,)).fetchone()
        if r:
            p = r[0]
            b = "Newcomer"
            if p>=500: b="Eco Legend"
            elif p>=200: b="Eco Champion"
            elif p>=100: b="Eco Hero"
            elif p>=50: b="Green Star"
            elif p>=20: b="Eco Starter"
            c.execute("UPDATE users SET badge=? WHERE username=?", (b,u))
            c.execute("UPDATE leaderboard SET badge=? WHERE username=?", (b,u))
        c.commit()

def insert_complaint(u, title, desc, cat, loc):
    d = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_con() as c:
        c.execute("INSERT INTO complaints (username,title,description,category,location,date) VALUES (?,?,?,?,?,?)", (u,title,desc,cat,loc,d))
        c.execute("UPDATE leaderboard SET complaints=complaints+1 WHERE username=?", (u,))
        c.commit()
    add_points(u, 10)

def get_staff_list():
    with get_con() as c:
        return c.execute("SELECT id,name,phone,area,available,rating FROM staff ORDER BY available DESC,rating DESC").fetchall()

def send_request(u, sid, loc, desc):
    d = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_con() as c:
        c.execute("INSERT INTO clean_requests (username,staff_id,location,description,date) VALUES (?,?,?,?,?)", (u,sid,loc,desc,d))
        c.commit()
    add_points(u, 5)

def get_leaderboard():
    with get_con() as c:
        return c.execute("SELECT username,points,complaints,badge FROM leaderboard ORDER BY points DESC LIMIT 10").fetchall()

def get_posts():
    with get_con() as c:
        return c.execute("SELECT id,username,message,likes,date FROM community ORDER BY likes DESC LIMIT 20").fetchall()

def add_post(u, msg):
    d = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_con() as c:
        c.execute("INSERT INTO community (username,message,date) VALUES (?,?,?)", (u,msg,d))
        c.commit()
    add_points(u, 3)

def like_post(pid):
    with get_con() as c:
        c.execute("UPDATE community SET likes=likes+1 WHERE id=?", (pid,))
        c.commit()

WASTE = {"plastic":"Blue dustbin","food":"Green dustbin","paper":"Dry waste","glass":"Blue dustbin","metal":"Blue dustbin","battery":"E-waste only!","electronic":"E-waste point","cloth":"Dry waste","medical":"Red bin","default":"Separate wet and dry!"}
TIPS = ["Carry a reusable bottle!","Use both sides of paper.","Say no to plastic bags.","Fix leaking taps.","Walk short distances."]
CHALLENGES = [("Carry reusable bottle",10),("Report 1 issue",10),("Pick up litter",15),("No plastic today",10),("Post in community",5)]

def ai_answer(q):
    q = q.lower()
    if any(w in q for w in ["tip","eco","green","save"]):
        return random.choice(TIPS)
    for k,v in WASTE.items():
        if k in q: return v
    return WASTE["default"]

class LoginScreen(MDScreen):
    def do_login(self):
        u = self.ids.lu.text.strip()
        p = self.ids.lp.text.strip()
        if not u or not p:
            snack("Please fill all fields!")
            return
        if validate_user(u, p):
            MDApp.get_running_app().current_user = u
            self.manager.current = "home"
        else:
            snack("Invalid username or password!")
    def go_signup(self):
        self.manager.current = "signup"

class SignupScreen(MDScreen):
    def do_signup(self):
        u = self.ids.su.text.strip()
        p = self.ids.sp.text.strip()
        c = self.ids.sc.text.strip()
        if not u or not p or not c:
            snack("Please fill all fields!")
            return
        if p != c:
            snack("Passwords do not match!")
            return
        if len(p) < 6:
            snack("Password must be 6+ characters!")
            return
        if register_user(u, p):
            snack("Account created! Please login.")
            self.manager.current = "login"
        else:
            snack("Username already taken!")
    def go_login(self):
        self.manager.current = "login"

class HomeScreen(MDScreen):
    def on_enter(self):
        u = MDApp.get_running_app().current_user or "Student"
        s = get_stats(u)
        self.ids.greeting.text = "Hey " + u + "!"
        self.ids.pts.text = str(s["points"]) + " pts"
        self.ids.badge.text = s["badge"]
        ch = random.choice(CHALLENGES)
        self.ids.challenge.text = ch[0] + " (+" + str(ch[1]) + " pts)"
    def go_to(self, s):
        self.manager.current = s

class ComplaintScreen(MDScreen):
    dialog = None
    def submit(self):
        t = self.ids.title.text.strip()
        if not t:
            snack("Please enter a title!")
            return
        u = MDApp.get_running_app().current_user or "anon"
        insert_complaint(u, t, self.ids.desc.text.strip(), self.ids.cat.text.strip() or "General", self.ids.loc.text.strip() or "Campus")
        self.ids.title.text = self.ids.desc.text = self.ids.cat.text = self.ids.loc.text = ""
        if not self.dialog:
            self.dialog = MDDialog(title="Submitted! +10 pts", text="Complaint saved!", buttons=[MDButton(MDButtonText(text="OK"), on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()
    def go_back(self):
        self.manager.current = "home"

class StaffScreen(MDScreen):
    sid = None
    dialog = None
    def on_enter(self): self.load()
    def load(self):
        from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
        self.ids.slist.clear_widgets()
        for s in get_staff_list():
            sid, name, phone, area, avail, rating = s
            self.ids.slist.add_widget(MDListItem(
                MDListItemHeadlineText(text=name + " - " + str(rating) + " stars"),
                MDListItemSupportingText(text=area + " | " + ("Available" if avail else "Busy") + " | " + phone),
                on_release=lambda x, sid=sid, name=name: self.select(sid, name)
            ))
    def select(self, sid, name):
        self.sid = sid
        self.ids.selected.text = "Selected: " + name
        snack(name + " selected!")
    def send(self):
        loc = self.ids.loc.text.strip()
        if not self.sid:
            snack("Please select a staff member!")
            return
        if not loc:
            snack("Please enter location!")
            return
        u = MDApp.get_running_app().current_user or "anon"
        send_request(u, self.sid, loc, self.ids.desc.text.strip())
        if not self.dialog:
            self.dialog = MDDialog(title="Request Sent! +5 pts", text="Staff notified!", buttons=[MDButton(MDButtonText(text="OK"), on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()
        self.ids.loc.text = self.ids.desc.text = ""
        self.sid = None
        self.ids.selected.text = "No staff selected"
    def go_back(self):
        self.manager.current = "home"

class LeaderboardScreen(MDScreen):
    def on_enter(self): self.load()
    def load(self):
        from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
        self.ids.llist.clear_widgets()
        medals = ["1st","2nd","3rd"]
        for i, row in enumerate(get_leaderboard()):
            u, pts, comp, badge = row
            self.ids.llist.add_widget(MDListItem(
                MDListItemHeadlineText(text=(medals[i] if i<3 else str(i+1))+" "+u+" - "+badge),
                MDListItemSupportingText(text=str(pts)+" points | "+str(comp)+" complaints")
            ))
    def go_back(self):
        self.manager.current = "home"

class RewardsScreen(MDScreen):
    def on_enter(self):
        s = get_stats(MDApp.get_running_app().current_user or "")
        pts = s["points"]
        self.ids.pts.text = str(pts)
        self.ids.badge.text = s["badge"]
        self.ids.prog.value = min(pts/200.0,1.0)*100
        self.ids.prog_label.text = str(max(0,200-pts))+" more pts to Eco Champion" if pts<200 else "Eco Champion!"
    def go_back(self):
        self.manager.current = "home"

class PhotoScreen(MDScreen):
    def open_gallery(self): snack("Gallery not available on Mac")
    def upload(self):
        add_points(MDApp.get_running_app().current_user or "anon", 5)
        snack("Uploaded! +5 pts")
    def go_back(self):
        self.manager.current = "home"

class AIScreen(MDScreen):
    def ask(self):
        q = self.ids.q.text.strip()
        if not q:
            snack("Please enter a question!")
            return
        self.ids.ans.text = ai_answer(q)
    def tip(self): self.ids.ans.text = random.choice(TIPS)
    def go_back(self):
        self.manager.current = "home"

class MapScreen(MDScreen):
    def on_enter(self):
        mp = os.path.join(os.path.dirname(__file__), "assets", "maps", "gwalior_map.png")
        if os.path.exists(mp):
            self.ids.mapimg.source = mp
            self.ids.mapimg.opacity = 1
            self.ids.maplabel.opacity = 0
        else:
            self.ids.mapimg.opacity = 0
            self.ids.maplabel.opacity = 1
    def go_back(self):
        self.manager.current = "home"

class CommunityScreen(MDScreen):
    def on_enter(self): self.load()
    def load(self):
        from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
        self.ids.clist.clear_widgets()
        for pid, uname, msg, likes, dt in get_posts():
            self.ids.clist.add_widget(MDListItem(
                MDListItemHeadlineText(text="@"+uname+" - "+str(likes)+" likes"),
                MDListItemSupportingText(text=msg),
                on_release=lambda x, pid=pid: self.like(pid)
            ))
    def like(self, pid):
        like_post(pid); snack("Liked!"); self.load()
    def post(self):
        msg = self.ids.msg.text.strip()
        if not msg:
            snack("Please write a message!")
            return
        add_post(MDApp.get_running_app().current_user or "anon", msg)
        self.ids.msg.text = ""
        snack("Posted! +3 pts")
        self.load()
    def go_back(self):
        self.manager.current = "home"

class ProfileScreen(MDScreen):
    def on_enter(self):
        u = MDApp.get_running_app().current_user or "Student"
        s = get_stats(u)
        self.ids.uname.text = u
        self.ids.pts.text = str(s["points"])+" Points"
        self.ids.badge.text = s["badge"]
    def logout(self):
        MDApp.get_running_app().current_user = ""
        self.manager.current = "login"
    def go_back(self):
        self.manager.current = "home"

class CleanCampusApp(MDApp):
    current_user = ""
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"
        self.title = "CleanCampus"
        init_db()
        Builder.load_file(KV_FILE)
        sm = ScreenManager(transition=SlideTransition())
        for name, cls in [("login",LoginScreen),("signup",SignupScreen),("home",HomeScreen),("complaint",ComplaintScreen),("staff",StaffScreen),("leaderboard",LeaderboardScreen),("rewards",RewardsScreen),("photo",PhotoScreen),("ai",AIScreen),("map",MapScreen),("community",CommunityScreen),("profile",ProfileScreen)]:
            sm.add_widget(cls(name=name))
        return sm

if __name__ == "__main__":
    CleanCampusApp().run()
