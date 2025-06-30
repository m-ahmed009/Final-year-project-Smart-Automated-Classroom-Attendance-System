# Final-year-project-SACAS-Smart-Automated-Classroom-Attendance-System

🚀 Smart Automated Classroom Attendance System – Our Final Year Project Completed! 🧠📸
Proudly developed by students of Iqra University, Airport Campus under the supervision of Sir Muhammad Affan Alim and instruction of Sir Waqas.

After months of hard work, research, and countless sleepless nights, we are thrilled to announce the successful completion of our FYP:
📍 "Smart Automated Classroom Attendance System" – powered by Deep Learning and Computer Vision.

💡 Project Overview:

We designed a fully automated attendance system that uses AI-based face recognition to mark student attendance.
Key Components of the System:

✅ Three Dedicated Dashboards:

Admin: Registers students and captures 15 facial images per student.

Faculty: Takes attendance using live CCTV stream.

Student: Views their attendance per course through their personalized dashboard.


✅ Image Processing & Face Detection:

We used YOLOv8 (yolov8n-face.pt) to detect faces before training.

Images were split into train (9), validation (3), and test (3) sets after face cropping using cv2.


✅ Model Training:

Model per course was trained using ResNet152V2 (TensorFlow + Keras), fine-tuned on top of ImageNet weights.

We applied data augmentation for better generalization.

Final model was saved for real-time recognition.


✅ Real-Time Camera Attendance:

Faculty clicks “Take Camera Attendance” → Live CCTV stream opens → Face detection via YOLOv8 → Cropping via cv2 → Recognized using the trained ResNet model → Attendance automatically marked.


✅ Camera Configuration Module:

Faculty can configure camera IP, port, etc. for smooth classroom integration.


✅ LMS-Integrated Architecture:

 Complete LMS system design based on university ERD to maintain attendance consistency.

Admin creates attendance session, which generates a faculty-side roaster.

Manual attendance option is also available as fallback.


✅ Student Dashboard:

Students can view their attendance course-wise, ensuring transparency and engagement.


🔧 Technologies Used:

YOLOv8: (You Only Look Once) Real-time object detection model – used for facial detection.

ResNet152V2: Deep convolutional neural network for image classification – used for recognizing student faces.

TensorFlow & Keras: Deep learning frameworks used to build and train our face recognition models.

OpenCV (cv2): Used for image processing and face cropping.

All of these belong to the fields of Machine Learning (ML) and Deep Learning (DL), which are at the heart of modern AI solutions.


🎓 This project was not just an academic milestone — it was an end-to-end AI-powered LMS-integrated solution that reflects what the future of education can look like.

🙌 Huge thanks to our amazing mentors and teammates who made this vision a reality.



