import librosa
import numpy as np

TARGET_SR = 16000


def extract_features(waveform: np.ndarray, sample_rate: int) -> np.ndarray:
    """Extract a fixed-length rich acoustic feature vector."""

    waveform = np.asarray(waveform, dtype=np.float32)
    if waveform.ndim > 1:
        waveform = np.mean(waveform, axis=1)
    if waveform.size == 0:
        raise ValueError("Empty audio.")

    if sample_rate != TARGET_SR:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=TARGET_SR)

    peak = float(np.max(np.abs(waveform)))
    if peak == 0:
        raise ValueError("Audio is silent.")
    waveform = waveform / peak

    features: list[float] = []

    mfcc = librosa.feature.mfcc(y=waveform, sr=TARGET_SR, n_mfcc=13)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2) if mfcc.shape[1] >= 9 else np.gradient(delta, axis=1)

    for matrix in (mfcc, delta, delta2):
        features.extend(np.mean(matrix, axis=1).tolist())
        features.extend(np.std(matrix, axis=1).tolist())

    spectral_features = (
        librosa.feature.spectral_centroid(y=waveform, sr=TARGET_SR),
        librosa.feature.spectral_bandwidth(y=waveform, sr=TARGET_SR),
        librosa.feature.spectral_rolloff(y=waveform, sr=TARGET_SR),
        librosa.feature.zero_crossing_rate(waveform),
        librosa.feature.rms(y=waveform),
    )

    for feature in spectral_features:
        features.append(float(np.mean(feature)))
        features.append(float(np.std(feature)))

    contrast = librosa.feature.spectral_contrast(y=waveform, sr=TARGET_SR)
    features.extend(np.mean(contrast, axis=1).tolist())
    features.extend(np.std(contrast, axis=1).tolist())

    return np.asarray(features, dtype=np.float32)
