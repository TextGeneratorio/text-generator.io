import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

from questions.utils import log_time
set_seed(42)

mm1b = AutoModelForCausalLM.from_pretrained("models/tg-7b1")
tokenizer1b = AutoTokenizer.from_pretrained("models/tg-7b1")
mm1b.eval()
mm1b = mm1b.bfloat16()
mm1b.eval()
# mm1b.save_pretrained("models/tgc-bf16")
# with log_time("compile"):
#     mm1b = torch.compile(mm1b)

# check model move back and forward
mm1b = mm1b.cuda()
# mm1b = mm1b.to("cpu")
# mm1b = mm1b.to("cpu")
# mm1b = mm1b.to("cuda")
# mm1b = mm1b.to("cpu")

# textgeneration piepline
from transformers import pipeline
# pipe = pipeline("text-generation", model=mm1b, tokenizer=tokenizer1b, device=0)
pipe = pipeline("text-generation", model=mm1b, tokenizer=tokenizer1b, device=0)
with log_time("pipeline"):
    newpipe = pipe("Hello, my dog is cute")
print(newpipe)
exit()
mm1b = mm1b.to("cpu")
mm1b = mm1b.to("cpu")

m = AutoModelForCausalLM.from_pretrained("models/tgc")
tokenizer = AutoTokenizer.from_pretrained("models/tgc")
m.eval()
m = m.bfloat16()
m.eval()
# m.save_pretrained("models/tgc-bf16")

# check model move back and forward
m = m.cuda()
m = m.to("cpu")
m = m.to("cuda")
# m = m.to("cpu")

# textgeneration piepline
from transformers import pipeline
pipe = pipeline("text-generation", model=m, tokenizer=tokenizer, device=0)
pipe = pipeline("text-generation", model=m, tokenizer=tokenizer, device=0)
l = pipe("Hello, my dog is cute")
print(l)

m = m.to("cpu")
m = m.to("cpu")
m = m.to("cuda")

l = pipe("Hello, my dog is cute")
m = m.to("cpu")
print(l)
# redopipeline?
pipe = pipeline("text-generation", model=m, tokenizer=tokenizer, device=0)
l = pipe("Hello, my dog is cute")
m = m.to("cpu")
print(l)
# load another model

mm1b = AutoModelForCausalLM.from_pretrained("models/tg-7b1")
tokenizer1b = AutoTokenizer.from_pretrained("models/tg-7b1")
mm1b.eval()
mm1b = mm1b.bfloat16()
mm1b.eval()
# mm1b.save_pretrained("models/tgc-bf16")

# check model move back and forward
mm1b = mm1b.cuda()
mm1b = mm1b.to("cpu")
mm1b = mm1b.to("cuda")
# mm1b = mm1b.to("cpu")

# textgeneration piepline
from transformers import pipeline
pipe = pipeline("text-generation", model=mm1b, tokenizer=tokenizer1b, device=0)
newpipe = pipe("Hello, my dog is cute")
mm1b = mm1b.to("cpu")
mm1b = mm1b.to("cuda")

newpipe = pipe("Hello, my dog is cute")
mm1b = mm1b.to("cpu")
print(newpipe)

# old model in out
m = m.to("cpu")
m = m.to("cuda")

l = pipe("Hello, my dog is cute")
m.to("cpu")

print(l)

mm1b = mm1b.to("cpu")
mm1b = mm1b.to("cuda")

newpipe = pipe("Hello, my dog is cute")
mm1b.to("cpu")

print(newpipe)

# old model in out
m = m.to("cpu")
m = m.to("cuda")

l = pipe("Hello, my dog is cute")
m.to("cpu")
print(l)
