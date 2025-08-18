from pydantic import BaseModel, Field


# LLM 평가 결과 파싱을 위한 Pydantic 모델
class EvaluationModel(BaseModel):
    score: float = Field(
        description="전반적인 답변 품질에 대한 점수 (0.0000-1.0000)",
        ge=0.0000,
        le=1.0000,
    )
    reason: str = Field(
        description="각 평가 기준에 대한 구체적인 분석과 점수에 대한 이유를 설명합니다."
    )
