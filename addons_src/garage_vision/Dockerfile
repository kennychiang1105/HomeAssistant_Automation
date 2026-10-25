# Stage 1：匯出模型（YOLO11 中型、CLIP ViT-B/32 影像編碼器、車型文字向量）。只在建置時用，不進最終映像。
FROM python:3.12-slim AS export
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir ultralytics open_clip_torch onnx onnxscript
WORKDIR /w
RUN yolo export model=yolo11m.pt format=onnx imgsz=640 opset=17 simplify=False
COPY export_clip.py /w/export_clip.py
RUN python export_clip.py

# Stage 2：執行環境（onnxruntime，不含 torch）
FROM python:3.12-slim
RUN pip install --no-cache-dir onnxruntime numpy pillow
COPY --from=export /w/yolo11m.onnx /models/yolo11m.onnx
COPY --from=export /w/clip_visual.onnx /models/clip_visual.onnx
COPY --from=export /w/text_embeds.npy /models/text_embeds.npy
COPY app.py /app/app.py
ENV THREADS=3
EXPOSE 8099
CMD ["python", "-u", "/app/app.py"]
