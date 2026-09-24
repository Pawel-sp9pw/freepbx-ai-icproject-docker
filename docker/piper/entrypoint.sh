#!/bin/sh
set -eu

VOICE="${PIPER_VOICE:-pl_PL-mc_speech-medium}"

if [ ! -f "/voices/${VOICE}.onnx" ]; then
  python -m piper.download_voices --download-dir /voices "${VOICE}"
fi

exec python -m piper.http_server \
  --host 0.0.0.0 \
  --port 5000 \
  -m "${VOICE}" \
  --data-dir /voices
