from typing import Any, Dict, List, Optional
from pathlib import Path

from galaxea_fm.models.galaxea_zero.paligemma.tokenizer import PaliGemmaTokenizer
from galaxea_fm.processors.base_processor import BaseProcessor


class GalaxeaZeroProcessor(BaseProcessor):
    """Compatibility wrapper for older G0/G0Plus checkpoint processor configs."""

    @staticmethod
    def _rewrite_local_tokenizer_path(tokenizer_params: Dict[str, Any]) -> Dict[str, Any]:
        tokenizer_params = dict(tokenizer_params)
        model_path = tokenizer_params.get("pretrained_model_name_or_path")
        if not isinstance(model_path, str) or not model_path.startswith("/data/google/"):
            return tokenizer_params

        candidate_google_dirs = [
            Path.home() / "g0plus_ros2" / "data" / "google",
            Path.home() / "r1lite_infer_bundle" / "google" / "paligemma-3b-pt-224",
        ]
        local_google_dir = next((path for path in candidate_google_dirs if path.exists()), None)
        if local_google_dir is None:
            return tokenizer_params

        tokenizer_params["pretrained_model_name_or_path"] = str(local_google_dir)
        return tokenizer_params

    def __init__(
        self,
        shape_meta: Dict[str, Any],
        num_obs_steps: int,
        action_state_transforms: Optional[List[Any]],
        use_stepwise_action_norm,
        norm_default_mode,
        norm_exception_mode,
        action_state_merger,
        train_transforms,
        val_transforms,
        num_output_cameras: int,
        use_zh_instruction: bool,
        drop_high_level_prob: float,
        pad_token_id: int,
        image_token_index: int,
        tokenizer_params: Dict[str, Any],
        max_text_tokens: int,
        max_image_text_tokens: int,
        num_input_cameras: int,
        num_image_tokens_per_camera: int,
    ):
        del max_image_text_tokens

        tokenizer_params = self._rewrite_local_tokenizer_path(tokenizer_params)

        tokenizer = PaliGemmaTokenizer(
            tokenizer_params=tokenizer_params,
            pad_token_id=pad_token_id,
            image_token_index=image_token_index,
            max_text_tokens=max_text_tokens,
            num_tokens_per_image=num_image_tokens_per_camera,
            num_input_images=num_input_cameras,
        )

        action_output_dim = sum(int(meta["shape"]) for meta in shape_meta["action"])
        proprio_output_dim = sum(int(meta["shape"]) for meta in shape_meta["state"])

        super().__init__(
            shape_meta=shape_meta,
            num_obs_steps=num_obs_steps,
            num_output_cameras=num_output_cameras,
            action_output_dim=action_output_dim,
            proprio_output_dim=proprio_output_dim,
            action_state_transforms=action_state_transforms,
            use_stepwise_action_norm=use_stepwise_action_norm,
            norm_default_mode=norm_default_mode,
            norm_exception_mode=norm_exception_mode,
            action_state_merger=action_state_merger,
            train_transforms=train_transforms,
            val_transforms=val_transforms,
            drop_high_level_prob=drop_high_level_prob,
            use_zh_instruction=use_zh_instruction,
            tokenizer=tokenizer,
        )
