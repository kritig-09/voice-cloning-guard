# API Reference

Base URL for local development: `http://127.0.0.1:8000`

## `GET /health`

Returns service and model status.

## `POST /analyze`

Multipart form upload using field name `file`.

Supported formats:

`WAV, FLAC, MP3, OGG, M4A, AAC, MPEG, MPG`

Returns duration, model type, rolling-window evidence, final risk score, confidence, action, and privacy-safe evidence metadata.

## `POST /score`

Accepts a detector probability and optional context:

```json
{
  "spoof_probability": 0.82,
  "ood_score": 0.0,
  "speaker_consistency": null,
  "transaction_risk": 0.4,
  "verified_contact": false
}
```

## `WS /stream`

Receives float32 mono PCM frames at 16 kHz and returns rolling risk decisions as JSON messages.

Swagger UI is available at `/docs` when the API is running.
