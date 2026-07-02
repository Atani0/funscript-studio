from __future__ import annotations


class DeepMotionModel:
    """Reserved interface for future local deep models.

    Planned model families:
    - action_probability_model
    - amplitude_regression_model
    - density_prediction_model
    - style_embedding_model
    """

    def train(self, training_samples):
        raise NotImplementedError

    def predict_motion_plan(self, perception_segments, candidate_events, learned_profile):
        raise NotImplementedError

    def save(self, path):
        raise NotImplementedError

    def load(self, path):
        raise NotImplementedError

