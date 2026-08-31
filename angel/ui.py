import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog
import threading
import sys
from pathlib import Path
from .config import Config
from .brain import Brain, MODES, CAPABILITIES
from .voice import Voice
from .feedback import Feedback

class AngelUI:
    def _set_window_icon(self, window):
        try:
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
            ico = base / "Angel_AI.ico"
            png = base / "Angel_AI.png"
            if ico.exists():
                window.iconbitmap(str(ico))
            elif png.exists():
                window_icon = tk.PhotoImage(file=str(png))
                window.iconphoto(True, window_icon)
                window._angel_icon_image = window_icon
        except Exception:
            pass

    def _set_app_icon(self):
        try:
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
            ico = base / "Angel_AI.ico"
            png = base / "Angel_AI.png"
            if ico.exists():
                self.root.iconbitmap(default=str(ico))
                self.root.iconbitmap(str(ico))
            elif png.exists():
                self._angel_icon_image = tk.PhotoImage(file=str(png))
                self.root.iconphoto(True, self._angel_icon_image)
        except Exception:
            pass

    def __init__(self,root,brain,voice):
        self.root=root; self.brain=brain; self.voice=voice; self.config=brain.config; self.feedback=Feedback(self.config.root/'data/feedback.json')
        self.last_answer=''; self.chat_rows=[]
        self._set_app_icon()
        root.title('Angel AI 6.0'); root.geometry('1320x840'); root.minsize(1000,700)
        self._build(); self.apply_theme(self.config.theme); self.refresh_chats(); self.update_pin_button()
        self.write('Angel',"Hello. I'm Angel AI 6.0. I'm local-first, knowledge-aware, and I will only claim abilities the application actually provides.")
        self.refresh_status(); self.refresh_models(); self.root.after(5000,self.status_loop)

    def _build(self):
        self.main=tk.Frame(self.root); self.main.pack(fill='both',expand=True)
        self.sidebar=tk.Frame(self.main,width=250); self.sidebar.pack(side='left',fill='y',padx=(10,5),pady=10); self.sidebar.pack_propagate(False)
        self.side_title=tk.Label(self.sidebar,text='ANGEL CHATS',font=('Segoe UI',15,'bold')); self.side_title.pack(anchor='w',padx=10,pady=(8,6))
        self.newbtn=tk.Button(self.sidebar,text='+ New Chat',command=self.new_chat); self.newbtn.pack(fill='x',padx=8,pady=4)
        self.pinbtn=tk.Button(self.sidebar,text='📌 Pin Current Chat',command=self.pin_current); self.pinbtn.pack(fill='x',padx=8,pady=4)
        self.pinned_label=tk.Label(self.sidebar,text='PINNED',font=('Segoe UI',9,'bold')); self.pinned_label.pack(anchor='w',padx=10,pady=(14,3))
        self.pinned=tk.Listbox(self.sidebar,height=5,exportselection=False); self.pinned.pack(fill='x',padx=8)
        self.pinned.bind('<Double-Button-1>',self.open_pinned)
        self.chats_label=tk.Label(self.sidebar,text='ALL CHATS',font=('Segoe UI',9,'bold')); self.chats_label.pack(anchor='w',padx=10,pady=(12,3))
        self.chats=tk.Listbox(self.sidebar,exportselection=False); self.chats.pack(fill='both',expand=True,padx=8,pady=(0,6))
        self.chats.bind('<Double-Button-1>',self.open_chat)
        self.delbtn=tk.Button(self.sidebar,text='Delete Selected Chat',command=self.delete_selected_chat); self.delbtn.pack(fill='x',padx=8,pady=4)
        self.renamebtn=tk.Button(self.sidebar,text='Rename Selected Chat',command=self.rename_selected_chat); self.renamebtn.pack(fill='x',padx=8,pady=(0,8))

        content=tk.Frame(self.main); content.pack(side='left',fill='both',expand=True,padx=(5,10),pady=10)
        self.top=tk.Frame(content); self.top.pack(fill='x',pady=(0,6))
        self.title=tk.Label(self.top,text='ANGEL AI',font=('Segoe UI',22,'bold')); self.title.pack(side='left')
        self.theme_btn=tk.Button(self.top,text='Light Mode',command=self.toggle_theme); self.theme_btn.pack(side='right',padx=4)
        self.status=tk.Label(self.top,text='● OFFLINE',font=('Segoe UI',10,'bold')); self.status.pack(side='right',padx=8)
        self.connect_btn=tk.Button(self.top,text='Get Angel Online',command=self.connect_ollama); self.connect_btn.pack(side='right')
        bar=tk.Frame(content); bar.pack(fill='x',pady=4)
        tk.Label(bar,text='Mode:').pack(side='left')
        self.mode=tk.StringVar(value=self.brain.mode); self.modebox=ttk.Combobox(bar,textvariable=self.mode,values=list(MODES.keys()),state='readonly',width=18); self.modebox.pack(side='left',padx=6); self.modebox.bind('<<ComboboxSelected>>',lambda e:self.brain.set_mode(self.mode.get()))
        tk.Label(bar,text='Model:').pack(side='left',padx=(16,4))
        self.model=tk.StringVar(value=self.config.model); self.modelbox=ttk.Combobox(bar,textvariable=self.model,values=[],state='readonly',width=24); self.modelbox.pack(side='left'); self.modelbox.bind('<<ComboboxSelected>>',lambda e:self.select_model())
        tk.Label(bar,text='GPT:').pack(side='left',padx=(16,4))
        self.gpt=tk.StringVar(value=self.brain.current_gpt)
        self.gptbox=ttk.Combobox(bar,textvariable=self.gpt,values=[],state='readonly',width=24)
        self.gptbox.pack(side='left')
        self.gptbox.bind('<<ComboboxSelected>>',lambda e:self.select_gpt())

        self.kb_label=tk.Label(bar,text='Knowledge: loading...',anchor='e'); self.kb_label.pack(side='right',fill='x',expand=True,padx=10)
        self.chat=tk.Text(content,wrap='word',font=('Segoe UI',12),state='disabled',padx=12,pady=10,bd=0,highlightthickness=0)
        self.chat.pack(fill='both',expand=True,pady=8)
        self._configure_chat_tags()
        self._thinking_job=None
        self._thinking_active=False
        self._thinking_phase=0

        row=tk.Frame(content); row.pack(fill='x',pady=5)
        self.entry=tk.Entry(row,font=('Segoe UI',12)); self.entry.pack(side='left',fill='x',expand=True); self.entry.bind('<Return>',lambda e:self.send())
        self.sendbtn=tk.Button(row,text='Send',command=self.send); self.sendbtn.pack(side='left',padx=6)
        ctl=tk.Frame(content); ctl.pack(fill='x',pady=(2,12))
        for txt,cmd in [('Add File',self.add_file),('Manage Knowledge',self.manage_knowledge),('Manage GPTs',self.manage_gpts),('Speak Last',self.speak_last),('Stop Voice',self.voice.stop),('Test Voice',lambda:self.voice.speak('Angel voice system test successful.'))]:
            tk.Button(ctl,text=txt,command=cmd).pack(side='left',padx=(0,6))
        self.auto=tk.BooleanVar(value=self.config.voice_enabled); tk.Checkbutton(ctl,text='Auto Speak',variable=self.auto,command=self.toggle_auto).pack(side='left',padx=4)
        tk.Label(ctl,text='Speech:').pack(side='left',padx=(12,4))
        ttk.Scale(ctl,from_=120,to=260,variable=tk.IntVar(value=self.config.speech_rate),orient='horizontal',length=150,command=self.save_rate).pack(side='left')
        self.up=tk.Button(ctl,text='👍',command=lambda:self.feedback.record('up')); self.up.pack(side='right'); self.down=tk.Button(ctl,text='👎',command=lambda:self.feedback.record('down')); self.down.pack(side='right',padx=4)

    def _configure_chat_tags(self):
        c=self.colors()
        if self.config.theme=='dark':
            angel_name='#78a9ff'; angel_text='#d8e7ff'
            user_name='#8be28b'; user_text='#ffffff'; user_bg='#1f5f3a'
        else:
            angel_name='#174ea6'; angel_text='#202124'
            user_name='#166534'; user_text='#111827'; user_bg='#dbeafe'
        self.chat.configure(bg=c['input'],fg=c['fg'],insertbackground=c['insert'])
        self.chat.tag_configure('angel_name',font=('Segoe UI',10,'bold'),foreground=angel_name,justify='left')
        self.chat.tag_configure('angel_text',foreground=angel_text,background=c['input'],justify='left',lmargin1=12,lmargin2=12,rmargin=150,spacing1=2,spacing3=10)
        self.chat.tag_configure('user_name',font=('Segoe UI',10,'bold'),foreground=user_name,justify='right',rmargin=12)
        self.chat.tag_configure('user_text',foreground=user_text,background=user_bg,justify='right',lmargin1=150,lmargin2=150,rmargin=12,spacing1=2,spacing3=10)

    def colors(self):
        return {'dark':{'bg':'#101216','panel':'#171a21','fg':'#f2f4f8','muted':'#aab2bf','input':'#0c0e12','insert':'#fff'},
                'light':{'bg':'#f4f6f8','panel':'#fff','fg':'#17202a','muted':'#59636e','input':'#fff','insert':'#17202a'}}[self.config.theme]
    def apply_theme(self,theme):
        self.config.theme=theme; self.config.save_settings(); c=self.colors(); self.root.configure(bg=c['bg'])
        def walk(parent):
            for w in parent.winfo_children():
                try:
                    if isinstance(w,tk.Frame): w.configure(bg=c['bg'])
                    elif isinstance(w,(tk.Button,tk.Checkbutton,tk.Label)): w.configure(bg=c['panel'],fg=c['fg'],activebackground=c['bg'],activeforeground=c['fg'])
                    elif isinstance(w,(tk.Entry,tk.Text,tk.Listbox)): w.configure(bg=c['input'],fg=c['fg'],insertbackground=c['insert'])
                except Exception: pass
                if w.winfo_children(): walk(w)
        walk(self.root); self._configure_chat_tags(); self.title.configure(bg=c['bg'],fg=c['fg']); self.theme_btn.configure(text='Light Mode' if theme=='dark' else 'Dark Mode')
    def toggle_theme(self): self.apply_theme('light' if self.config.theme=='dark' else 'dark')
    def toggle_auto(self): self.config.voice_enabled=bool(self.auto.get()); self.config.save_settings(); self.voice.enabled=self.config.voice_enabled
    def save_rate(self,value): self.config.speech_rate=int(float(value)); self.config.save_settings(); self.voice.rate=self.config.speech_rate
    def select_model(self): self.config.model=self.model.get(); self.config.save_settings(); self.write('Angel',f'Model selected: {self.config.model}')
    def status_loop(self): self.refresh_status(); self.root.after(5000,self.status_loop)
    def select_gpt(self):
        name=self.gpt.get()
        profile=next((p for p in self.brain.gpt_profiles() if p["name"]==name),None)
        if not profile:return
        self.brain.set_gpt(profile["slug"])
        self.write('Angel',f'Specialist GPT selected for this chat: {profile["name"]}')

    def manage_gpts(self):
        win=tk.Toplevel(self.root); self._set_window_icon(win); win.title("Angel GPTs"); win.geometry("1150x760"); win.minsize(950,620)
        c=self.colors(); win.configure(bg=c["bg"])
        left=tk.Frame(win,bg=c["bg"]); left.pack(side="left",fill="y",padx=14,pady=14)
        right=tk.Frame(win,bg=c["bg"]); right.pack(side="left",fill="both",expand=True,padx=(0,14),pady=14)
        tk.Label(left,text="SPECIALIST GPTs",font=("Segoe UI",15,"bold"),bg=c["bg"],fg=c["fg"]).pack(anchor="w")
        lb=tk.Listbox(left,width=34,height=28,bg=c["input"],fg=c["fg"])
        lb.pack(fill="y",expand=True,pady=8)
        tk.Label(right,text="GPT Profile",font=("Segoe UI",15,"bold"),bg=c["bg"],fg=c["fg"]).pack(anchor="w")
        vars={k:tk.StringVar() for k in ["name","description","domains","topics"]}
        for label,key in [("Name","name"),("Description","description"),("Domains (comma separated)","domains"),("Topics (comma separated)","topics")]:
            tk.Label(right,text=label,bg=c["bg"],fg=c["fg"]).pack(anchor="w",pady=(8,2))
            tk.Entry(right,textvariable=vars[key],bg=c["input"],fg=c["fg"],insertbackground=c["fg"]).pack(fill="x")
        tk.Label(right,text="Specialist instructions",bg=c["bg"],fg=c["fg"]).pack(anchor="w",pady=(8,2))
        prompt=tk.Text(right,height=13,wrap="word",bg=c["input"],fg=c["fg"],insertbackground=c["fg"])
        prompt.pack(fill="both",expand=True)
        status=tk.Label(right,text="",bg=c["bg"],fg=c["muted"]); status.pack(anchor="w",pady=5)
        def refresh():
            lb.delete(0,"end")
            profiles=self.brain.gpt_profiles()
            for p in profiles:
                marker="★ " if p["slug"]==getattr(self.brain,"current_gpt_slug","angel") else ""
                lb.insert("end",marker+p["name"])
            lb.profiles=profiles
        def load():
            sel=lb.curselection()
            if not sel:return
            p=lb.profiles[sel[0]]
            for k in vars:vars[k].set(p.get(k,""))
            prompt.delete("1.0","end"); prompt.insert("1.0",p.get("system_prompt",""))
            status.config(text=f"Slug: {p['slug']}")
        def save():
            sel=lb.curselection()
            try:
                if sel:
                    p=lb.profiles[sel[0]]
                    self.brain.update_gpt(p["slug"],name=vars["name"].get(),description=vars["description"].get(),
                                          domains=vars["domains"].get(),topics=vars["topics"].get(),
                                          system_prompt=prompt.get("1.0","end").strip())
                else:
                    self.brain.create_gpt(vars["name"].get(),vars["description"].get(),
                                          prompt.get("1.0","end").strip(),vars["domains"].get(),vars["topics"].get())
                refresh(); self.refresh_models(); status.config(text="Saved.")
            except Exception as e: messagebox.showerror("GPT",str(e),parent=win)
        def activate():
            sel=lb.curselection()
            if not sel:return
            p=lb.profiles[sel[0]]
            try:
                self.brain.set_gpt(p["slug"]); self.gpt.set(p["name"]); refresh(); status.config(text=f"Active: {p['name']}")
            except Exception as e:messagebox.showerror("GPT",str(e),parent=win)
        def new():
            lb.selection_clear(0,"end")
            for k in vars:vars[k].set("")
            prompt.delete("1.0","end")
            status.config(text="New GPT")
        def delete():
            sel=lb.curselection()
            if not sel:return
            p=lb.profiles[sel[0]]
            if not messagebox.askyesno("Delete GPT",f"Delete {p['name']}?",parent=win):return
            try:self.brain.delete_gpt(p["slug"]);refresh();self.refresh_models()
            except Exception as e:messagebox.showerror("GPT",str(e),parent=win)
        lb.bind("<<ListboxSelect>>",lambda e:load())
        row=tk.Frame(right,bg=c["bg"]);row.pack(fill="x",pady=8)
        for label,cmd in [("New",new),("Save",save),("Activate",activate),("Delete",delete),("Refresh",refresh)]:
            tk.Button(row,text=label,command=cmd,bg=c["panel"],fg=c["fg"]).pack(side="left",padx=(0,7))
        tk.Button(row,text="Close",command=win.destroy,bg=c["panel"],fg=c["fg"]).pack(side="right")
        refresh()

    def refresh_models(self):
        models=self.brain.client.models(); self.modelbox['values']=models
        if models and self.config.model not in models: self.config.model=models[0]; self.model.set(models[0]); self.config.save_settings()
        try:
            profiles=self.brain.gpt_profiles()
            self.gptbox['values']=[p['name'] for p in profiles]
            active=self.brain.get_active_gpt()
            if active: self.gpt.set(active['name'])
        except Exception: pass
    def refresh_status(self):
        online=self.brain.client.online(); self.status.config(text='● ONLINE' if online else '● OFFLINE')
        self.status.config(fg='#55d66a' if online else '#ff5c5c'); self.connect_btn.config(text='Ollama Online' if online else 'Get Angel Online',state='disabled' if online else 'normal')
        self.refresh_models()
        try:self.kb_label.config(text=f'Knowledge: {len(self.brain.list_knowledge())} sources')
        except Exception:pass
        return online
    def connect_ollama(self):
        self.status.config(text='● STARTING…',fg='#ffb347'); self.connect_btn.config(state='disabled',text='Starting Ollama…'); threading.Thread(target=self._connect_worker,daemon=True).start()
    def _connect_worker(self):
        ok,msg=self.brain.client.start_local(); self.root.after(0,lambda:self._connect_done(ok,msg))
    def _connect_done(self,ok,msg): self.refresh_status(); self.write('Angel',msg); self.refresh_models()
    def write(self,who,text):
        self.chat.configure(state='normal')
        if who == 'You':
            self.chat.insert('end','\nYou\n','user_name')
            self.chat.insert('end',f'{text}\n','user_text')
        elif who == 'Angel':
            self.chat.insert('end','\nAngel\n','angel_name')
            self.chat.insert('end',f'{text}\n','angel_text')
        else:
            self.chat.insert('end',f'\n{who}\n{text}\n')
        self.chat.configure(state='disabled')
        self.chat.see('end')
    def clear_chat_view(self): self.chat.configure(state='normal'); self.chat.delete('1.0','end'); self.chat.configure(state='disabled')
    def _set_thinking(self, active):
        self._thinking_active=active
        if active:
            self._thinking_phase=0
            self._animate_thinking()
        elif self._thinking_job is not None:
            try:
                self.root.after_cancel(self._thinking_job)
            except Exception:
                pass
            self._thinking_job=None

    def _animate_thinking(self):
        if not self._thinking_active:
            return
        self._thinking_phase=(self._thinking_phase+1)%4
        dots="."*self._thinking_phase
        self.status.config(text=f"● THINKING{dots}",fg="#ffb347")
        self._thinking_job=self.root.after(450,self._animate_thinking)

    def send(self):
        text=self.entry.get().strip()
        if not text:return
        self.entry.delete(0,'end'); self.write('You',text); self._set_thinking(True); self.sendbtn.config(state='disabled'); threading.Thread(target=self._answer,args=(text,),daemon=True).start()
    def _answer(self,text):
        try:
            ans=self.brain.respond(text)
        except Exception as e:
            ans=f"Angel encountered an internal error while processing that request.\n\n{type(e).__name__}: {e}"
        self.root.after(0,lambda:self._finish(ans))
    def _finish(self,ans):
        self._set_thinking(False)
        self.last_answer=ans
        self.write('Angel',ans)
        try:
            self.refresh_status()
        except Exception:
            pass
        try:
            self.refresh_chats()
        except Exception:
            pass
        self.sendbtn.config(state='normal')
        self.voice.rate=self.config.speech_rate
        if self.config.voice_enabled and ans:
            try:
                self.voice.speak(ans)
            except Exception:
                pass
    def speak_last(self):
        if self.last_answer:self.voice.speak(self.last_answer)
        elif self.voice.last_text:self.voice.replay()
        else:messagebox.showinfo('Angel Voice','There is no previous Angel response to speak yet.')
    # ---- Chats ----
    def update_pin_button(self):
        row=self.brain.memory.get_conversation(self.current_chat_id())
        self.pinbtn.config(text='📌 Unpin Current Chat' if row and row[2] else '📌 Pin Current Chat')
    def refresh_chats(self):
        rows=self.brain.list_chats(); self.chat_rows=rows
        self.pinned.delete(0,'end'); self.chats.delete(0,'end')
        for r in rows:
            label=('📌 ' if r[2] else '')+(r[1] or 'New Chat')
            if r[2]: self.pinned.insert('end',f'{r[0]}  {label}')
            else:self.chats.insert('end',f'{r[0]}  {label}')
    def _id_from(self,listbox):
        sel=listbox.curselection()
        if not sel:return None
        try:return int(listbox.get(sel[0]).split()[0])
        except:return None
    def new_chat(self):
        title=simpledialog.askstring('New Chat','Chat name (optional):',parent=self.root)
        cid=self.brain.new_chat(title or 'New Chat'); self.clear_chat_view(); self.last_answer=''; self.refresh_chats(); self.update_pin_button()
        self.write('Angel',f'New chat started: {title or "New Chat"}')
    def open_chat(self,event=None):
        cid=self._id_from(self.chats)
        if cid:self.load_chat(cid)
    def open_pinned(self,event=None):
        cid=self._id_from(self.pinned)
        if cid:self.load_chat(cid)
    def load_chat(self,cid):
        try:self.brain.open_chat(cid); self.gpt.set(self.brain.current_gpt)
        except Exception as e:return messagebox.showerror('Chat',str(e))
        self.clear_chat_view()
        rows=self.brain.memory.recent_messages(100,cid)
        for m in rows:self.write('You' if m['role']=='user' else 'Angel',m['content'])
        self.last_answer=next((m['content'] for m in reversed(rows) if m['role']=='assistant'),''); self.update_pin_button()
    def current_chat_id(self): return self.brain.memory.current_id
    def pin_current(self):
        pinned=self.brain.pin_chat(self.current_chat_id()); self.refresh_chats(); self.pinbtn.config(text='📌 Unpin Current Chat' if pinned else '📌 Pin Current Chat')
    def delete_selected_chat(self):
        cid=self._id_from(self.chats) or self._id_from(self.pinned)
        if not cid:return
        if not messagebox.askyesno('Delete Chat','Delete this chat and its messages?',parent=self.root):return
        self.brain.delete_chat(cid); self.refresh_chats(); self.load_chat(self.brain.memory.current_id)
    def rename_selected_chat(self):
        cid=self._id_from(self.chats) or self._id_from(self.pinned)
        if not cid:return
        title=simpledialog.askstring('Rename Chat','New chat name:',parent=self.root)
        if title:self.brain.rename_chat(cid,title); self.refresh_chats()
    # ---- Knowledge ----

    def manage_learning(self):
        win=tk.Toplevel(self.root); self._set_window_icon(win); win.title("Angel Learning Brain"); win.geometry("1050x720"); win.minsize(900,600)
        c=self.colors(); win.configure(bg=c["bg"])
        tk.Label(win,text="Angel Learning Brain",font=("Segoe UI",18,"bold"),bg=c["bg"],fg=c["fg"]).pack(anchor="w",padx=16,pady=(14,2))
        tk.Label(win,text="SQLite learning database • derived notes never become authoritative knowledge automatically",bg=c["bg"],fg=c["muted"]).pack(anchor="w",padx=16,pady=(0,10))
        body=tk.Frame(win,bg=c["bg"]); body.pack(fill="both",expand=True,padx=16)
        left=tk.Frame(body,bg=c["bg"]); left.pack(side="left",fill="y")
        tk.Label(left,text="Topics / Goals",bg=c["bg"],fg=c["fg"]).pack(anchor="w")
        topic_lb=tk.Listbox(left,width=42,height=24,bg=c["input"],fg=c["fg"],selectbackground=c["panel"])
        topic_lb.pack(fill="y",expand=False,pady=5)
        right=tk.Frame(body,bg=c["bg"]); right.pack(side="left",fill="both",expand=True,padx=(14,0))
        out=tk.Text(right,wrap="word",bg=c["input"],fg=c["fg"],insertbackground=c["fg"],font=("Consolas",10))
        out.pack(fill="both",expand=True)
        def refresh():
            topic_lb.delete(0,"end")
            topics=self.brain.learning_topics()
            for t in topics:
                stats=self.brain.learning.topic_stats(t["id"])
                topic_lb.insert("end",f'{t["name"]} [{t["domain"]}] • {stats["notes"]} notes')
            goals=self.brain.learning_goals("queued")
            out.delete("1.0","end")
            out.insert("end",f"Topics: {len(topics)}\nQueued goals: {len(goals)}\n\n")
            if goals:
                out.insert("end","Queued learning goals:\n")
                for g in goals:
                    out.insert("end",f'- {g["topic_name"]}: {g["goal"]} ({g["level"]})\n')
        def add_topic():
            name=simpledialog.askstring("New Learning Topic","Topic name:",parent=win)
            if not name:return
            domain=simpledialog.askstring("Domain","Domain (technology, education, novel_baker, moonlit_storyroom, etc.):",initialvalue="general",parent=win) or "general"
            goal=simpledialog.askstring("Learning Goal","Optional goal:",parent=win)
            self.brain.add_learning_topic(name,domain,goal or f"Learn the fundamentals of {name}.",goal or f"Learn the fundamentals of {name}.")
            refresh()
        def self_learn():
            name=simpledialog.askstring("Self Learn","Topic Angel should study:",parent=win)
            if not name:return
            goal=simpledialog.askstring("Goal","Learning goal:",initialvalue=f"Learn {name} from Angel's local knowledge.",parent=win)
            out.delete("1.0","end"); out.insert("end","Running local self-learning session...\n")
            try:
                result=self.brain.self_learn_topic(name,goal)
                out.insert("end",f"\nProvenance: {result['provenance']}\nSources:\n")
                out.insert("end","\n".join(f"- {x}" for x in result["sources"]) or "(none)")
                out.insert("end","\n\n"+result["summary"])
                refresh()
            except Exception as e:
                messagebox.showerror("Self Learning",str(e),parent=win)
        def discover():
            made=self.brain.discover_learning_topics()
            messagebox.showinfo("Topic Discovery",f"Added {len(made)} new topic records from the local knowledge index.",parent=win)
            refresh()
        def backup():
            try:
                p=self.brain.learning.backup()
                messagebox.showinfo("Learning Backup",f"Backup created:\n{p}",parent=win)
            except Exception as e:messagebox.showerror("Backup",str(e),parent=win)
        btns=tk.Frame(win,bg=c["bg"]); btns.pack(fill="x",padx=16,pady=12)
        for label,cmd in [("Add Topic",add_topic),("Self Learn",self_learn),("Discover Topics",discover),("Backup Learning DB",backup),("Refresh",refresh)]:
            tk.Button(btns,text=label,command=cmd,bg=c["panel"],fg=c["fg"]).pack(side="left",padx=(0,7))
        tk.Button(btns,text="Close",command=win.destroy,bg=c["panel"],fg=c["fg"]).pack(side="right")
        refresh()

    def manage_knowledge(self):
        win=tk.Toplevel(self.root); self._set_window_icon(win); win.title('Angel Knowledge Library'); win.geometry('1080x700'); win.minsize(850,560); win.transient(self.root); c=self.colors(); win.configure(bg=c['bg'])
        tk.Label(win,text='Angel Knowledge Library',font=('Segoe UI',18,'bold'),bg=c['bg'],fg=c['fg']).pack(anchor='w',padx=16,pady=(14,2))
        path_var=tk.StringVar(value=str(self.brain.knowledge.library_path))
        row=tk.Frame(win,bg=c['bg']); row.pack(fill='x',padx=16,pady=(0,8)); tk.Label(row,text='Active library:',bg=c['bg'],fg=c['fg']).pack(side='left')
        tk.Entry(row,textvariable=path_var,bg=c['input'],fg=c['fg'],insertbackground=c['fg']).pack(side='left',fill='x',expand=True,padx=8)
        def choose():
            p=filedialog.askdirectory(title='Choose Angel knowledge folder')
            if p:
                self.brain.set_knowledge_path(p); path_var.set(str(self.brain.knowledge.library_path)); refresh(); self.refresh_status()
        tk.Button(row,text='Choose Folder',command=choose,bg=c['panel'],fg=c['fg']).pack(side='right')
        info=tk.Label(win,text='',anchor='w',bg=c['bg'],fg=c['muted']); info.pack(fill='x',padx=16)
        body=tk.Frame(win,bg=c['bg']); body.pack(fill='both',expand=True,padx=16,pady=4)
        left=tk.Frame(body,bg=c['bg']); left.pack(side='left',fill='y'); lb=tk.Listbox(left,width=48,height=24,font=('Segoe UI',10),bg=c['input'],fg=c['fg'],selectbackground=c['panel']); lb.pack(side='left',fill='y'); sb=tk.Scrollbar(left,command=lb.yview); sb.pack(side='right',fill='y'); lb.config(yscrollcommand=sb.set)
        right=tk.Frame(body,bg=c['bg']); right.pack(side='left',fill='both',expand=True,padx=(14,0)); preview=tk.Text(right,wrap='word',font=('Consolas',10),bg=c['input'],fg=c['fg'],insertbackground=c['fg']); preview.pack(fill='both',expand=True)
        sources=[]
        def refresh():
            nonlocal sources
            sources=self.brain.list_knowledge(); lb.delete(0,'end')
            for x in sources:lb.insert('end',f"{x['name']} | {x['topic']} | {x['chars']:,}")
            preview.delete('1.0','end'); info.config(text=f'{len(sources)} sources indexed • Backups: {self.brain.knowledge.backup_dir}')
            if sources:lb.selection_set(0);show()
        def show(_=None):
            i=lb.curselection()
            if not i:return
            try:text=self.brain.knowledge.read(sources[i[0]]['path'])
            except Exception as e:text=f'Unable to read source: {e}'
            preview.delete('1.0','end'); preview.insert('1.0',text[:80000]); preview.see('1.0')
        lb.bind('<<ListboxSelect>>',show)
        btns=tk.Frame(win,bg=c['bg']); btns.pack(fill='x',padx=16,pady=12)
        def add_files():
            ps=filedialog.askopenfilenames(title='Add knowledge files',filetypes=[('Knowledge/Text files','*.md *.txt *.py *.ps1 *.bat *.cmd *.json *.csv *.log *.ini *.cfg *.xml *.yaml *.yml *.html *.css *.js *.ts *.sql *.toml'),('All files','*.*')])
            if not ps:return
            try:self.brain.add_knowledge_many(ps); refresh(); self.refresh_status()
            except Exception as e:messagebox.showerror('Knowledge error',str(e),parent=win)
        def add_zip():
            p=filedialog.askopenfilename(title='Import knowledge ZIP',filetypes=[('ZIP archives','*.zip')])
            if not p:return
            try:
                added=self.brain.import_knowledge_zip(p); refresh(); self.refresh_status()
                messagebox.showinfo('Knowledge ZIP',f'Imported {len(added)} supported files.',parent=win)
            except Exception as e:messagebox.showerror('Knowledge ZIP',str(e),parent=win)
        def update():
            i=lb.curselection()
            if not i:return
            p=filedialog.askopenfilename(title='Choose replacement knowledge source')
            if p:
                try:self.brain.update_knowledge(sources[i[0]]['path'],p); refresh(); self.refresh_status()
                except Exception as e:messagebox.showerror('Knowledge error',str(e),parent=win)
        def remove():
            i=lb.curselection()
            if not i:return
            item=sources[i[0]]
            if messagebox.askyesno('Remove Knowledge',f"Remove '{item['name']}'? A backup will be kept.",parent=win):
                try:self.brain.remove_knowledge(item['path']); refresh(); self.refresh_status()
                except Exception as e:messagebox.showerror('Knowledge error',str(e),parent=win)
        def backup():
            n=self.brain.backup_knowledge(); messagebox.showinfo('Knowledge Backup',f'Created {n} backup copies in:\n{self.brain.knowledge.backup_dir}',parent=win)
        for text,cmd in [('Add Files',add_files),('Import ZIP',add_zip),('Update Selected',update),('Remove Selected',remove),('Refresh / Re-index',refresh),('Backup All',backup)]:
            tk.Button(btns,text=text,command=cmd,bg=c['panel'],fg=c['fg']).pack(side='left',padx=(0,7))
        tk.Button(btns,text='Close',command=win.destroy,bg=c['panel'],fg=c['fg']).pack(side='right')
        refresh()
    def add_file(self):
        p=filedialog.askopenfilename(title='Give Angel a file to review')
        if not p:return
        try:
            info=self.brain.ingest_file(p); self.write('Angel',f'I received {info["name"]} and loaded {len(info["text"]):,} characters for review. Ask me about its contents.')
        except Exception as e:messagebox.showerror('Angel file error',str(e))
def launch():
    c=Config.from_env(); b=Brain(c); root=tk.Tk(); AngelUI(root,b,Voice(c.voice_enabled,c.speech_rate)); root.mainloop()
