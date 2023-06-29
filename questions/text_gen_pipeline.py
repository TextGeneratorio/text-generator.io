from transformers import TextGenerationPipeline
from transformers.pipelines import SUPPORTED_TASKS

from questions.fixtures import get_stop_reason


class TextGenPipeline(TextGenerationPipeline):
    def _forward(self, model_inputs, **generate_kwargs):
        input_ids = model_inputs["input_ids"]
        # Allow empty prompts
        if input_ids.shape[1] == 0:
            input_ids = None
            in_b = 1
        else:
            in_b = input_ids.shape[0]
        prompt_text = model_inputs.pop("prompt_text")
        generated_sequence = self.model.generate(input_ids=input_ids, **generate_kwargs)  # BS x SL

        generated_sequence = generated_sequence.sequences
        # todo use scores?
        out_b = generated_sequence.shape[0]

        if self.framework == "pt":
            generated_sequence = generated_sequence.reshape(in_b, out_b // in_b, *generated_sequence.shape[1:])
        # elif self.framework == "tf":
        #     generated_sequence = tf.reshape(generated_sequence, (in_b, out_b // in_b, *generated_sequence.shape[1:]))
        return {"generated_sequence": generated_sequence, "input_ids": input_ids, "prompt_text": prompt_text}


SUPPORTED_TASKS["text-generation"]["impl"] = TextGenPipeline
