#! /bin/bash

python ../apps/plm/generate.py --ckpt /media/intern/HDD-2TB/plmodel/Perception-LM-1B  --media_type image  --media_path "$1" --question "$2"