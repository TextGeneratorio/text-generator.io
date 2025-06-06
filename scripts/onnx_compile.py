"""
pip install onnxruntime-gpu

"""

from transformers import AutoTokenizer, GPT2TokenizerFast

from onnxruntime import InferenceSession
import numpy as np
import os
import subprocess
import logging
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

if not os.path.exists("models/neo-causal-lm"):
    try:
        subprocess.run(['python3', '-m', 'transformers.onnx',
                        '--model=models/gpt-neo-1.3B',
                        '--feature=causal-lm',
                        'models/neo-causal-lm/'])
    except Exception as e:
        print("Failed to run onnx")
        logger.error(e)

## inference
session = InferenceSession("models/neo-causal-lm/model.onnx",
                           providers=['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider'])
# if "CUDAExecutionProvider" in session.get_providers():
#     # session.set_providers(["CUDAExecutionProvider", "CPUExecutionProvider"])
#     session.set_providers(["CUDAExecutionProvider"])
tokenizer = GPT2TokenizerFast.from_pretrained("models/gpt-neo-1.3B")
# ONNX Runtime expects NumPy arrays as input
inputs = tokenizer("Using DistilBERT with ONNX Runtime!", return_tensors="np")
# outputs = session.run(output_names=["last_hidden_state"], input_feed=dict(inputs))

# 1x1x15x2048
# print (outputs[0][0])
# print (outputs)


# test on 10 or 1k token inputs
inputs = {'input_ids': np.array([[27, 91, 3605, 20500, 91, 29, 314, 588, 22514, 13,
                                  1052]]), 'past_key_values': None,  # 'use_cache': True,
          # 'position_ids': np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]),
          'attention_mask': np.array([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]), 'token_type_ids': None}

inputs = {'input_ids': np.array([[27, 91, 3605, 20500, 91, 29, 314, 588, 22514, 13] * 100]), 'past_key_values': None,
          # 'use_cache': True,
          # 'position_ids': np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]),
          'attention_mask': np.array([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1] * 100]),
          'token_type_ids': None}
% time
outputs = session.run(output_names=["logits"], input_feed=dict(inputs))
