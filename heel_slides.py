import cv2
import mediapipe as mp
import numpy as np
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0)

# Function to calculate angle between three points
def calculate_angle(v1, v0, v2):
    v1 = np.array(v1)
    v0 = np.array(v0)
    v2 = np.array(v2)
    
    angle_1 = (np.arctan2(v2[1]-v0[1], v2[0]-v0[0]) - np.arctan2(v1[1]-v0[1], v1[0]-v0[0]))
    angle_2 = np.arccos(np.dot(v0-v1, v2-v0) / (np.linalg.norm(v0-v1) * np.linalg.norm(v2-v0)))
    angle = np.abs(angle_1 * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle



def arm_extensions(reps=5, total_sets=1, threshold_angle=120):
    sets = 0
    status = None
    count = 0
    side = "left"
    start_time = time.time()
    elapsed_time = 0  # Initialize elapsed_time outside the try block
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            results = pose.process(image)
            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            try:
                # Extract landmarks for right shoulder, elbow, and wrist
                if side == "left":
                    landmarks = results.pose_landmarks.landmark
                    shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                elif side=='right':
                    landmarks = results.pose_landmarks.landmark
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                
                # Calculate angle between the shoulder, elbow, and wrist
                angle = calculate_angle(shoulder, elbow, wrist)
                shoulder_angle = calculate_angle(hip, shoulder, elbow)
                
                # Draw semi-circle at elbow
                if side == "left":
                    cv2.ellipse(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), (80, 80), 0, 0, -(int(angle)), (255, 0, 0), 2)
                else:
                    cv2.ellipse(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), (80, 80), 0, 0, -(int(angle)), (255, 0, 0), 2)
                
                # Draw circle spot on shoulder and elbow
                
                # Check if arms are raised above threshold angle (e.g., 120 degrees)
                if shoulder_angle > 100:
                    cv2.putText(image, f"Please lower your elbow!", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.circle(image, tuple(np.multiply(shoulder, [640, 480]).astype(int)), 10, (0, 0, 255), -1)  # Red spot on shoulder
                    
                elif shoulder_angle < 70:
                    cv2.putText(image, f"Please raise your elbow!", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.circle(image, tuple(np.multiply(shoulder, [640, 480]).astype(int)), 10, (0, 0, 255), -1)  # Red spot on shoulder
                else:
                    cv2.circle(image, tuple(np.multiply(shoulder, [640, 480]).astype(int)), 10, (0, 255, 0), -1)  # Green spot on shoulder
                
                # Calculate proportion of current angle to threshold angle
                proportion = max(0, min(1, angle / threshold_angle))
                # Calculate radius of filled circle based on proportion
                filled_circle_radius = int(proportion * threshold_angle / 4)

                # Draw hollow circle at elbow with maximum radius
                cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), int(threshold_angle / 4), (255, 255, 255), 2)

                # Draw filled circle at elbow with radius proportional to the angle
                if int(threshold_angle / 4)-5 < filled_circle_radius < int(threshold_angle / 4)+5:
                    cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), filled_circle_radius, (0, 255, 0), -1)
                elif filled_circle_radius > int(threshold_angle / 4):
                    cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), filled_circle_radius, (0, 0, 255), -1)
                else:
                    cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), filled_circle_radius, (255, 0, 0), -1)
                

                if angle >= threshold_angle and angle <threshold_angle+10:
                    if status == "Lower":
                        count += 1
                    status = 'Raise'
                    # Reset filled circle when threshold angle is met
                    filled_circle_radius = 0
                elif angle > threshold_angle+10:
                    cv2.putText(image, "Do not over extend!", (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), circle_radius, (0, 0, 255), -1)
                elif angle < 50:
                    status = 'Lower'
                
                if status == 'Raise':
                    cv2.putText(image, "Contract!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                elif status == 'Lower':
                    cv2.putText(image, "Extend!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            except:
                pass
            circle_radius = int(angle/4)
            #cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), circle_radius, (255, 0, 0), -1)  # Red spot on elbow
            
            cv2.putText(image,f"Count: {count} / {reps}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)   
            cv2.putText(image,f"Set: {sets} / {total_sets}", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            #Draw pose landmarks
            # if results.pose_landmarks:
            #     mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            #                               mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
            #                               mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
            
            # Display frame
            if count == reps:
                sets+=0.5
                if sets == total_sets:
                    cv2.putText(image, "Workout Complete!", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    elapsed_time = time.time() - start_time
                    break
                else:
                    cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    if side == "left":
                        side = "right"
                    elif side == "right":
                        side = "left"
                    status = None
                    count = 0
            cv2.imshow('Mediapipe Feed', image)
            
            # Exit loop if 'q' is pressed
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        
        # Release video capture and close all windows
        cap.release()
        cv2.destroyAllWindows()
        return 'completed', sets, reps, elapsed_time  # Return elapsed_time outside the loop
    
    
def heel_slides(reps=5,total_sets=1,threshold_angle=100):
    sets = 0
    status = None
    count = 0
    side = "left"
    over_extension = False
    mistakes = 0
    start_time = time.time()
    start = False
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            results = pose.process(image)
            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            try:
                # Extract landmarks for right shoulder, elbow, and wrist
                if side == "left":
                    landmarks = results.pose_landmarks.landmark
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    heel = [landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].y]
                elif side=='right':
                    landmarks = results.pose_landmarks.landmark
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    heel = [landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y]
                
                # Calculate angle between the shoulder, elbow, and wrist
                #angle = calculate_angle(shoulder, elbow, wrist)
                knee_angle = calculate_angle(hip, knee, heel)
                if start == False:
                    cv2.putText(image, "Stretch Legs to Start!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    if knee_angle < 100:
                        start = True
                    
                elif start:
                    # Draw semi-circle at elbow
                    if side == "left":
                        #cv2.ellipse(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), (80, 80), 0, 0, -(int(angle)), (255, 0, 0), 2)
                        cv2.ellipse(image, tuple(np.multiply(knee, [640, 480]).astype(int)), (80, 80), 0, 0, (int(knee_angle)), (255, 0, 0), 2)
                    else:
                        cv2.ellipse(image, tuple(np.multiply(knee, [640, 480]).astype(int)), (80, 80), 0, 0, (int(knee_angle)), (255, 0, 0), 2)
                    
                    # Calculate proportion of current angle to threshold angle
                    proportion = max(0, min(1, knee_angle / 180))
                    # Calculate radius of filled circle based on proportion
                    filled_circle_radius = int(proportion * threshold_angle / 4)

                    # Draw hollow circle at elbow with maximum radius
                    cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), int(threshold_angle / 4), (255, 255, 255), 2)

                    # Draw filled circle at elbow with radius proportional to the angle
                    if int(threshold_angle / 4)-5 < filled_circle_radius < int(threshold_angle / 4)+5:
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (0, 255, 0), -1)
                    elif filled_circle_radius > int(threshold_angle / 4):
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (0, 0, 255), -1)
                    else:
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (255, 0, 0), -1)
                    

                    if knee_angle > 150:
                        if status == "Lower":
                            count += 1
                        status = 'Raise'
                        filled_circle_radius = 0
                    elif knee_angle <= threshold_angle:
                        status='Lower'
                        
                        
                    if knee_angle <= threshold_angle-10:
                        over_extension = True
                        cv2.putText(image, "Do not over contract!", (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        if over_extension:
                            mistakes+=1
                            over_extension = False
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), circle_radius, (0, 0, 255), -1)

                    
                    if status == 'Raise':
                        cv2.putText(image, "Contract!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    elif status == 'Lower':
                        cv2.putText(image, "Extend!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                circle_radius = int(knee_angle/4)
                #cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), circle_radius, (255, 0, 0), -1)  # Red spot on elbow
            
                cv2.putText(image,f"Count: {count} / {reps}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)   
                cv2.putText(image,f"Set: {sets} / {total_sets}", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                #Draw pose landmarks
                # if results.pose_landmarks:
                #     mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                #                               mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                #                               mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
                
                # Display frame
                if count == reps:
                    sets+=0.5
                    if sets == total_sets:
                        cv2.putText(image, "Workout Complete!", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        elapsed_time = time.time() - start_time
                        cv2.waitKey(5000) 
                        break
                    else:
                        cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        if side == "left":
                            side = "right"
                        elif side == "right":
                            side = "left"
                        cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        cv2.waitKey(5000) 
                        status = None
                        count = 0
            except:
                pass
            cv2.imshow('Heel Slides', image)
            
            # Exit loop if 'q' is pressed
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        
        # Release video capture and close all windows
        cap.release()
        cv2.destroyAllWindows()
        return 'completed', sets, reps, elapsed_time,mistakes
    

def knee_extensions(reps=5, total_sets=1, threshold_angle=140):
    sets = 0
    status = None
    count = 0
    side = "left"
    over_extension = False
    mistakes = 0
    start_time = time.time()
    start = True
    circle_radius = 0  # Initialize circle_radius with a default value
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            results = pose.process(image)
            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            try:
                # Extract landmarks for right shoulder, elbow, and wrist
                if side == "left":
                    landmarks = results.pose_landmarks.landmark
                    hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    heel = [landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].y]
                elif side == 'right':
                    landmarks = results.pose_landmarks.landmark
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    heel = [landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y]
                
                # Calculate angle between the shoulder, elbow, and wrist
                knee_angle = calculate_angle(hip, knee, heel)
                if start == True:
                    # Draw semi-circle at elbow
                    cv2.ellipse(image, tuple(np.multiply(knee, [640, 480]).astype(int)), (80, 80), 0, 0, (int(knee_angle)), (255, 0, 0), 2)
                    
                    # Calculate proportion of current angle to threshold angle
                    proportion = max(0, min(1, knee_angle / threshold_angle))
                    # Calculate radius of filled circle based on proportion
                    filled_circle_radius = int(proportion * threshold_angle / 4)

                    # Draw hollow circle at elbow with maximum radius
                    cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), int(threshold_angle / 4), (255, 255, 255), 2)

                    # Draw filled circle at elbow with radius proportional to the angle
                    if int(threshold_angle / 4) - 5 < filled_circle_radius < int(threshold_angle / 4) + 5:
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (0, 255, 0), -1)
                    elif filled_circle_radius > int(threshold_angle / 4):
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (0, 0, 255), -1)
                    else:
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (255, 0, 0), -1)

                    if knee_angle < 80:
                        if status == "Lower":
                            count += 1
                        status = 'Raise'
                        filled_circle_radius = 0
                    elif knee_angle >= threshold_angle and knee_angle < threshold_angle + 10:
                        status = 'Lower'
                        
                    if knee_angle >= threshold_angle + 20:
                        over_extension = True
                        cv2.putText(image, "Do not over contract!", (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        if over_extension:
                            mistakes += 1
                            over_extension = False
                        cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), circle_radius, (0, 0, 255), -1)

                    if status == 'Raise':
                        cv2.putText(image, "Extend!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    elif status == 'Lower':
                        cv2.putText(image, "Contract!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                circle_radius = int(knee_angle / 4)
                cv2.putText(image, f"Count: {count} / {reps}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)   
                cv2.putText(image, f"Set: {sets} / {total_sets}", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                
                # Display frame
                if count < 2 and side == 'right':
                    cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    
                if count == reps:
                    sets += 0.5
                    if sets == total_sets:
                        cv2.putText(image, "Workout Complete!", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        elapsed_time = time.time() - start_time
                        break
                    else:
                        cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        if side == "left":
                            side = "right"
                        elif side == "right":
                            side = "left"
                        status = None
                        count = 0
            except:
                pass
            
            cv2.imshow('Knee Extensions', image)
            
            # Exit loop if 'q' is pressed
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        # Release video capture and close all windows
        cap.release()
        cv2.destroyAllWindows()
        return 'completed', sets, reps, elapsed_time, mistakes


# def knee_extensions(reps=5,total_sets=1,threshold_angle=140):
#     sets = 0
#     status = None
#     count = 0
#     side = "left"
#     over_extension = False
#     mistakes = 0
#     start_time = time.time()
#     start = True
#     with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
#         while cap.isOpened():
#             ret, frame = cap.read()
#             frame = cv2.flip(frame, 1)
#             image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             image.flags.writeable = False
            
#             results = pose.process(image)
            
#             image.flags.writeable = True
#             image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
#             try:
#                 # Extract landmarks for right shoulder, elbow, and wrist
#                 if side == "left":
#                     landmarks = results.pose_landmarks.landmark
#                     hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
#                     knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
#                     heel = [landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].y]
#                 elif side=='right':
#                     landmarks = results.pose_landmarks.landmark
#                     hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
#                     knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
#                     heel = [landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y]
                
#                 # Calculate angle between the shoulder, elbow, and wrist
#                 #angle = calculate_angle(shoulder, elbow, wrist)
#                 knee_angle = calculate_angle(hip, knee, heel)
#                 if start == True:
#                     # Draw semi-circle at elbow
#                     if side == "left":
#                         #cv2.ellipse(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), (80, 80), 0, 0, -(int(angle)), (255, 0, 0), 2)
#                         cv2.ellipse(image, tuple(np.multiply(knee, [640, 480]).astype(int)), (80, 80), 0, 0, (int(knee_angle)), (255, 0, 0), 2)
#                     else:
#                         cv2.ellipse(image, tuple(np.multiply(knee, [640, 480]).astype(int)), (80, 80), 0, 0, (int(knee_angle)), (255, 0, 0), 2)
                    
#                     # Calculate proportion of current angle to threshold angle
#                     proportion = max(0, min(1, knee_angle / (threshold_angle)))
#                     # Calculate radius of filled circle based on proportion
#                     filled_circle_radius = int(proportion * threshold_angle/4 )

#                     # Draw hollow circle at elbow with maximum radius
#                     cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), int(threshold_angle/4), (255, 255, 255), 2)

#                     # Draw filled circle at elbow with radius proportional to the angle
#                     if int(threshold_angle/4)-5 < filled_circle_radius < int(threshold_angle/4)+5:
#                         cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (0, 255, 0), -1)
#                     elif filled_circle_radius > int(threshold_angle / 4):
#                         cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (0, 0, 255), -1)
#                     else:
#                         cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), filled_circle_radius, (255, 0, 0), -1)
                    

#                     if knee_angle < 80:
#                         if status == "Lower":
#                             count += 1
#                         status = 'Raise'
#                         filled_circle_radius = 0
                        
#                     elif knee_angle >= threshold_angle and knee_angle <threshold_angle+10:
#                         status='Lower'
                        
#                     if knee_angle >= threshold_angle+20:
#                         over_extension = True
#                         cv2.putText(image, "Do not over contract!", (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
#                         if over_extension:
#                             mistakes+=1
#                             over_extension = False
#                         cv2.circle(image, tuple(np.multiply(knee, [640, 480]).astype(int)), circle_radius, (0, 0, 255), -1)

                    
#                     if status == 'Raise':
#                         cv2.putText(image, "Extend!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
#                     elif status == 'Lower':
#                         cv2.putText(image, "Contract!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

#                 circle_radius = int(knee_angle/4)
#                 #cv2.circle(image, tuple(np.multiply(elbow, [640, 480]).astype(int)), circle_radius, (255, 0, 0), -1)  # Red spot on elbow
                
#                 cv2.putText(image,f"Count: {count} / {reps}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)   
#                 cv2.putText(image,f"Set: {sets} / {total_sets}", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
#                 #Draw pose landmarks
#                 # if results.pose_landmarks:
#                 #     mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
#                 #                               mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
#                 #                               mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
                
#                 # Display frame
#                 if count <2 and side=='right':
#                     cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    
#                 if count == reps:
#                     sets+=0.5
#                     if sets == total_sets:
#                         cv2.putText(image, "Workout Complete!", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
#                         elapsed_time = time.time() - start_time
#                         break
#                     else:
#                         cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
#                         if side == "left":
#                             side = "right"
#                         elif side == "right":
#                             side = "left"
#                         status = None
#                         count = 0
#             except:
#                 pass
#             cv2.imshow('Knee Extensions', image)
            
#             # Exit loop if 'q' is pressed
#             if cv2.waitKey(10) & 0xFF == ord('q'):
#                 break

        
#         # Release video capture and close all windows
#         cap.release()
#         cv2.destroyAllWindows()
#         return 'completed', sets, reps, elapsed_time,mistakes
    

def squats(reps=5, total_sets=1, threshold_angle=140):
    sets = 0
    status = None
    count = 0
    side = "left"
    over_extension = False
    mistakes = 0
    start_time = time.time()
    elapsed_time = 0  # Initialize elapsed_time with a default value

    cap = cv2.VideoCapture(0)  # Change to the appropriate camera index if necessary

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break

            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results = pose.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                # Extract landmarks for hips, knees, and heels
                landmarks = results.pose_landmarks.landmark
                left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                              landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                # Get coordinates for right side
                right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                               landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

                # We need torso-leg coordination

                # Get coordinates for left shoulder-left leg
                left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,  # used for break statement
                                 landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]

                # Get coordinates for right shoulder-right leg
                right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,  # used for break statement
                                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                             landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
                              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]

                # Calculate angle
                angle_left = calculate_angle(left_hip, left_knee, left_ankle)
                angle_right = calculate_angle(right_hip, right_knee, right_ankle)
                angle_left_upper = calculate_angle(left_shoulder, left_hip, left_knee)
                angle_right_upper = calculate_angle(right_shoulder, right_hip, right_knee)

                # Squats counter logic
                if (angle_left > 120 and angle_right > 120) and (angle_left_upper > 160 and angle_right_upper > 160):
                    stage = "up"
                    status = 'up'
                elif (angle_left < 90 and angle_right < 90) and (
                        angle_left_upper < 100 and angle_right_upper < 100) and stage == "up":
                    stage = "down"
                    count += 1
                    status = 'down'

                # Calculate angle between hips, knees, and heels
                knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
                # Calculate proportion of current angle to threshold angle
                proportion = max(0, min(1, knee_angle / threshold_angle))
                # Calculate radius of filled circle based on proportion
                filled_circle_radius = int(proportion * threshold_angle / 4)

                # Draw hollow circle at knee with maximum radius
                cv2.circle(image, tuple(np.multiply(left_knee, [640, 480]).astype(int)), int(threshold_angle / 4), (255, 255, 255), 2)

                # Draw filled circle at knee with radius proportional to the angle
                if int(threshold_angle / 4) - 5 < filled_circle_radius < int(threshold_angle / 4) + 5:
                    cv2.circle(image, tuple(np.multiply(left_knee, [640, 480]).astype(int)), filled_circle_radius, (0, 255, 0), -1)
                elif filled_circle_radius > int(threshold_angle / 4):
                    cv2.circle(image, tuple(np.multiply(left_knee, [640, 480]).astype(int)), filled_circle_radius, (0, 0, 255), -1)
                else:
                    cv2.circle(image, tuple(np.multiply(left_knee, [640, 480]).astype(int)), filled_circle_radius, (255, 0, 0), -1)

                if knee_angle >= threshold_angle + 20:
                    over_extension = True
                    cv2.putText(image, "Do not over extend!", (250, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    if over_extension:
                        mistakes += 1
                        over_extension = False
                    cv2.circle(image, tuple(np.multiply(left_knee, [640, 480]).astype(int)), int(knee_angle / 4), (0, 0, 255), -1)

                if status == 'up':
                    cv2.putText(image, "Go down!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                elif status == 'down':
                    cv2.putText(image, "Go up!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                circle_radius = int(knee_angle / 4)

                cv2.putText(image, f"Count: {count}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)   

                if count < 2 and side == 'right':
                    cv2.putText(image, "Set Complete! Time to switch sides!", (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                if count == reps:
                    sets += 1
                    if sets == total_sets:
                        cv2.putText(image, "Workout Complete!", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        elapsed_time = time.time() - start_time
                        break
            except Exception as e:
                print(f"An error occurred: {e}")
                pass

            cv2.imshow('Squats', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        return 'completed', sets, reps, elapsed_time, mistakes


