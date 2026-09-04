"""FastAPI boundary for deterministic experiment design and analysis."""

import hmac
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analysis import analyze_experiment
from .design import generate_design
from .interpreter import interpret
from .parsing import experiment_design, observation


class DesignRequest(BaseModel):
    design: dict


class AnalysisRequest(BaseModel):
    design: dict
    observation: dict


def verify_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("API_TOKEN")
    if not expected:
        return
    provided = (authorization or "").removeprefix("Bearer ")
    if not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(title="AI Experimentation Copilot", version="0.1.0")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-experimentation-copilot", "policy": "deterministic-fixed-horizon-v1"}


@app.post("/api/design", dependencies=[Depends(verify_token)])
def design_endpoint(payload: DesignRequest):
    try:
        return generate_design(experiment_design(payload.design))
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/analyze", dependencies=[Depends(verify_token)])
def analysis_endpoint(payload: AnalysisRequest):
    try:
        design = experiment_design(payload.design)
        result = analyze_experiment(design, observation(payload.observation))
        return {**result, "interpretation": interpret(result)}
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


frontend = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/assets", StaticFiles(directory=frontend), name="assets")


@app.get("/")
def home():
    return FileResponse(frontend / "index.html")
