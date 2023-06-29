
import torch
from torch import nn
"""
pip install intel-extension-for-pytorch
pip install torch-quantization
"""
backend = "fbgemm"  # running on a x86 CPU. Use "qnnpack" if running on ARM.
from training_data import training_data_chunks
from main import model, daemon
daemon.join()

from main import tokenizer
from main import model

model_fp32 = model



# model must be set to train mode for QAT logic to work
model_fp32.train()

# attach a global qconfig, which contains information about what kind
# of observers to attach. Use 'fbgemm' for server inference and
# 'qnnpack' for mobile inference. Other quantization configurations such
# as selecting symmetric or assymetric quantization and MinMax or L2Norm
# calibration techniques can be specified here.
model_fp32.qconfig = torch.quantization.get_default_qat_qconfig('fbgemm')

# fuse the activations to preceding layers, where applicable
# this needs to be done manually depending on the model architecture
model_fp32_fused = torch.quantization.fuse_modules(model_fp32,
    [['conv', 'bn', 'relu']])

# Prepare the model for QAT. This inserts observers and fake_quants in
# the model that will observe weight and activation tensors during calibration.
model_fp32_prepared = torch.quantization.prepare_qat(model_fp32_fused)


"""set default quantizers"""

quant_nn.QuantLinear.set_default_quant_desc_input(input_desc)
quant_nn.QuantLinear.set_default_quant_desc_weight(weight_desc)

"""Fuse"""
# torch.quantization.fuse_modules(m, ['0','1'], inplace=True) # fuse first Conv-ReLU pair
# torch.quantization.fuse_modules(m, ['2','3'], inplace=True) # fuse second Conv-ReLU pair

"""Insert stubs"""
m = nn.Sequential(torch.quantization.QuantStub(),
                  m,
                  torch.quantization.DeQuantStub())


"""create dataset"""
# xx_c = [tokenizer("Today i'm turning "+ str(i) ) for i in range(10, 50)]
xx_v = [tokenizer(chunk) for chunk in training_data_chunks]
"""Prepare"""
m.train()
m.qconfig = torch.quantization.get_default_qconfig(backend)
torch.quantization.prepare_qat(m, inplace=True)

"""Training Loop"""
n_epochs = 1
opt = torch.optim.SGD(m.parameters(), lr=0.1)
loss_fn = lambda out, tgt: torch.pow(tgt-out, 2).mean()
for epoch in range(n_epochs):
    for datum in xx_v:

        out = m(input_ids=datum, )
        loss = loss_fn(out, torch.rand_like(out))
        opt.zero_grad()
        loss.backward()
        opt.step()

"""Convert"""
m.eval()
m = torch.quantization.convert(m, inplace=True)
m.save("quantized_bloom.bin")
