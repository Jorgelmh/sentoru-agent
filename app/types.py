from pydantic import BaseModel


class GitPatch(BaseModel):
    file: str
    position: int
    patch: str
    comment: str

class FixerAgentOutput(BaseModel):
    patches: list[GitPatch]
    comment: str
