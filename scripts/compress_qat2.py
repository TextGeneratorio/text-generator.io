import logging
import os
from collections import OrderedDict
from typing import Dict, List
from typing import OrderedDict as OD
from typing import Union

import datasets
import numpy as np
import tensorrt as trt
import torch
import transformers
from datasets import load_dataset, load_metric
from tensorrt.tensorrt import IExecutionContext, Logger, Runtime

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    IntervalStrategy,
    PreTrainedModel,
    PreTrainedTokenizer,
    Trainer,
    TrainingArguments,
)

from transformer_deploy.backends.ort_utils import (
    cpu_quantization,
    create_model_for_provider,
    optimize_onnx,
)
from transformer_deploy.backends.pytorch_utils import convert_to_onnx
from transformer_deploy.backends.trt_utils import build_engine, get_binding_idxs, infer_tensorrt
from transformer_deploy.benchmarks.utils import print_timings, track_infer_time
from transformer_deploy.QDQModels.calibration_utils import QATCalibrate

log_level = logging.ERROR
logging.getLogger().setLevel(log_level)
datasets.utils.logging.set_verbosity(log_level)
transformers.utils.logging.set_verbosity(log_level)
transformers.utils.logging.enable_default_handler()
transformers.utils.logging.enable_explicit_format()
trt_logger: Logger = trt.Logger(trt.Logger.ERROR)
transformers.logging.set_verbosity_error()

model_name = "roberta-base"
task = "mnli"
num_labels = 3
batch_size = 32
max_seq_len = 256
validation_key = "validation_matched"
timings: Dict[str, List[float]] = dict()
runtime: Runtime = trt.Runtime(trt_logger)
profile_index = 0

def preprocess_function(examples):
    return tokenizer(
        examples["premise"], examples["hypothesis"], truncation=True, padding="max_length", max_length=max_seq_len
    )


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    if task != "stsb":
        predictions = np.argmax(predictions, axis=1)
    else:
        predictions = predictions[:, 0]
    return metric.compute(predictions=predictions, references=labels)


def convert_tensor(data: OD[str, List[List[int]]], output: str) -> OD[str, Union[np.ndarray, torch.Tensor]]:
    input: OD[str, Union[np.ndarray, torch.Tensor]] = OrderedDict()
    for k in ["input_ids", "attention_mask", "token_type_ids"]:
        if k in data:
            v = data[k]
            if output == "torch":
                value = torch.tensor(v, dtype=torch.long, device="cuda")
            elif output == "np":
                value = np.asarray(v, dtype=np.int32)
            else:
                raise Exception(f"unknown output type: {output}")
            input[k] = value
    return input


def measure_accuracy(infer, int64: bool) -> float:
    outputs = list()
    for start_index in range(0, len(encoded_dataset[validation_key]), batch_size):
        end_index = start_index + batch_size
        data = encoded_dataset[validation_key][start_index:end_index]
        inputs: OD[str, np.ndarray] = convert_tensor(data=data, output="np")
        if int64:
            for k, v in inputs.items():
                inputs[k] = v.astype(np.int64)
        output = infer(inputs)
        output = np.argmax(output[0], axis=1).astype(int).tolist()
        outputs.extend(output)
    return np.mean(np.array(outputs) == np.array(validation_labels))


def get_trainer(model: PreTrainedModel) -> Trainer:
    trainer = Trainer(
        model,
        args,
        train_dataset=encoded_dataset["train"],
        eval_dataset=encoded_dataset[validation_key],
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    transformers.logging.set_verbosity_error()
    return trainer


model_fp16: PreTrainedModel = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
trainer = get_trainer(model_fp16)
transformers.logging.set_verbosity_error()
trainer.train()
print(trainer.evaluate())

model_fp16.save_pretrained("model_trained_fp16")

tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

dataset = load_dataset("glue", task)
metric = load_metric("glue", task)

encoded_dataset = dataset.map(preprocess_function, batched=True)
validation_labels = [item["label"] for item in encoded_dataset[validation_key]]

nb_step = 1000
strategy = IntervalStrategy.STEPS
args = TrainingArguments(
    f"{model_name}-{task}",
    evaluation_strategy=strategy,
    eval_steps=nb_step,
    logging_steps=nb_step,
    save_steps=nb_step,
    save_strategy=strategy,
    learning_rate=1e-5,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size * 2,
    num_train_epochs=1,
    fp16=True,
    group_by_length=True,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    report_to=[],
)

model_fp16: PreTrainedModel = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
trainer = get_trainer(model_fp16)
transformers.logging.set_verbosity_error()
trainer.train()
print(trainer.evaluate())

model_fp16.save_pretrained("model_trained_fp16")


for percentile in [99.9, 99.99, 99.999, 99.9999]:
    with QATCalibrate(method="histogram", percentile=percentile) as qat:
        model_q: PreTrainedModel = AutoModelForSequenceClassification.from_pretrained(
            "model_trained_fp16", num_labels=num_labels
        )
        model_q = model_q.cuda()
        qat.setup_model_qat(model_q)  # prepare quantizer to any model

        with torch.no_grad():
            for start_index in range(0, 128, batch_size):
                end_index = start_index + batch_size
                data = encoded_dataset["train"][start_index:end_index]
                input_torch = {
                    k: torch.tensor(v, dtype=torch.long, device="cuda")
                    for k, v in data.items()
                    if k in ["input_ids", "attention_mask", "token_type_ids"]
                }
                model_q(**input_torch)
    trainer = get_trainer(model_q)
    print(f"percentile: {percentile}")
    print(trainer.evaluate())
