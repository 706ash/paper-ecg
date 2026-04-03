from typing import Dict, List, Optional
import dataclasses

from model.Lead import LeadId, Lead, GridBox


@dataclasses.dataclass(frozen=True)
class InputParameters:
    rotation: int
    timeScale: int
    voltScale: int
    leads: Dict[LeadId, Lead]
    gridBoxes: List[GridBox] = dataclasses.field(default_factory=list)
    baselineYs: Dict[int, float] = dataclasses.field(default_factory=dict)  # {baselineId: y_position}
