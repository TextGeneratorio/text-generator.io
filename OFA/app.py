import os
from pathlib import Path

from questions.download_utils import download_model

# os.system('cd fairseq;'
#           'pip install --use-feature=in-tree-build ./; cd ..')
# os.system('ls -l')

import torch
import numpy as np
from fairseq import utils, tasks
from fairseq import checkpoint_utils
from utils.eval_utils import eval_step
from tasks.mm_tasks.caption import CaptionTask
from models.ofa import OFAModel
from PIL import Image
from torchvision import transforms
# import gradio as gr

# Register caption task
tasks.register_task('caption', CaptionTask)
# turn on cuda if GPU is available
use_cuda = torch.cuda.is_available()
# use fp16 only when GPU is available
use_fp16 = use_cuda

if Path('/models').exists():
    if not Path('/models/caption.pt').exists():
        download_model('models/caption.pt', '/models/')

elif not Path('checkpoints/caption.pt').exists():

    # os.system('wget https://ofa-silicon.oss-us-west-1.aliyuncs.com/checkpoints/caption_large_best_clean.pt; '
    #           'mkdir -p checkpoints; mv caption_large_best_clean.pt checkpoints/caption.pt')
    download_model('models/caption.pt', 'checkpoints/')
    # os.system('gsutil -m cp gs://20-questions/models/caption.pt checkpoints/caption.pt')

# Load pretrained ckpt & config
overrides = {"bpe_dir": "utils/BPE", "eval_cider": False, "beam": 5,
             "max_len_b": 16, "no_repeat_ngram_size": 3, "seed": 7}
model_path = utils.split_paths('checkpoints/caption.pt')
if Path('/models/caption.pt').exists():
    model_path = utils.split_paths('/models/caption.pt')


models, cfg, task = checkpoint_utils.load_model_ensemble_and_task(
    model_path,
    arg_overrides=overrides
)

# Move models to GPU
for model in models:
    model.eval()
    if use_fp16:
        if torch.cuda.is_bf16_supported():
            model.bfloat16()
        else:
            model.half()
    if use_cuda and not cfg.distributed_training.pipeline_model_parallel:
        model.cuda()
    model.prepare_for_inference_(cfg)

# Initialize generator
generator = task.build_generator(models, cfg.generation)

mean = [0.5, 0.5, 0.5]
std = [0.5, 0.5, 0.5]

patch_resize_transform = transforms.Compose([
    lambda image: image.convert("RGB"),
    transforms.Resize((cfg.task.patch_image_size, cfg.task.patch_image_size), interpolation=Image.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize(mean=mean, std=std),
])

patch_resize_transform_np = transforms.Compose([
    transforms.Resize((cfg.task.patch_image_size, cfg.task.patch_image_size), interpolation=Image.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize(mean=mean, std=std),
])

# Text preprocess
bos_item = torch.LongTensor([task.src_dict.bos()])
eos_item = torch.LongTensor([task.src_dict.eos()])
pad_idx = task.src_dict.pad()


def encode_text(text, length=None, append_bos=False, append_eos=False):
    s = task.tgt_dict.encode_line(
        line=task.bpe.encode(text),
        add_if_not_exist=False,
        append_eos=False
    ).long()
    if length is not None:
        s = s[:length]
    if append_bos:
        s = torch.cat([bos_item, s])
    if append_eos:
        s = torch.cat([s, eos_item])
    return s


# Construct input for caption task
def construct_sample(image: Image):
    patch_image = patch_resize_transform(image).unsqueeze(0)
    patch_mask = torch.tensor([True])
    src_text = encode_text(" what does the image describe?", append_bos=True, append_eos=True).unsqueeze(0)
    src_length = torch.LongTensor([s.ne(pad_idx).long().sum() for s in src_text])
    sample = {
        "id": np.array(['42']),
        "net_input": {
            "src_tokens": src_text,
            "src_lengths": src_length,
            "patch_images": patch_image,
            "patch_masks": patch_mask
        }
    }
    return sample

# Construct input for caption task opencv image
def construct_sample_np(image):
    patch_image = patch_resize_transform_np(image).unsqueeze(0)
    patch_mask = torch.tensor([True])
    src_text = encode_text(" what does the image describe?", append_bos=True, append_eos=True).unsqueeze(0)
    src_length = torch.LongTensor([s.ne(pad_idx).long().sum() for s in src_text])
    sample = {
        "id": np.array(['42']),
        "net_input": {
            "src_tokens": src_text,
            "src_lengths": src_length,
            "patch_images": patch_image,
            "patch_masks": patch_mask
        }
    }
    return sample


# Function to turn FP32 to (b)FP16
def apply_half(t):
    if t.dtype is torch.float32:
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        if not use_fp16:
            return t
        return t.to(dtype=dtype)
    return t


# Function for image captioning
def image_caption(Image):
    sample = construct_sample(Image)
    sample = utils.apply_to_sample(apply_half, sample) if use_fp16 else sample
    sample = utils.move_to_cuda(sample) if use_cuda else sample
    with torch.inference_mode():
        result, scores = eval_step(task, generator, models, sample)

    return result[0]['caption']

# Function for image captioning
def image_caption_np(Image): #opencv image
    sample = construct_sample_np(Image)
    sample = utils.move_to_cuda(sample) if use_cuda else sample
    sample = utils.apply_to_sample(apply_half, sample) if use_fp16 else sample
    with torch.inference_mode():
        result, scores = eval_step(task, generator, models, sample)
    return result[0]['caption']

title = "Image Captioning API"
description = "Upload your own image or click any one of the examples, and click " \
              "\"Submit\" and then wait for the generated caption.  "
article = "<p style='text-align: center'><a href='https://text-generator.io' target='_blank'>Text Generator " \
          "IO</a></p> "
examples = [['examples/stepping_stones.jpeg']]

# io = gr.Interface(fn=image_caption, inputs=gr.inputs.Image(type='pil'), outputs=gr.outputs.Textbox(label="Caption"),
#                   title=title, description=description, article=article, examples=examples,
#                   )
# app = io.launch()

