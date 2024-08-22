import cv2

class Image_Preprocess:
    def __init__(self):
        self.selected_preprocessing = "Normal"
        self.preprocessing_types = ["Normal", "Increase Brightness", "Image Pyramids", "Color Space Conversion"]

    def change_preprocessing(self, text):
        self.selected_preprocessing = text

    def apply_preprocessing(self, frame):
        if self.selected_preprocessing == "Increase Brightness":
            return self.increase_brightness(frame, beta=50)
        elif self.selected_preprocessing == "Image Pyramids":
            return self.image_pyramids(frame)
        elif self.selected_preprocessing == "Color Space Conversion":
            return self.color_space_converted(frame)
        else:
            return frame

    def increase_brightness(self, image, beta):
        return cv2.convertScaleAbs(image, alpha=1, beta=beta)

    def image_pyramids(self, image):
        return cv2.pyrUp(image)

    def color_space_converted(self, image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2HSV)