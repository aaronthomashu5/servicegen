import streamlit as st
import datetime
from bson.objectid import ObjectId
from utils.helpers import navigate_to_page, reset_autosave_timer, create_workflow_steps_indicator
from database.connection import customers

def render():
    # Display workflow steps indicator
    create_workflow_steps_indicator("crm_entry")
    
    st.header("New Service Visit")
    
    # Instructions in a card
    st.markdown("""
    <div class="css-card">
        <h3>Customer Registration</h3>
        <p>Enter the customer information to start the service workflow process.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input fields with default values from session state or database
    if st.session_state.customer_id:
        # If we have a customer ID, try to load their data from database
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        if customer:
            # Use database values as defaults
            company_name = st.text_input("Company name", value=customer.get('name', ''), key="company_name")
            contact_name = st.text_input("Procurement contact name", value=customer.get('contact_name', ''), key="contact_name")
            contact_phone = st.text_input("Procurement contact phone", value=customer.get('contact_phone', ''), key="contact_phone")
            machine_count = st.number_input("Number of machines", min_value=0, step=1, value=customer.get('machine_count', 0), key="machine_count")
        else:
            # If customer ID is invalid, use empty defaults
            company_name = st.text_input("Company name", key="company_name")
            contact_name = st.text_input("Procurement contact name", key="contact_name")
            contact_phone = st.text_input("Procurement contact phone", key="contact_phone")
            machine_count = st.number_input("Number of machines", min_value=0, step=1, key="machine_count")
    else:
        # No customer ID, start fresh
        company_name = st.text_input("Company name", key="company_name")
        contact_name = st.text_input("Procurement contact name", key="contact_name")
        contact_phone = st.text_input("Procurement contact phone", key="contact_phone")
        machine_count = st.number_input("Number of machines", min_value=0, step=1, key="machine_count")
    
    # Autosave function for CRM entry
    def save_customer_data():
        customer_data = {
            "name": company_name,
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "machine_count": machine_count,
            "created_at": datetime.datetime.now(),
            "status": {
                "vendor_registered": False,
                "mrn_created": False,
                "service_report_created": False,
                "telecontroller_done": False
            }
        }
        
        # If customer_id exists, update; otherwise insert
        if st.session_state.customer_id:
            customers.update_one(
                {"_id": ObjectId(st.session_state.customer_id)}, 
                {"$set": customer_data}
            )
        else:
            result = customers.insert_one(customer_data)
            st.session_state.customer_id = str(result.inserted_id)
            
        st.toast("Customer data saved", icon="✅")
    
    # Set up input change detection for autosave
    for key in ["company_name", "contact_name", "contact_phone", "machine_count"]:
        if key in st.session_state:
            reset_autosave_timer(save_customer_data)
    
    # Add a manual save button
    if st.button("💾 Save Information", key="save_customer_info"):
        save_customer_data()
    
    # Form validation
    has_errors = False
    if not company_name.strip():
        st.error("Company name is required")
        has_errors = True
    if not contact_name.strip():
        st.error("Contact name is required")
        has_errors = True
    if not contact_phone.strip():
        st.error("Contact phone is required")
        has_errors = True
    if machine_count <= 0:
        st.warning("Please specify at least 1 machine")
        has_errors = True
    
    # Next button with better styling
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([5, 2, 5])
    with col2:
        if st.button("Next Step →", key="next_to_vendor_registration", use_container_width=True, disabled=has_errors):
            if not st.session_state.customer_id:
                # If no autosave happened yet, save immediately
                save_customer_data()
            navigate_to_page("vendor_registration")
            st.rerun()
