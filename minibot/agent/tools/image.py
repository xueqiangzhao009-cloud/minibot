import logging
import os
from typing import Optional, List, Dict, Any

import cv2
import numpy as np
from PIL import Image
import pytesseract
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from diffusers import StableDiffusionPipeline

logger = logging.getLogger(__name__)

class ImageAnalysisTool:
    """图像分析工具，识别图像内容并描述"""
    
    name = "image_analysis"
    description = "分析图像内容并生成描述"
    
    def __init__(self):
        try:
            self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        except Exception as e:
            logger.warning(f"初始化BLIP模型失败: {e}")
            self.processor = None
            self.model = None
    
    async def run(self, image_path: str) -> str:
        """分析图像内容
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像描述
        """
        try:
            if self.model is None:
                return "错误: 未初始化BLIP模型"
            
            if not os.path.exists(image_path):
                return "错误: 图像文件不存在"
            
            logger.info(f"分析图像: {image_path}")
            
            # 加载图像
            image = Image.open(image_path).convert("RGB")
            
            # 生成描述
            inputs = self.processor(image, return_tensors="pt")
            out = self.model.generate(**inputs)
            description = self.processor.decode(out[0], skip_special_tokens=True)
            
            logger.info(f"图像描述: {description}")
            return f"图像分析结果: {description}"
        except Exception as e:
            return f"错误: {str(e)}"

class OCRTool:
    """OCR工具，提取图像中的文字"""
    
    name = "ocr"
    description = "提取图像中的文字"
    
    async def run(self, image_path: str, lang: str = "chi_sim+eng") -> str:
        """提取图像中的文字
        
        Args:
            image_path: 图像文件路径
            lang: OCR语言，默认为中文+英文
            
        Returns:
            提取的文字
        """
        try:
            if not os.path.exists(image_path):
                return "错误: 图像文件不存在"
            
            logger.info(f"执行OCR: {image_path}")
            
            # 使用pytesseract进行OCR
            text = pytesseract.image_to_string(Image.open(image_path), lang=lang)
            
            if not text.strip():
                return "未检测到文字"
            
            logger.info(f"OCR结果: {text[:100]}...")
            return f"OCR提取结果:\n{text}"
        except Exception as e:
            return f"错误: {str(e)}"

class FaceRecognitionTool:
    """人脸识别工具，识别和分析人脸"""
    
    name = "face_recognition"
    description = "识别和分析图像中的人脸"
    
    def __init__(self):
        try:
            self.mtcnn = MTCNN(keep_all=True)
            self.resnet = InceptionResnetV1(pretrained='vggface2').eval()
        except Exception as e:
            logger.warning(f"初始化人脸识别模型失败: {e}")
            self.mtcnn = None
            self.resnet = None
    
    async def run(self, image_path: str) -> str:
        """识别和分析人脸
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            人脸分析结果
        """
        try:
            if self.mtcnn is None:
                return "错误: 未初始化人脸识别模型"
            
            if not os.path.exists(image_path):
                return "错误: 图像文件不存在"
            
            logger.info(f"进行人脸识别: {image_path}")
            
            # 加载图像
            image = Image.open(image_path)
            
            # 检测人脸
            boxes, _ = self.mtcnn.detect(image)
            
            if boxes is None:
                return "未检测到人脸"
            
            faces = self.mtcnn(image)
            if faces is not None:
                embeddings = self.resnet(faces)
            
            result = f"检测到 {len(boxes)} 个人脸\n"
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box
                result += f"人脸 {i+1}: 位置 ({int(x1)}, {int(y1)}) - ({int(x2)}, {int(y2)})\n"
            
            logger.info(f"人脸识别结果: 检测到 {len(boxes)} 个人脸")
            return result
        except Exception as e:
            return f"错误: {str(e)}"

class ObjectDetectionTool:
    """物体检测工具，识别图像中的物体"""
    
    name = "object_detection"
    description = "识别图像中的物体"
    
    def __init__(self):
        # 使用YOLOv3预训练模型
        self.net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
        self.classes = []
        with open("coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
    
    async def run(self, image_path: str, confidence_threshold: float = 0.5) -> str:
        """识别图像中的物体
        
        Args:
            image_path: 图像文件路径
            confidence_threshold: 置信度阈值
            
        Returns:
            物体检测结果
        """
        try:
            if not os.path.exists(image_path):
                return "错误: 图像文件不存在"
            
            logger.info(f"进行物体检测: {image_path}")
            
            # 加载图像
            img = cv2.imread(image_path)
            height, width, channels = img.shape
            
            # 预处理图像
            blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            self.net.setInput(blob)
            outs = self.net.forward(self.output_layers)
            
            # 处理检测结果
            class_ids = []
            confidences = []
            boxes = []
            
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    if confidence > confidence_threshold:
                        # 计算边界框
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            # 非最大抑制
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, 0.4)
            
            result = "物体检测结果:\n"
            for i in range(len(boxes)):
                if i in indexes:
                    x, y, w, h = boxes[i]
                    label = str(self.classes[class_ids[i]])
                    confidence = confidences[i]
                    result += f"{label}: 置信度 {confidence:.2f}, 位置 ({x}, {y}, {w}, {h})\n"
            
            if not result.strip():
                return "未检测到物体"
            
            logger.info(f"物体检测完成，检测到 {len(indexes)} 个物体")
            return result
        except Exception as e:
            return f"错误: {str(e)}"

class ImageGenerationTool:
    """图像生成工具，根据描述生成图像"""
    
    name = "image_generation"
    description = "根据文本描述生成图像"
    
    def __init__(self):
        try:
            self.pipeline = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4")
            if torch.cuda.is_available():
                self.pipeline.to("cuda")
        except Exception as e:
            logger.warning(f"初始化图像生成模型失败: {e}")
            self.pipeline = None
    
    async def run(self, prompt: str, num_images: int = 1, size: str = "512x512") -> str:
        """根据描述生成图像
        
        Args:
            prompt: 图像描述
            num_images: 生成图像数量
            size: 图像尺寸，如 "512x512"
            
        Returns:
            生成结果
        """
        try:
            if self.pipeline is None:
                return "错误: 未初始化图像生成模型"
            
            logger.info(f"生成图像，提示词: {prompt}")
            
            # 解析尺寸
            width, height = map(int, size.split("x"))
            
            # 生成图像
            images = self.pipeline([prompt] * num_images, width=width, height=height).images
            
            # 保存图像
            output_paths = []
            for i, image in enumerate(images):
                output_path = f"generated_image_{i+1}.png"
                image.save(output_path)
                output_paths.append(output_path)
            
            result = f"成功生成 {num_images} 张图像:\n"
            for path in output_paths:
                result += f"- {path}\n"
            
            logger.info(f"图像生成完成，保存到: {output_paths}")
            return result
        except Exception as e:
            return f"错误: {str(e)}"

# 注册工具
def register_image_tools(tool_registry):
    """注册图像处理相关工具"""
    tool_registry.register(ImageAnalysisTool())
    tool_registry.register(OCRTool())
    tool_registry.register(FaceRecognitionTool())
    tool_registry.register(ObjectDetectionTool())
    tool_registry.register(ImageGenerationTool())
