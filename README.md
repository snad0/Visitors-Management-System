
# 🧠 Visitors Management System with Face Detection

![Face Detection](https://github.com/user-attachments/assets/58b72fc4-24f5-4cd1-a82a-531e7020129e)


An AI-powered secure entry management system designed for private societies. It uses facial recognition to automate and streamline visitor authentication, integrating real-time face detection with a web-based admin dashboard.

---

## 🔍 Project Overview

In environments like residential complexes, corporate campuses, and gated communities, traditional visitor management methods are prone to human error and inefficiency. This system solves these issues with:

- Real-time facial recognition using **OpenCV** and **TensorFlow**
- A web-based interface for **admin approval and monitoring**
- A **PostgreSQL database** to manage entries, residents, and visitors
- **Flask framework** for backend integration

---

## 🎯 Features

- 👁️ Real-time face detection and verification
- 🔐 Manual override and approval for unknown faces
- 📊 Logs entry/exit with timestamps
- 📸 Stores image data of residents and visitors
- 📈 Dashboard to view activity reports and stats
- 💾 Secure data storage with role-based access control

---

## 🧰 Tech Stack

| Component         | Technology                    |
|------------------|-------------------------------|
| Frontend         | HTML5, CSS3, JavaScript (ES6) |
| Backend          | Flask (Python)                |
| Face Recognition | OpenCV, TensorFlow, Keras     |
| Database         | PostgreSQL                    |
| Version Control  | Git, GitHub                   |
| Deployment       | Local server / Cloud Ready    |

---

## 🖼️ Screenshots

> Replace these links with actual images/screenshots from your repo

### 👤 Face Detection in Action

![Face Recognition Demo](https://github.com/user-attachments/assets/def60cf0-1d58-4948-9086-b12da6619931)


### 🧑‍💼 Admin Dashboard

![Admin Dashboard](https://github.com/user-attachments/assets/2fdede47-6a29-468d-b189-0a1149832a39)

### 📝 Visitor Entry Form

![Visitor Entry](https://github.com/user-attachments/assets/c3d725fc-fdd6-4eba-ac3e-b4da1bcc447e)


---

## 📦 Installation


# 1. Clone the repo
git clone https://github.com/yourusername/face-detection-entry-system.git
cd face-detection-entry-system

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask server
python app.py
Make sure PostgreSQL is running.

Update your config.py or .env with your database credentials.

## 🗃️ Database Schema
🧍 Residents Table
resident_id, name, address, block_no, resident_type, image

🧑 Visitors Table
visitor_id, name, phone, image

📋 Entries Table
date, name, entry_time, exit_time, re_entry, status

##🚨 Security Measures
HTTPS for secure transmission

Encrypted image storage

Admin login with RBAC

Input validation & SQL injection protection

Session timeout & secure cookies

## 🚀 Future Enhancements
📱 Mobile app for admin/visitor

📊 Predictive analytics and visitor trend reports

🌐 Cloud deployment and scalability with Docker/Kubernetes

🛂 Integration with RFID/NFC or IoT-based doors

👀 Emotion detection and visitor profiling

## 📚 References
OpenCV Documentation

PostgreSQL Docs

Flask Docs

"Hands-On ML" by Aurélien Géron

Viola-Jones Paper on Face Detection

