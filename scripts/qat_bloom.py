
import torch
from torch import nn, tensor

"""
pip install intel-extension-for-pytorch
pip install torch-quantization
"""
# import pytorch_quantization.nn as quant_nn
# from pytorch_quantization.tensor_quant import QuantDescriptor
#
# # The default tensor quantizer is set to use Max calibration method
# input_desc = QuantDescriptor(num_bits=8, calib_method="max")
# # The default tensor quantizer is set to be per-channel quantization for weights
# weight_desc = QuantDescriptor(num_bits=8, axis=((0,)))

backend = "fbgemm"  # running on a x86 CPU. Use "qnnpack" if running on ARM.
from training_data import training_data_chunks
from main import model, daemon
daemon.join()

from main import tokenizer
from main import model

from questions.text_generator_inference import DEVICE

# m = model.deepcopy()
m = model
"""set default quantizers"""

# quant_nn.QuantLinear.set_default_quant_desc_input(input_desc)
# quant_nn.QuantLinear.set_default_quant_desc_weight(weight_desc)

"""Fuse"""
# torch.quantization.fuse_modules(m, ['0','1'], inplace=True) # fuse first Conv-ReLU pair
# torch.quantization.fuse_modules(m, ['2','3'], inplace=True) # fuse second Conv-ReLU pair

"""Insert stubs"""
# m = nn.Sequential(torch.quantization.QuantStub(),
#                   m,
#                   torch.quantization.DeQuantStub())


"""create dataset"""
# xx_c = [tokenizer("Today i'm turning "+ str(i) ) for i in range(10, 50)]
xx_v = [tokenizer(chunk) for chunk in training_data_chunks]
"""Prepare"""
m.train()
m.qconfig = torch.quantization.get_default_qconfig(backend)
torch.quantization.prepare_qat(m, inplace=True)

"""Training Loop"""
n_epochs = 1
m = m.float() # do in fullprecision
opt = torch.optim.SGD(m.parameters(), lr=0.00000000001)
loss_fn = lambda out, tgt: torch.pow(tgt-out, 2).mean()

for epoch in range(n_epochs):
    for datum in xx_v:

        datum_tensor = tensor([datum['input_ids']], dtype=torch.int32, device=DEVICE)
        out = m(input_ids=datum_tensor,
                attention_mask=torch.ones(datum_tensor.shape, dtype=torch.int32, device=DEVICE),
                )
        # out_orig = model(input_ids=datum_tensor,
        #         attention_mask=torch.ones(datum_tensor.shape, dtype=torch.int32, device="cuda"),
        #         )
        # loss = loss_fn(out.logits, out_orig.logits)
        loss = loss_fn(out.logits, torch.rand_like(out.logits))
        opt.zero_grad()
        loss.backward()
        opt.step()
        print(f"loss: ${loss.item()}")

"""Convert"""
m.eval()
m = torch.quantization.convert(m, inplace=True)
m.save_pretrained("models/qat_bloom.bin")
# m.save("quantized_bloom.bin")
