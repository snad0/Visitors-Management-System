import logging

from flask import Flask, render_template, Response, jsonify, request
import cv2
import face_recognition
import numpy as np
import psycopg2
from datetime import datetime, timedelta

from flask_socketio import SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Database connection function
def get_db_connection():
    return psycopg2.connect(database="AiSystemDB", user="postgres", password="qwerty123", host="localhost", port="5432")
def initialize_database():
    try:
        # Use the existing get_db_connection function to connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL to create `residents_detail` table
        create_residents_detail_table = """
        CREATE TABLE IF NOT EXISTS residents_detail (
            resident_id Varchar(20) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(255) NOT NULL,
            block_no VARCHAR(10) NOT NULL,
            resident_type VARCHAR(10) NOT NULL,
            image BYTEA NOT NULL
        );
        """

        # SQL to create `entries` table
        create_entries_table = """
        CREATE TABLE IF NOT EXISTS entries (
            date DATE NOT NULL,
            name VARCHAR(100) NOT NULL,
            entry_time TIME,
            exit_time TIME,
            re_entry BOOLEAN DEFAULT FALSE,
            re_entry_time TIME,
            status VARCHAR(10) NOT NULL,
            visit_id Varchar(20),
            is_visitor BOOLEAN DEFAULT FALSE,
            visiting_address VARCHAR(255) DEFAULT 'NA',
            purpose_of_visit VARCHAR(255) DEFAULT 'NA'
        );
        """
        create_table_visitors="""
        CREATE TABLE IF NOT EXISTS visitors (
            visitor_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            phone BIGINT,
            image BYTEA NOT NULL
        );
        """

        # Execute the SQL statements
        cursor.execute(create_residents_detail_table)
        cursor.execute(create_entries_table)
        cursor.execute(create_table_visitors)

        # Commit changes
        conn.commit()
        print("Database tables initialized successfully!")

    except Exception as e:
        print(f"Error initializing database tables: {e}")

# Configure logging to write to a file
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Load resident images and encodings from PostgreSQL
def load_resident_encodings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT resident_id, name, image FROM residents_detail")
    rows = cursor.fetchall()
    conn.close()

    images = []
    resident_ids = []

    for row in rows:
        resident_id, name, image_data = row
        resident_ids.append((resident_id, name))
        
        # Convert binary data back to an image
        img_array = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        images.append(img)

    # Encode the images
    encode_list = []
    for img in images:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_rgb)
        if encodings:
            encode_list.append(encodings[0])

    return encode_list, resident_ids

# Initialize encodings and class names
encodeListKnown, ResidentData = load_resident_encodings()
print("Encoding Complete")
logger.info("Encoding Complete")

