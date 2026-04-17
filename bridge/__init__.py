"""
bridge — OpenStudio integration layer

Exposes Open Generative AI's 200+ models as native OpenMontage tools.
"""

from .asset_router import generate_image, generate_video, lipsync, estimate_cost

__all__ = ["generate_image", "generate_video", "lipsync", "estimate_cost"]
