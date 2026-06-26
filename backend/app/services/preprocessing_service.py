from pathlib import Path
import cv2, numpy as np

class PreprocessingService:
    def load_image(self, path):
        img = cv2.imread(str(path))
        if img is None: raise ValueError(f"Cannot read image {path}")
        return img
    def grayscale(self,img): return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
    def denoise(self,img): return cv2.fastNlMeansDenoising(self.grayscale(img), None, 10, 7, 21)
    def enhance_contrast(self,img):
        return cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(self.grayscale(img))
    def threshold(self,img): return cv2.threshold(self.grayscale(img),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    def blur_score(self,img): return float(cv2.Laplacian(self.grayscale(img), cv2.CV_64F).var())
    def quality_score(self,img):
        return round(min(1.0, (self.blur_score(img)/500)*0.55 + (float(np.std(self.grayscale(img)))/80)*0.45),3)
    def preprocess_to_file(self, input_path, output_path):
        img = self.load_image(input_path)
        out = self.denoise(self.enhance_contrast(img))
        Path(output_path).parent.mkdir(parents=True,exist_ok=True)
        cv2.imwrite(str(output_path), out)
        return {"output_path":str(output_path),"blur_score":self.blur_score(img),"quality_score":self.quality_score(img)}
