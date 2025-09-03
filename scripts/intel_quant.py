import intel_extension_for_pytorch as ipex
import torch
import torch.nn as nn

from main import daemon, model

daemon.join()

from main import tokenizer


class MyModel(nn.Module):
    def __init__(self):
        super(MyModel, self).__init__()
        self.conv = nn.Conv2d(10, 10, 3)

    def forward(self, x):
        x = self.conv(x)
        return x


model = model

# user dataset for calibration.
# user dataset for validation.
xx_c = [tokenizer("Today i'm turning " + str(i)) for i in range(20)]
xx_v = [tokenizer("Today is a great day, on my birthday i'm turning " + str(i)) for i in range(20)]

conf = ipex.quantization.QuantConf(qscheme=torch.per_tensor_affine)

with torch.no_grad():
    for x in xx_c:
        with ipex.quantization.calibrate(conf):
            y = model(x)

conf.save("configure.json")
conf = ipex.quantization.QuantConf("configure.json")


with torch.no_grad():
    trace_model = ipex.quantization.convert(model, conf, tokenizer("Hi whats the weather looking like today"))

with torch.no_grad():
    for x in xx_v:
        y = trace_model(x)
trace_model.save("quantization_model.pt")

loaded = torch.jit.load("quantization_model.pt")
