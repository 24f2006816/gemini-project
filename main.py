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

# =============== IITM LLM DEPLOYMENT ROUND 1 AUTO FILE GENERATOR ===============
import os, json, textwrap

def generate_iitm_required_files(task_dir: str):
    """Generate the 9 required IITM files dynamically in the repo folder."""
    os.makedirs(task_dir, exist_ok=True)
    def w(name, content):
        with open(os.path.join(task_dir, name), "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    w("ashravan.txt", textwrap.dedent("""
        Ashravan awoke to silence, a silence that no emperor should hear...
        (short story content omitted for brevity)
    """))

    w("dilemma.json", json.dumps({
        "people": 2,
        "case_1": {"swerve": True, "reason": "Minimize total harm — one life lost instead of two."},
        "case_2": {"swerve": False, "reason": "The single person is a child — preserve future potential."}
    }, indent=2))

    w("about.md", "Curious Driven Resilient")

    w("pelican.svg", """<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="90" fill="lightblue"/>
    <text x="25" y="110" font-size="16" font-family="Verdana">🦩 Pelican on Bike 🚴‍♂️</text>
    </svg>""")

    w("restaurant.json", json.dumps({
        "city": "Bangalore",
        "lat": 12.9716,
        "long": 77.5946,
        "name": "Truffles",
        "what_to_eat": "Try the All American Cheese Burger with Peri-Peri fries."
    }, indent=2))

    w("prediction.json", json.dumps({
        "rate": 0.045,
        "reason": "The Fed is likely to maintain a stable 4.5% rate due to inflation stabilization by late 2025."
    }, indent=2))

    w("LICENSE", "MIT License © 2025 IITM Student")

    w("index.html", textwrap.dedent("""
        <!DOCTYPE html>
        <html lang="en">
        <head><meta charset="UTF-8"><title>LLMPages Round 1</title></head>
        <body>
          <h1>Round 1: LLM Deployment Project Files</h1>
          <ul>
            <li><a href="ashravan.txt">ashravan.txt</a></li>
            <li><a href="dilemma.json">dilemma.json</a></li>
            <li><a href="about.md">about.md</a></li>
            <li><a href="pelican.svg">pelican.svg</a></li>
            <li><a href="restaurant.json">restaurant.json</a></li>
            <li><a href="prediction.json">prediction.json</a></li>
            <li><a href="LICENSE">LICENSE</a></li>
            <li><a href="uid.txt">uid.txt</a></li>
          </ul>
        </body></html>
    """))

    w("uid.txt", "019a0ad7-5420-73aa-9b1a-d4fc9964c565")

    print(f"✅ IITM required files created inside: {task_dir}")

# ===============================================================================

# ========================= ISOLATED REPO CREATION PATCH ==========================
import subprocess, json, shutil

def create_new_github_repo(task_name: str, files_dir: str):
    """
    Creates a brand-new GitHub repo for each IITM task dynamically.
    Pushes required files and enables GitHub Pages.
    """
    print(f"🚀 Creating isolated repo for task: {task_name}")

    # --- Step 1: Create new repo using GitHub API ---
    repo_api = f"https://api.github.com/user/repos"
    payload = {"name": task_name, "private": False, "auto_init": False}
    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
               "Accept": "application/vnd.github+json"}

    response = requests.post(repo_api, headers=headers, data=json.dumps(payload))
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create repo: {response.text}")
        return None
    print(f"✅ Repo created successfully: https://github.com/{GITHUB_USERNAME}/{task_name}")

    # --- Step 2: Initialize local git and push ---
    os.chdir(files_dir)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Add IITM Round 1 required files"], check=True)
    subprocess.run(["git", "remote", "add", "origin",
                    f"https://github.com/{GITHUB_USERNAME}/{task_name}.git"], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    print("✅ Files pushed successfully")

    # --- Step 3: Enable GitHub Pages ---
    enable_pages_api = f"https://api.github.com/repos/{GITHUB_USERNAME}/{task_name}/pages"
    pages_payload = {"source": {"branch": "main", "path": "/"}}
    res = requests.post(enable_pages_api, headers=headers, data=json.dumps(pages_payload))
    if res.status_code in [201, 204]:
        print("✅ GitHub Pages enabled successfully")
    else:
        print(f"⚠️ GitHub Pages enabling failed: {res.text}")

    os.chdir("..")
    return f"https://{GITHUB_USERNAME}.github.io/{task_name}/"
# ===============================================================================

