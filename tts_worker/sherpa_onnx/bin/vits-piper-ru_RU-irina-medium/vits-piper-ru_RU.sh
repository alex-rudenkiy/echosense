#!/usr/bin/env bash

name=$NAME
echo "name: $name"

type=$TYPE
echo "type: $type"

set -ex

# for ru_RU-ruslan-medium.onnx
# export TYPE=ruslan
# export NAME=medium

wget -qq https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/$name/$type/ru_RU-$name-$type.onnx
wget -qq https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/$name/$type/ru_RU-$name-$type.onnx.json
wget -qq https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/$name/$type/MODEL_CARD

wget -qq https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/espeak-ng-data.tar.bz2
tar xf espeak-ng-data.tar.bz2
rm espeak-ng-data.tar.bz2

pip install piper-phonemize onnx onnxruntime==1.16.0

python3 ./vits-piper-ru_RU.py
