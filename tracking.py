import os
import sys
import cv2
import torch
import numpy as np

# Add local 'yolov5' and 'deep_sort' directories to sys.path
sys.path.append(os.path.abspath('./yolov5'))
sys.path.append(os.path.abspath('./deep_sort'))

# Import YOLOv5 modules
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import (non_max_suppression, scale_coords, check_img_size)
from yolov5.utils.datasets import letterbox
from yolov5.utils.torch_utils import select_device

# Import DeepSORT modules
from deep_sort.utils.parser import get_config
from deep_sort.deep_sort import DeepSort

def main():
    # Initialize webcam
    cap = cv2.VideoCapture(0)  # 0 is the default webcam
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Initialize device
    device = select_device('')  # Set to 'cpu' or '0' for GPU
    half = device.type != 'cpu'  # Half precision only supported on CUDA

    # Load YOLOv5 model
    yolo_weights = './yolov5/yolov5s.pt'  # Path to your YOLOv5 weights
    model = DetectMultiBackend(yolo_weights, device=device)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = 640  # Set your desired image size
    imgsz = check_img_size(imgsz, s=stride)

    if half:
        model.model.half()

    # Initialize DeepSORT
    cfg = get_config()
    cfg.merge_from_file("./deep_sort/configs/deep_sort.yaml")

    deepsort = DeepSort(
        cfg.DEEPSORT.REID_CKPT,
        max_dist=cfg.DEEPSORT.MAX_DIST,
        min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
        nms_max_overlap=cfg.DEEPSORT.NMS_MAX_OVERLAP,
        max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
        max_age=cfg.DEEPSORT.MAX_AGE,
        n_init=cfg.DEEPSORT.N_INIT,
        nn_budget=cfg.DEEPSORT.NN_BUDGET,
        use_cuda=True if device.type != 'cpu' else False
    )

    # Start video processing
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Pre-process the frame for YOLOv5
        img = letterbox(frame, imgsz, stride=stride)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3xHxW
        img = np.ascontiguousarray(img)

        # Convert to torch tensor
        img_tensor = torch.from_numpy(img).to(device)
        img_tensor = img_tensor.half() if half else img_tensor.float()  # uint8 to fp16/32
        img_tensor /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img_tensor.ndimension() == 3:
            img_tensor = img_tensor.unsqueeze(0)

        # Inference
        pred = model(img_tensor, augment=False, visualize=False)

        # Apply NMS
        conf_thres = 0.4
        iou_thres = 0.5
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes=None, agnostic=False)

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            if det is not None and len(det):
                # Rescale boxes to original image
                det[:, :4] = scale_coords(img_tensor.shape[2:], det[:, :4], frame.shape).round()

                # Prepare detections for DeepSORT
                bbox_xywh = []
                confs = []
                class_ids = []

                for *xyxy, conf, cls in det:
                    x_c, y_c, w, h = bbox_rel(*xyxy)
                    bbox_xywh.append([x_c, y_c, w, h])
                    confs.append(conf.item())
                    class_ids.append(int(cls.item()))

                # Convert to numpy arrays
                bbox_xywh = np.array(bbox_xywh)
                confs = np.array(confs)
                class_ids = np.array(class_ids)

                # Pass detections to DeepSORT
                outputs = deepsort.update(bbox_xywh, confs, class_ids, frame)

                # Draw tracking results
                if len(outputs) > 0:
                    for j, (output, conf) in enumerate(zip(outputs, confs)):
                        x1, y1, x2, y2, track_id, cls_id = output
                        bbox = [int(x1), int(y1), int(x2), int(y2)]
                        class_name = names[cls_id]
                        color = compute_color_for_labels(track_id)
                        label = f"{track_id} {class_name}"

                        plot_one_box(bbox, frame, label=label, color=color, line_thickness=2)

            else:
                deepsort.increment_ages()

        # Display the resulting frame
        cv2.imshow('Object Tracking', frame)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

def bbox_rel(x1, y1, x2, y2):
    """Calculate relative bounding box coordinates (center x, center y, width, height)."""
    x_c = (x1 + x2) / 2
    y_c = (y1 + y2) / 2
    w = x2 - x1
    h = y2 - y1
    return x_c, y_c, w, h

def compute_color_for_labels(label):
    """Assign a fixed color to each label."""
    palette = (2 ** 11 - 1, 2 ** 15 -1, 2**20 -1)
    color = [int((p * (label + 1)) % 255) for p in palette]
    return tuple(color)

def plot_one_box(bbox, img, color=None, label=None, line_thickness=None):
    """Draw bounding box on the image."""
    tl = line_thickness or 2
    color = color or [0, 255, 0]
    x1, y1, x2, y2 = bbox
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness=tl)
    if label:
        font_scale = 0.5
        t_size = cv2.getTextSize(label, 0, font_scale, thickness=tl)[0]
        y1 = y1 - t_size[1] - 3 if y1 - t_size[1] - 3 > 0 else y1 + t_size[1] + 3
        cv2.rectangle(img, (x1, y1), (x1 + t_size[0], y1 + t_size[1] + 3), color, -1)
        cv2.putText(img, label, (x1, y1 + t_size[1] + 3), 0, font_scale, (255, 255, 255), thickness=tl, lineType=cv2.LINE_AA)

if __name__ == '__main__':
    main()

