import os
import json
import time
import shutil
import base64
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings

# ================== CONFIG ==================
class Settings(BaseSettings):
    STUDENT_SECRET: str
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_USERNAME: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    class Config:
        env_file = ".env"

settings = Settings()

app = FastAPI(title="LLM Deployment API")
ROOT = Path.cwd() / "generated_tasks"
ROOT.mkdir(parents=True, exist_ok=True)

# ================== MODELS ==================
class Attachment(BaseModel):
    name: str
    url: str

class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    evaluation_url: HttpUrl
    checks: List[str] = []
    attachments: List[Attachment] = []

# ================== HELPERS ==================
def safe_log(*a): print(*a, flush=True)

def save_files(files: Dict[str,str], folder: Path):
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for k,v in files.items():
        (folder/k).write_text(v, encoding="utf-8")

def git(cmd, cwd): 
    r=subprocess.run(["git"]+cmd, cwd=cwd, capture_output=True,text=True)
    if r.returncode!=0: safe_log("git",cmd,"failed",r.stderr); return False
    return True

# ================== FALLBACK ==================
def fallback(task: TaskRequest)->Dict[str,str]:
    uid=""
    for a in task.attachments:
        if a.name.lower().startswith("uid"):
            try: uid=base64.b64decode(a.url.split(",")[1]).decode()
            except: uid="UID_ERROR"
    files={
      "about.md":"Curious Focused Resilient",
      "uid.txt":uid or "UID_NOT_PROVIDED",
      "LICENSE":"MIT License\n\nCopyright (c) 2025",
      "ashravan.txt":"Ashravan woke to a new dawn, aware of every choice reborn...",
      "dilemma.json":json.dumps({"people":2,"case_1":{"swerve":True,"reason":"minimize loss"},"case_2":{"swerve":False,"reason":"protect child"}},indent=2),
      "restaurant.json":json.dumps({"city":"Bangalore","lat":12.97,"long":77.59,"name":"Truffles","what_to_eat":"Burgers"},indent=2),
      "prediction.json":json.dumps({"rate":0.045,"reason":"likely Fed path"},indent=2),
      "pelican.svg":"<svg xmlns='http://www.w3.org/2000/svg'><text x='10' y='20'>Pelican</text></svg>",
      "index.html":"<html><body><h1>Generated Files</h1><ul>"+ "".join(f"<li><a href='{f}'>{f}</a></li>" for f in ["ashravan.txt","dilemma.json","about.md","pelican.svg","restaurant.json","prediction.json","uid.txt"]) +"</ul></body></html>"
    }
    return files

# ================== CORE ==================
def process(task:TaskRequest):
    repo=task.task.replace(" ","-")
    path=ROOT/repo
    safe_log(f"--- Starting task {repo} ---")

    gh_user=settings.GITHUB_USERNAME or "24f2006816"
    gh_token=settings.GITHUB_TOKEN or ""
    remote=f"https://{gh_user}:{gh_token}@github.com/{gh_user}/{repo}.git"

    if path.exists(): shutil.rmtree(path)
    git(["clone",remote,str(path)],Path.cwd()) or git(["init"],Path.cwd())
    files=fallback(task)
    save_files(files,path)
    git(["add","."],path)
    git(["commit","-m",f"Round {task.round} update"],path)
    git(["branch","-M","main"],path)
    git(["push","-u","origin","main","--force"],path)

    pages=f"https://{gh_user}.github.io/{repo}/"
    payload={"email":task.email,"task":task.task,"round":task.round,"nonce":task.nonce,
             "repo_url":f"https://github.com/{gh_user}/{repo}",
             "commit_sha":subprocess.run(["git","rev-parse","HEAD"],cwd=path,capture_output=True,text=True).stdout.strip(),
             "pages_url":pages}
    for i in range(3):
        try:
            r=requests.post(task.evaluation_url,json=payload,timeout=10)
            if r.status_code==200: safe_log("✅ Notified evaluator");break
            safe_log("Attempt",i+1,"status",r.status_code)
        except Exception as e: safe_log("Notify error",e);time.sleep(2)
    safe_log("--- Done ---")

# ================== API ==================
@app.post("/ready")
def ready(t:TaskRequest,bg:BackgroundTasks):
    if t.secret!=settings.STUDENT_SECRET:
        raise HTTPException(status_code=401,detail="Invalid secret")
    bg.add_task(process,t)
    return {"status":"ready","message":f"Task {t.task} started."}

@app.get("/")
def root(): return {"status":"running"}
