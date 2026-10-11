"""EKS Web API — connects robot-sim.html to real DeepSeek + Laya"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn, shutil, os

from eks.eks import EKS

app = FastAPI(title="EKS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global EKS instance
eks: EKS | None = None

class DecideRequest(BaseModel):
    input: str

class SeedRequest(BaseModel):
    domain: str
    description: str

@app.post("/seed")
def seed(req: SeedRequest):
    global eks
    # clear old core for fresh start
    if os.path.exists("./eks_core"):
        shutil.rmtree("./eks_core")
    eks = EKS(
        domain=req.domain,
        description=req.description,
        laya_model="aac6fef/laya-mlx",
        llm_url="http://localhost:8001/v1",
        storage="./eks_core",
    )
    schema = eks.core.get_current(req.domain)
    return {
        "ok": True,
        "schema_version": schema.version,
        "schema_name": schema.name,
        "fields": schema.question_names(),
    }

@app.post("/decide")
def decide(req: DecideRequest):
    if not eks:
        return {"error": "not seeded"}
    schema_before = eks.core.get_current(eks.domain)
    v_before = schema_before.version if schema_before else 0

    answers = eks.decide(req.input)

    schema_after = eks.core.get_current(eks.domain)
    v_after = schema_after.version if schema_after else 0
    evolved = v_after > v_before

    return {
        "answers": {
            k: {
                "answer": v.get("answer"),
                "confidence": round(float(v.get("confidence", 0)), 3),
            }
            for k, v in answers.items()
        },
        "evolved": evolved,
        "schema_version": v_after,
        "schema_name": schema_after.name if schema_after else "",
        "fields": schema_after.question_names() if schema_after else [],
    }

@app.get("/status")
def status():
    if not eks:
        return {"seeded": False}
    schema = eks.core.get_current(eks.domain)
    history = []
    if schema:
        for s in eks.core._schemas.values():
            if s.domain == eks.domain:
                history.append({
                    "version": s.version,
                    "name": s.name,
                    "trigger": s.issue_that_triggered,
                    "fields": s.question_names(),
                })
    return {
        "seeded": True,
        "domain": eks.domain,
        "schema_version": schema.version if schema else 0,
        "schema_name": schema.name if schema else "",
        "fields": schema.question_names() if schema else [],
        "history": sorted(history, key=lambda x: x["version"]),
    }

@app.post("/reset")
def reset():
    global eks
    eks = None
    if os.path.exists("./eks_core"):
        shutil.rmtree("./eks_core")
    return {"ok": True}

@app.get("/logs")
def get_logs(limit: int = 50):
    if not eks:
        return {"error": "not seeded", "logs": []}
    return {
        "logs": eks.log.all_for_api(eks.domain, limit=limit),
        "stats": eks.log.stats(eks.domain),
    }

@app.get("/logs/stats")
def get_stats():
    if not eks:
        return {"error": "not seeded"}
    return eks.log.stats(eks.domain)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")
