import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os


class YoloLabelViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 라벨 확인 프로그램")

        # 이미지와 캔버스 초기화
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        # 폴더 열기 버튼
        self.open_folder_button = tk.Button(root, text="폴더 열기", command=self.open_folder)
        self.open_folder_button.pack()

        # 다음 이미지로 이동 버튼
        self.next_button = tk.Button(root, text="다음 이미지", command=self.next_image, state=tk.DISABLED)
        self.next_button.pack()

        self.image_files = []
        self.label_folder = ""
        self.current_index = -1

    def open_folder(self):
        # 폴더 선택 대화상자 열기
        folder_path = filedialog.askdirectory(title="폴더 선택")

        if folder_path:
            image_folder = os.path.join(folder_path, "images")
            self.label_folder = os.path.join(folder_path, "labels")

            if os.path.exists(image_folder) and os.path.exists(self.label_folder):
                # 이미지 파일 목록 로드
                self.image_files = [f for f in os.listdir(image_folder) if f.endswith((".jpg", ".jpeg", ".png"))]
                self.image_folder = image_folder
                self.current_index = -1

                if self.image_files:
                    self.next_button.config(state=tk.NORMAL)
                    self.next_image()
                else:
                    messagebox.showwarning("경고", "이미지 파일이 존재하지 않습니다.")
            else:
                messagebox.showwarning("경고", "images 또는 labels 폴더가 존재하지 않습니다.")

    def next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            image_path = os.path.join(self.image_folder, self.image_files[self.current_index])
            self.load_image(image_path)
        else:
            messagebox.showinfo("정보", "더 이상 이미지가 없습니다.")
            self.next_button.config(state=tk.DISABLED)

    def load_image(self, image_path):
        # 이미지 로드
        self.image = Image.open(image_path)
        self.image.thumbnail((800, 600))
        self.photo = ImageTk.PhotoImage(self.image)

        # 이미지 표시
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # 라벨 파일 열기
        self.open_labels(image_path)

    def open_labels(self, image_path):
        # YOLO 라벨 텍스트 파일 경로 추출
        label_filename = os.path.splitext(os.path.basename(image_path))[0] + ".txt"
        label_path = os.path.join(self.label_folder, label_filename)

        if os.path.exists(label_path):
            with open(label_path, "r") as file:
                labels = file.readlines()

            draw = ImageDraw.Draw(self.image)
            width, height = self.image.size

            # 라벨 좌표를 이미지 위에 그리기
            for label in labels:
                data = label.strip().split()
                class_id = data[0]
                x_center, y_center, w, h = map(float, data[1:])

                # YOLO 좌표를 이미지 좌표로 변환
                x_center *= width
                y_center *= height
                w *= width
                h *= height

                # 좌상단과 우하단 좌표 계산
                x1 = x_center - w / 2
                y1 = y_center - h / 2
                x2 = x_center + w / 2
                y2 = y_center + h / 2

                # 바운딩 박스 그리기
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

            # 다시 이미지 갱신
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        else:
            messagebox.showwarning("경고", f"라벨 파일이 없습니다: {label_filename}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YoloLabelViewer(root)
    root.mainloop()
