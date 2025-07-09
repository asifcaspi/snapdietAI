from transformers import BlipProcessor, BlipForConditionalGeneration
from app.constants.device import device


class Blip:
    def __init__(self):
        self.processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-large"
        )
        self.blip_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-large"
        ).to(device)

    def generate_caption(self, image, prompts):
        captions: list[str] = []
        for prompt in prompts:
            inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(
                device
            )

            output_ids = self.blip_model.generate(
                **inputs,
                max_new_tokens=64,
                num_beams=5,
                repetition_penalty=1.3,
                no_repeat_ngram_size=3,
            )
            text = self.processor.batch_decode(output_ids, skip_special_tokens=True)[0]

            # strip the prompt prefix
            if text.lower().startswith(prompt.lower()):
                text = text[len(prompt) :].lstrip()

            captions.append(text)

        print("BLIP found:")
        for i, cap in enumerate(captions, 1):
            print(f"Prompt {i} → {cap}")

        return captions