# Function to mark attendance in the database
def mark_attendance(resident_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    date_today = now.date()
    current_time = now.strftime('%H:%M:%S')

    # Fetch the name associated with the resident_id
    cursor.execute("SELECT name FROM residents_detail WHERE resident_id = %s", (resident_id,))
    resident = cursor.fetchone()

    if not resident:
        print(f"No resident found for ID {resident_id}.")
        logger.error(f"No resident found for ID {resident_id}.")
        conn.close()
        return

    name = resident[0]  # Extract the name

    # Check if an entry exists for the resident today
    cursor.execute("SELECT * FROM entries WHERE visit_id = %s AND date = %s", (resident_id, date_today))
    entry = cursor.fetchone()

    if entry:
        entry_time, exit_time, re_entry, re_entry_time, status = entry[2], entry[3], entry[4], entry[5], entry[6]

        if status == "IN":
            check_time = re_entry_time if re_entry_time else entry_time
            time_diff = now - datetime.combine(date_today, check_time)
            if time_diff >= timedelta(minutes=10):
                cursor.execute(
                    "UPDATE entries SET exit_time = %s, status = 'OUT' WHERE visit_id = %s AND date = %s",
                    (current_time, resident_id, date_today)
                )
                print(f"Updated Exit_Time for {resident_id} ({name}) to {current_time} and status to OUT.")
                logger.info(f"Updated Exit_Time for {resident_id} ({name}) to {current_time} and status to OUT.")
            else:
                remaining_minutes = 10 - (time_diff.seconds // 60)
                print(f"Cannot update Exit_Time for {resident_id} ({name}). {remaining_minutes} minutes remaining.")
                logger.info(f"Cannot update Exit_Time for {resident_id} ({name}). {remaining_minutes} minutes remaining.")
        
        elif status == "OUT":
            if exit_time and (now - datetime.combine(date_today, exit_time)) >= timedelta(minutes=10):
                cursor.execute(
                    "UPDATE entries SET re_entry = TRUE, re_entry_time = %s, status = 'IN' WHERE visit_id = %s AND date = %s",
                    (current_time, resident_id, date_today)
                )
                print(f"Marked {resident_id} ({name}) as IN again (Re-Entry) with updated Re_Entry_Time to {current_time}.")
                logger.info(f"Marked {resident_id} ({name}) as IN again (Re-Entry) with updated Re_Entry_Time to {current_time}.")
            else:
                remaining_minutes = 10 - ((now - datetime.combine(date_today, exit_time)).seconds // 60) if exit_time else 10
                print(f"Cannot mark Re-Entry for {resident_id} ({name}). {remaining_minutes} minutes remaining.")
                logger.info(f"Cannot mark Re-Entry for {resident_id} ({name}). {remaining_minutes} minutes remaining.")
    else:
        # Insert new entry with resident_id and name if no record exists for today
        cursor.execute(
            """
            INSERT INTO entries (date, name, entry_time, exit_time, re_entry, re_entry_time, status, visit_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (date_today, name, current_time, None, False, None, "IN", resident_id)
        )
        print(f"Added new entry for {resident_id} ({name}).")
        logger.info(f"Added new entry for {resident_id} ({name}).")

    conn.commit()
    conn.close()


# Camera feed processing
def generate_frames():
    cap = cv2.VideoCapture(0)
    frame_skip = 10
    frame_count = 0
    recognition_threshold = 0.6
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        if frame_count % frame_skip == 0:
            imgS = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
            face_Current_Frame = face_recognition.face_locations(imgS)
            encoding_Current_Frame = face_recognition.face_encodings(imgS, face_Current_Frame)
            
            for encode_face, face_loc in zip(encoding_Current_Frame, face_Current_Frame):
                matches = face_recognition.compare_faces(encodeListKnown, encode_face)
                face_Distance = face_recognition.face_distance(encodeListKnown, encode_face)
                match_index = np.argmin(face_Distance)
                
                if matches[match_index] and face_Distance[match_index] <recognition_threshold:
                    resident_id, name = ResidentData[match_index]
                    mark_attendance(resident_id)
                    
                    y1, x2, y2, x1 = face_loc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 255), 2)
                else:
                    logger.warning("Unrecognized face detected!")
                    socketio.emit('unrecognized_alert', {'message': 'Unrecognized face detected!'})

                    y1, x2, y2, x1 = face_loc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (0, 0, 255), cv2.FILLED)
                    cv2.putText(frame, "Unknown", (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 255), 2)

        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries ORDER BY date DESC, entry_time DESC")
    attendance_data = cursor.fetchall()
    conn.close()
    return render_template('index.html', attendance_data=attendance_data)

@app.route('/add_resident', methods=['POST'])
def add_resident():
    try:
        name = request.form.get('name')
        address = request.form.get('address')
        block_no = request.form.get('block_no')
        resident_type = request.form.get('resident_type')
        image_file = request.files.get('image')

        if not all([name, address, block_no, resident_type, image_file]):
            return jsonify({'message': 'All fields are required'}), 400

        image_data = image_file.read()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO residents_detail (name, address, block_no, resident_type, image)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, address, block_no, resident_type, psycopg2.Binary(image_data)))
        conn.commit()
        conn.close()

        return jsonify({'message': f'Resident {name} added successfully'})
    except Exception as e:
        print(f"Error occurred: {e}")
        logger.info(f"Error occurred: {e}")
        return jsonify({'message': 'An error occurred while adding the resident'}), 500

@app.route('/fetch_attendance')
def fetch_attendance():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries ORDER BY date DESC, entry_time DESC")
    rows = cursor.fetchall()
    conn.close()

    attendance_data = [
        {
            'date': row[0].strftime('%Y-%m-%d'),
            'name': row[1],
            'entry_time': row[2].strftime('%H:%M:%S') if row[2] else None,
            'exit_time': row[3].strftime('%H:%M:%S') if row[3] else None,
            're_entry': row[4],
            're_entry_time': row[5].strftime('%H:%M:%S') if row[5] else None,
            'status': row[6],
            'visit_id': row[7]
        } for row in rows
    ]
    return jsonify(attendance_data)
    # print(jsonify(attendance_data))
@app.route('/fetch_logs')

def fetch_logs():
    try:
        with open('app.log', 'r') as log_file:
            # Read the last 20 lines (or adjust as needed)
            logs = log_file.readlines()[-20:]
        return jsonify(logs)
    except Exception as e:
        logger.info(f"Error fetching logs: {e}")
        return jsonify({'error': 'Failed to fetch logs'}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)



