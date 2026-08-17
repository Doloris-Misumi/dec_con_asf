from .a2_fusion import A2Fusion
from .patch_dec_a2_fusion import (
    DecControlledA2Fusion,
    ForegroundGatedPatchDecA2Fusion,
    PatchDecA2Fusion,
    TaskAwareDecControlledA2Fusion,
)

__all__ = {
    'A2Fusion': A2Fusion,
    'PatchDecA2Fusion': PatchDecA2Fusion,
    'ForegroundGatedPatchDecA2Fusion': ForegroundGatedPatchDecA2Fusion,
    'DecControlledA2Fusion': DecControlledA2Fusion,
    'TaskAwareDecControlledA2Fusion': TaskAwareDecControlledA2Fusion,
}
