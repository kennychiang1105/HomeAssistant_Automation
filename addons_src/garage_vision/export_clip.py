"""建置時匯出 CLIP ViT-B/32 影像編碼器（ONNX）與車型文字向量。"""
import numpy as np
import open_clip
import torch

model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
model.eval()
tok = open_clip.get_tokenizer("ViT-B-32")
prompts = [
    "a photo of an SUV parked in a garage",
    "a photo of a sedan parked in a garage",
    "a photo of a motorcycle in a garage",
    "a photo of a pickup truck in a garage",
]
with torch.no_grad():
    t = model.encode_text(tok(prompts))
    t = t / t.norm(dim=-1, keepdim=True)
    np.save("text_embeds.npy", t.numpy().astype("float32"))


class V(torch.nn.Module):
    def __init__(self, v):
        super().__init__()
        self.v = v

    def forward(self, x):
        return self.v(x)


dummy = torch.randn(1, 3, 224, 224)
kw = dict(input_names=["image"], output_names=["emb"], opset_version=17)
try:
    torch.onnx.export(V(model.visual), dummy, "clip_visual.onnx", dynamo=False, **kw)
except TypeError:
    torch.onnx.export(V(model.visual), dummy, "clip_visual.onnx", **kw)
print("exported")
