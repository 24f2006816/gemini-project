#!/bin/bash

FILE="main.py"

# Backup first
cp "$FILE" "${FILE}.bak"

# Use perl for multi-line safe replacement (handles quotes better than awk)
perl -0777 -pe '
s|@app\.post\("/ready"[\s\S]*?return JSONResponse\([\s\S]*?\)\n\s*\)|@app.post("/ready", status_code=200)\nasync def receive_task(task_data: TaskRequest):\n    if not verify_secret(task_data.secret):\n        print(f"--- FAILED SECRET VERIFICATION for task {task_data.task} ---")\n        raise HTTPException(status_code=401, detail="Unauthorized: Secret does not match configured student secret.")\n\n    repo_name = task_data.task.replace(" ", "-").lower()\n    repo_url = f"https://github.com/{settings.GITHUB_USERNAME}/{repo_name}"\n    pages_url = f"https://{settings.GITHUB_USERNAME}.github.io/{repo_name}/"\n\n    print("--- TASK RECEIVED SUCCESSFULLY ---")\n    print(f"Task ID: {task_data.task}, Round: {task_data.round}")\n\n    asyncio.create_task(generate_files_and_deploy(task_data))\n\n    return JSONResponse(\n        status_code=200,\n        content={\n            "status": "processing",\n            "message": f"Task {task_data.task} received and deployment started.",\n            "repo_url": repo_url,\n            "pages_url": pages_url\n        }\n    )\n|gs' "$FILE" > temp.py && mv temp.py "$FILE"

echo "✅ main.py patched successfully! Backup saved as main.py.bak"
