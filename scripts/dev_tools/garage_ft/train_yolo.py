from ultralytics import YOLO
if __name__ == '__main__':
    m = YOLO('yolo11m.pt')
    m.train(data=r'C:\ai_lab\garage\yolo_ds\data.yaml', imgsz=960, epochs=40, batch=8, device=0, workers=4, patience=12,
            project=r'C:\ai_lab\garage\runs', name='garage_m', exist_ok=True, hsv_s=0.8, hsv_v=0.5, degrees=0, fliplr=0.0, mosaic=0.8,
            close_mosaic=8, cache=False, plots=False, verbose=False)
    print('TRAIN_DONE')
