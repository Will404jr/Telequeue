import streamlit as st
from chat_bot import process_patient, match_symptoms, call_next_patient, play_audio
from database import update_patient_status
import ast
from typing import Optional, Tuple
import base64


def apply_custom_css(css_path: str = "styles.css"):
    with open(css_path) as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

def landing_page():
    # Path to your local image
    image_path = 'img.jpg'
    
    # Encode the image in base64
    encoded_image = encode_image_to_base64(image_path)
    
    # Create the HTML string with the image embedded in the h1
    html_content = f'''
    <div class="main-header">
        <h1>
            <img src="data:image/png;base64,{encoded_image}" alt="Custom Image" style="width:70px;vertical-align:middle;">
            Welcome to Tele-Queue Management System
        </h1>
    </div>
    '''
    
    # Display the content using Streamlit's markdown allowing HTML
    st.markdown(html_content, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem;">Choose your role to get started</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="role-card" onclick="document.querySelector('#doctor-button').click()">
                <div class="role-icon">👨‍⚕️</div>
                <h2>Doctor</h2>
                <p>Access patient queue and manage consultations</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Login as Doctor", key="doctor-button", type="primary"):
            st.session_state.user_type = "Doctor"
            st.rerun()
            
    with col2:
        st.markdown("""
            <div class="role-card" onclick="document.querySelector('#patient-button').click()">
                <div class="role-icon">🏥</div>
                <h2>Patient</h2>
                <p>Register for consultation and get queue number</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Register as Patient", key="patient-button", type="primary"):
            st.session_state.user_type = "Patient"
            st.rerun()

def doctor_interface():
    st.markdown('<div class="main-header"><h2>👨‍⚕️ Doctor Dashboard</h2></div>', unsafe_allow_html=True)
    
    # Initialize session state
    default_state = {
        "calling_patients": False,
        "current_patient": None,
        "audio_played_for": None
    }
    
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

    def parse_patient_data(patient_data: tuple) -> Tuple[str, str, list, str]:
        try:
            ticket_number, name, symptoms_raw, disease = (
                str(patient_data[7]), patient_data[1], patient_data[2], patient_data[3]
            )
            try:
                symptoms = ast.literal_eval(symptoms_raw) if isinstance(symptoms_raw, str) else symptoms_raw
                symptoms = symptoms if isinstance(symptoms, list) else [str(symptoms)]
            except (ValueError, SyntaxError):
                symptoms = [str(symptoms_raw)]
            return ticket_number, name, symptoms, disease
        except Exception as e:
            st.error(f"Error parsing patient data: {e}")
            return None, None, None, None

    def display_patient_info(patient_data: tuple) -> None:
        if not patient_data:
            st.markdown('<div class="warning-message">No valid patient data available.</div>', unsafe_allow_html=True)
            return
            
        ticket_number, name, symptoms, disease = parse_patient_data(patient_data)
        if not all([ticket_number, name, symptoms, disease]):
            return
            
        # Patient info card
        st.markdown(f"""
            <div class="patient-card">
                <h3>Current Patient</h3>
                <div class="status-indicator status-active"></div>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Ticket:</strong> #{ticket_number}</p>
                <p><strong>Symptoms:</strong> {', '.join(symptoms)}</p>
                <p><strong>Diagnosis:</strong> {disease}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.audio_played_for != ticket_number:
            play_audio(ticket_number)
            st.session_state.audio_played_for = ticket_number
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Mark as Served", key=f"serve_{ticket_number}"):
                try:
                    update_patient_status(ticket_number)
                    st.markdown(f'<div class="success-message">Patient {name} (#{ticket_number}) has been served.</div>', 
                              unsafe_allow_html=True)
                    st.session_state.audio_played_for = None
                    st.session_state.current_patient = call_next_patient()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            if st.button("⏭️ Next Patient", key=f"next_{ticket_number}"):
                st.session_state.current_patient = call_next_patient()
                st.rerun()

    # Main interface logic with styled components
    if not st.session_state.calling_patients:
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("🔊 Start Calling Patients", key="initial_call"):
                next_patient = call_next_patient()
                if next_patient:
                    st.session_state.calling_patients = True
                    st.session_state.current_patient = next_patient
                    st.rerun()
                else:
                    st.markdown('<div class="warning-message">No patients in queue</div>', unsafe_allow_html=True)
    
    if st.session_state.calling_patients and st.session_state.current_patient:
        display_patient_info(st.session_state.current_patient)
    elif st.session_state.calling_patients:
        st.markdown('<div class="warning-message">No patients available. Click "Start Calling Patients" to begin.</div>', 
                   unsafe_allow_html=True)

def patient_interface():
    # Add back button
    if st.button("← Back to Home", key="back_button"):
        st.session_state.user_type = None
        st.rerun()
        
    st.markdown('<div class="main-header"><h2>🏥 Patient Registration</h2></div>', unsafe_allow_html=True)
    
    # Initialize session state for patient registration
    if "patient_data" not in st.session_state:
        st.session_state.patient_data = None
        
    if "registration_complete" not in st.session_state:
        st.session_state.registration_complete = False
        
    # Add a form counter to force input refresh
    if "form_counter" not in st.session_state:
        st.session_state.form_counter = 0
    
    if not st.session_state.registration_complete:
        st.markdown("""
            <div class="patient-card">
                <h3>Enter Your Details</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Use form_counter in the key to force refresh
        name = st.text_input("Full Name", key=f"name_input_{st.session_state.form_counter}")
        symptoms_input = st.text_area("Describe your symptoms (separate with commas)", 
                                    key=f"symptoms_input_{st.session_state.form_counter}")
        
        if st.button("Check Symptoms"):
            if name and symptoms_input:
                input_symptoms = [symptom.strip() for symptom in symptoms_input.split(',')]
                matched_symptoms = match_symptoms(input_symptoms)
                
                if len(matched_symptoms) == len(input_symptoms):
                    st.markdown("""
                        <div class="patient-card">
                            <h3>Confirm Your Symptoms</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    confirmed_symptoms = st.multiselect("Please verify your symptoms:", 
                                                      matched_symptoms, 
                                                      default=matched_symptoms)
                    
                    if len(confirmed_symptoms) == len(matched_symptoms):
                        disease, criticality, ticket_number, predicted_waiting_time = process_patient(name, confirmed_symptoms)
                        
                        # Store the data in session state
                        st.session_state.patient_data = {
                            "name": name,
                            "symptoms": confirmed_symptoms,
                            "disease": disease,
                            "criticality": criticality,
                            "ticket_number": ticket_number,
                            "waiting_time": predicted_waiting_time
                        }
                        
                        # Display results for confirmation
                        st.markdown(f"""
                            <div class="patient-card">
                                <h3>Review Your Information</h3>
                                <div class="metric-card">
                                    <p>Name</p>
                                    <div class="metric-value">{name}</div>
                                </div>
                                <div class="metric-card">
                                    <p>Ticket Number</p>
                                    <div class="metric-value">#{ticket_number}</div>
                                </div>
                                <div class="metric-card">
                                    <p>Estimated Wait Time</p>
                                    <div class="metric-value">{predicted_waiting_time} min</div>
                                </div>
                                <div class="metric-card">
                                    <p>Priority Level</p>
                                    <div class="metric-value">{criticality}</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Add confirmation and cancel buttons side by side using columns
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Confirm Registration"):
                                st.session_state.registration_complete = True
                                # Increment form counter to reset inputs
                                st.session_state.form_counter += 1
                                st.session_state.patient_data = None
                                st.rerun()
                else:
                    st.markdown('<div class="warning-message">Please check your symptoms and try again.</div>', 
                               unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-message">Please fill in all required fields.</div>', 
                           unsafe_allow_html=True)
    
    else:
        # Display confirmation message and ticket information
        data = st.session_state.patient_data
        st.markdown(f"""
            <div class="confirmation-card">
                <h2>✅ Registration Complete!</h2>
                <p>Welcome, {data['name']}!</p>
            </div>
            
            <div class="patient-card">
                <h3>Your Queue Information</h3>
                <div class="metric-card">
                    <p>Ticket Number</p>
                    <div class="metric-value">#{data['ticket_number']}</div>
                </div>
                <div class="metric-card">
                    <p>Estimated Wait Time</p>
                    <div class="metric-value">{data['waiting_time']} min</div>
                </div>
                <div class="metric-card">
                    <p>Priority Level</p>
                    <div class="metric-value">{data['criticality']}</div>
                </div>
            </div>
            
            <div class="patient-card">
                <h3>Important Notes</h3>
                <p>• Please keep your ticket number handy</p>
                <p>• Listen for your number to be called</p>
                <p>• Ensure you're in the waiting area 10 minutes before your estimated time</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("← Start New Registration"):
            st.session_state.registration_complete = False
            st.session_state.patient_data = None
            # Increment form counter to reset inputs
            st.session_state.form_counter += 1
            st.rerun()

def main():
    apply_custom_css("styles.css")  # Apply the external CSS file
    
    # Initialize session state for user type
    if "user_type" not in st.session_state:
        st.session_state.user_type = None
    
    # Show landing page if no user type selected
    if st.session_state.user_type is None:
        landing_page()
    elif st.session_state.user_type == "Doctor":
        doctor_interface()
    elif st.session_state.user_type == "Patient":
        patient_interface()

if __name__ == "__main__":
    if "current_patient" not in st.session_state:
        st.session_state.current_patient = None
    main()