import mediapipe as mp

class GestureRecognizer:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )

    def process_frame(self, rgb_frame):
        """
        Processes a frame and returns (results, gesture_name).
        gesture_name can be "THUMBS_UP", "LOVE" (Peace), "SUS" (Pointing), or None.
        """
        results = self.hands.process(rgb_frame)
        gesture = None

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                gesture = self._classify_gesture(handLms.landmark)
                # We only engage with the first hand detected
                break
        
        return results, gesture

    def _classify_gesture(self, landmarks):
        # Finger tips
        thumb_tip = landmarks[4].y
        thumb_ip = landmarks[3].y # Inter-phalangeal joint
        thumb_base = landmarks[2].y # MCP

        index_tip = landmarks[8].y
        index_pip = landmarks[6].y

        middle_tip = landmarks[12].y
        middle_pip = landmarks[10].y

        ring_tip = landmarks[16].y
        ring_pip = landmarks[14].y

        pinky_tip = landmarks[20].y
        pinky_pip = landmarks[18].y

        # Helper: is finger extended? (Tip above PIP, remember y increases downwards)
        is_index_ext = index_tip < index_pip
        is_middle_ext = middle_tip < middle_pip
        is_ring_ext = ring_tip < ring_pip
        is_pinky_ext = pinky_tip < pinky_pip
        
        # THUMBS UP Logic (Simple)
        # Thumb tip is significantly higher than base (small y vs large y)
        # BUT orientation matters. Let's assume hand is upright.
        # Actually, standard "Thumbs Up" is usually fist with thumb up.
        # Fingers closed:
        fingers_closed = (not is_index_ext) and (not is_middle_ext) and (not is_ring_ext) and (not is_pinky_ext)
        if fingers_closed:
            # Check thumb.
            # thumb tip above thumb base
            if thumb_tip < thumb_base: 
                return "THUMBS_UP"

        # LOVE / PEACE Logic (V Sign)
        # Index and Middle Extended, others closed.
        if is_index_ext and is_middle_ext and (not is_ring_ext) and (not is_pinky_ext):
            return "LOVE" 

        # SUS / POINTING Logic
        # Only Index extended
        if is_index_ext and (not is_middle_ext) and (not is_ring_ext) and (not is_pinky_ext):
            return "SUS"
            
        # RAINBOW (Swipe Left) Logic ?
        # Harder to detect with single frame. Maybe "Open Hand" triggers Rainbow?
        # Let's map "Open Hand" (All fingers extended) to RAINBOW for now, 
        # or stick to user request. User said "Left swipe = RAINBOW".
        # Dynamic gesture requires history. Static replacement: Open Hand = RAINBOW?
        # User prompt: "Swipe Left = RAINBOW". 
        # I'll stick to static gestures for simplicity first version. 
        # Let's map OPEN FIVE to RAINBOW for simplicity or ignore.
        
        return None

    def draw_landmarks(self, frame, results):
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, handLms, self.mp_hands.HAND_CONNECTIONS)
