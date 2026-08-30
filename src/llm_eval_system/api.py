from functools import lru_cache

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .experiments import Experiment, PROMPTS
from .llm import LLMClient
from .models import ChatRequest, ChatResponse, FeedbackRequest
from .observability import Observability

app = FastAPI(title="LLM Eval System", version="0.1.0")


@lru_cache
def services():
    settings = get_settings()
    return settings, LLMClient(settings), Observability(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings, llm, obs = services()
    experiment = Experiment(
        name=f"{request.scenario}-prompt-v1",
        variant_b_percent=settings.ab_variant_b_percent,
        salt=settings.ab_salt,
    )
    variant = experiment.assign(request.user_id)
    prompt = PROMPTS[request.scenario][variant]
    metadata = {"experiment": experiment.name, "variant": variant, "scenario": request.scenario}

    try:
        with obs.generation(
            name=request.scenario,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=metadata,
            input={"message": request.message, "contexts": request.contexts},
        ) as handle:
            answer = await llm.answer(prompt, request.message, request.contexts)
            obs.end(handle, output=answer, model=settings.llm_model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="模型服务暂时不可用") from exc

    return ChatResponse(answer=answer, variant=variant, trace_id=handle.id, model=settings.llm_model)


@app.post("/v1/feedback")
def feedback(request: FeedbackRequest) -> dict[str, str]:
    _, _, obs = services()
    if request.thumbs_up is not None:
        obs.score(request.trace_id, "thumbs_up", float(request.thumbs_up), request.comment)
    if request.resolved is not None:
        obs.score(request.trace_id, "resolved", float(request.resolved), request.comment)
    if request.csat is not None:
        obs.score(request.trace_id, "csat", float(request.csat), request.comment)
    return {"status": "recorded"}

