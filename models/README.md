# Model artifacts

VoiceCloneGuard keeps model binaries outside Git by default because they can be large and may be tied to a specific scikit-learn runtime.

Place either of these files here for local inference:

- `voice_cloning_model.pkl` — original detector model; class 0 = AI-cloned, class 1 = real.
- `improved_voice_model.pkl` — prototype rich-feature model produced by `train_improved_model.py`; class 0 = real, class 1 = AI-cloned.

The application prefers `improved_voice_model.pkl` when it exists and otherwise falls back to `voice_cloning_model.pkl`.

Do not upload private, copyrighted, or personally identifying audio samples to the repository.
