import streamlit as st
import datetime
import pandas as pd
from bson.objectid import ObjectId
from utils.helpers import navigate_to_page, generate_sequential_code, create_workflow_steps_indicator
from database.connection import customers, mrns

def render():
    # Display workflow steps indicator
    create_workflow_steps_indicator("mrn_creation")
    
    st.header("Create MRN")
    
    # Instructions in a card
    st.markdown("""
    <div class="css-card">
        <h3>Material Return Number</h3>
        <p>Complete this form to record details of the received machine and generate a Material Return Number (MRN).</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load customer data
    if st.session_state.customer_id:
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        if customer:
            # Check if MRN already exists
            existing_mrn = mrns.find_one({"customer_id": st.session_state.customer_id})
            
            if existing_mrn:
                st.session_state.mrn_code = existing_mrn['mrn_code']
                st.success(f"MRN already generated: {st.session_state.mrn_code}")
                
                # Display existing MRN data if available
                st.subheader("Existing MRN Information")
                
                # Create tabs for different sections of the form
                tab1, tab2, tab3, tab4 = st.tabs(["Receipt Information", "Machine Details", "Inspection Checklist", "Customer Report"])
                
                with tab1:
                    st.write("**Receipt Information**")
                    for field in ["received_by", "date_of_receipt", "customer_name", "contact_number", 
                                 "delivered_by", "email_id", "deliverer_contact"]:
                        if field in existing_mrn:
                            st.write(f"{field.replace('_', ' ').title()}: {existing_mrn.get(field, 'Not specified')}")
                
                with tab2:
                    st.write("**Machine Details**")
                    for field in ["model", "machine_type", "serial_no", "accessories_received"]:
                        if field in existing_mrn:
                            st.write(f"{field.replace('_', ' ').title()}: {existing_mrn.get(field, 'Not specified')}")
                
                with tab3:
                    st.write("**Inspection Results**")
                    checklist_items = ["power_cable", "front_panel", "control_knobs_buttons", 
                                      "display_screen", "gas_hose_connectors", "cooling_fan_vents", 
                                      "welding_torch_socket"]
                    
                    for item in checklist_items:
                        if f"{item}_status" in existing_mrn:
                            st.write(f"{item.replace('_', ' ').title()}:")
                            st.write(f"   Status: {existing_mrn.get(f'{item}_status', 'Not checked')}")
                            st.write(f"   Remarks: {existing_mrn.get(f'{item}_remarks', '')}")
                    
                    if "overall_condition" in existing_mrn:
                        st.write(f"Overall Visual Condition: {existing_mrn.get('overall_condition', 'Not assessed')}")
                
                with tab4:
                    st.write("**Customer Report and Signatures**")
                    st.write(f"Problem Reported: {existing_mrn.get('problem_reported', 'None reported')}")
                    st.write(f"Received By: {existing_mrn.get('signature_received_by', '')}")
                    st.write(f"Date Signed: {existing_mrn.get('signature_date', '')}")
                    st.write(f"Customer Signature: {'Completed' if existing_mrn.get('customer_signature') else 'Not completed'}")
                    st.write(f"Office Notes: {existing_mrn.get('office_use_notes', '')}")
                
                # Navigation buttons
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("← Previous", key="prev_to_vendor_existing", use_container_width=True):
                        navigate_to_page("vendor_registration")
                with col2:
                    if st.button("Next Step →", key="next_to_service_report", use_container_width=True):
                        navigate_to_page("service_report")
            else:
                # Create MRN form
                st.subheader("Machine Receipt Form")
                
                # Create tabs for different sections of the form
                tab1, tab2, tab3, tab4 = st.tabs(["Receipt Information", "Machine Details", "Inspection Checklist", "Customer Report"])
                
                # Initialize the form data dictionary to store all inputs
                if "mrn_form_data" not in st.session_state:
                    st.session_state.mrn_form_data = {}
                
                with tab1:
                    st.subheader("Receipt Information")
                    
                    # Received By
                    received_by = st.text_input("Received By (Name/ID)", 
                                               key="mrn_received_by",
                                               help="Name of the person receiving the machine")
                    st.session_state.mrn_form_data["received_by"] = received_by
                    
                    # Date of Receipt
                    receipt_date = st.date_input("Date of Receipt", 
                                               value=datetime.datetime.now(),
                                               key="mrn_receipt_date")
                    st.session_state.mrn_form_data["date_of_receipt"] = receipt_date
                    
                    # Customer details
                    st.subheader("Customer Information")
                    
                    # Get all customers for the dropdown suggestion
                    all_customers = list(customers.find({}, {"name": 1, "contact_phone": 1}))
                    customer_names = [c.get("name", "") for c in all_customers]
                    
                    # Customer name with autocomplete
                    customer_name = customer["name"]  # Pre-fill with current customer
                    st.session_state.mrn_form_data["customer_name"] = customer_name
                    st.text_input("Customer Name", value=customer_name, disabled=True)
                    
                    # Contact number (auto-filled from customer data)
                    contact_number = customer.get("contact_phone", "")
                    st.session_state.mrn_form_data["contact_number"] = contact_number
                    st.text_input("Contact Number", value=contact_number, disabled=True)
                    
                    # Delivered By
                    st.subheader("Delivery Information")
                    delivered_by = st.text_input("Delivered By (Name/Company)", 
                                                key="mrn_delivered_by")
                    st.session_state.mrn_form_data["delivered_by"] = delivered_by
                    
                    # Delivery contact information
                    email_id = st.text_input("Email ID", key="mrn_email_id")
                    st.session_state.mrn_form_data["email_id"] = email_id
                    
                    deliverer_contact = st.text_input("Contact Number", key="mrn_deliverer_contact")
                    st.session_state.mrn_form_data["deliverer_contact"] = deliverer_contact
                
                with tab2:
                    st.subheader("Machine Details")
                    
                    # Model
                    model = st.text_input("Model", key="mrn_model")
                    st.session_state.mrn_form_data["model"] = model
                    
                    # Machine Type
                    machine_type = st.text_input("Machine Type", key="mrn_machine_type")
                    st.session_state.mrn_form_data["machine_type"] = machine_type
                    
                    # Serial Number
                    serial_no = st.text_input("Serial No", key="mrn_serial_no")
                    st.session_state.mrn_form_data["serial_no"] = serial_no
                    
                    # Accessories Received
                    accessories = st.text_area("Accessories Received", key="mrn_accessories")
                    st.session_state.mrn_form_data["accessories_received"] = accessories
                
                with tab3:
                    st.subheader("Machine Visual Inspection Checklist")
                    
                    # Define inspection items with detailed descriptions
                    inspection_items = [
                        {"name": "Power Cable", "key": "power_cable", "description": "Check for fraying, damage, proper connection"},
                        {"name": "Front Panel", "key": "front_panel", "description": "Check for cracks, dents, display clarity"},
                        {"name": "Control Knobs/Buttons", "key": "control_knobs_button", "description": "Test functionality, check for sticking or damage"},
                        {"name": "Display Screen", "key": "display_screen", "description": "Verify screen works, no dead pixels or cracks"},
                        {"name": "Gas Hose Connectors", "key": "gas_hose_connectors", "description": "Check for proper connection, leaks, damage"},
                        {"name": "Cooling Fan/Vents", "key": "cooling_fan_vents", "description": "Ensure fans spin freely, vents are clear"},
                        {"name": "Welding Torch Socket", "key": "welding_torch_socket", "description": "Check connection quality and secure fit"}
                    ]
                    
                    # Track overall inspection status
                    inspection_statuses = []
                    
                    # Create inspection form with improved UI
                    for item in inspection_items:
                        with st.expander(f"**{item['name']}**", expanded=False):
                            st.info(item['description'])
                            
                            # Status selection
                            status = st.selectbox(
                                "Status:", 
                                ["Good", "Fair", "Poor", "Not Applicable"],
                                key=f"mrn_{item['key']}_status"
                            )
                            st.session_state.mrn_form_data[f"{item['key']}_status"] = status
                            inspection_statuses.append(status)
                            
                            # Remarks
                            remarks = st.text_input(
                                "Remarks:", 
                                key=f"mrn_{item['key']}_remarks"
                            )
                            st.session_state.mrn_form_data[f"{item['key']}_remarks"] = remarks
                            
                            # Display visual indicator
                            if status == "Good":
                                st.success("✓ Good condition")
                            elif status == "Fair":
                                st.warning("⚠ Fair condition - monitor during service")
                            elif status == "Poor":
                                st.error("✗ Poor condition - requires attention")
                    
                    # Calculate inspection score
                    valid_statuses = [s for s in inspection_statuses if s != "Not Applicable"]
                    good_count = valid_statuses.count("Good")
                    fair_count = valid_statuses.count("Fair")
                    poor_count = valid_statuses.count("Poor")
                    
                    if valid_statuses:
                        inspection_score = (good_count * 3 + fair_count * 1) / (len(valid_statuses) * 3) * 100
                        st.progress(inspection_score/100, f"Overall Inspection Score: {inspection_score:.0f}%")
                    
                    # Overall Visual Condition with recommendation
                    st.subheader("Overall Visual Condition")
                    overall_condition = st.radio(
                        "Rate the overall condition:", 
                        ["Good", "Fair", "Poor"],
                        horizontal=True,
                        key="mrn_overall_condition"
                    )
                    st.session_state.mrn_form_data["overall_condition"] = overall_condition
                
                with tab4:
                    st.subheader("Problem Reported by Customer")
                    
                    # Problem description
                    problem_reported = st.text_area(
                        "Describe the problem reported by the customer:",
                        height=150,
                        key="mrn_problem_reported"
                    )
                    st.session_state.mrn_form_data["problem_reported"] = problem_reported
                    
                    # Signatures
                    st.subheader("Signatures and Acknowledgement")
                    
                    signature_name = st.text_input(
                        "Received By (Signature or printed name):",
                        key="mrn_signature_name"
                    )
                    st.session_state.mrn_form_data["signature_received_by"] = signature_name
                    
                    signature_date = st.date_input(
                        "Date:",
                        value=datetime.datetime.now(),
                        key="mrn_signature_date"
                    )
                    st.session_state.mrn_form_data["signature_date"] = signature_date
                    
                    customer_signature = st.checkbox(
                        "Customer Signature Received",
                        key="mrn_customer_signature"
                    )
                    st.session_state.mrn_form_data["customer_signature"] = customer_signature
                    
                    # Office Use
                    st.subheader("Office Use")
                    
                    office_notes = st.text_area(
                        "Notes for office use only:",
                        height=100,
                        key="mrn_office_notes"
                    )
                    st.session_state.mrn_form_data["office_use_notes"] = office_notes
                
                # Add a save button before generate
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save Form Data (Without Generating MRN)", key="save_mrn_form"):
                    # Save the form data without generating MRN
                    if st.session_state.customer_id and "mrn_form_data" in st.session_state:
                        # Save form data to database without generating MRN
                        draft_data = st.session_state.mrn_form_data.copy()
                        draft_data.update({
                            "customer_id": st.session_state.customer_id,
                            "is_draft": True,
                            "updated_at": datetime.datetime.now()
                        })
                        
                        # Convert date objects to strings
                        for key, value in draft_data.items():
                            if isinstance(value, datetime.date):
                                draft_data[key] = value.isoformat()
                        
                        # Check if draft exists already
                        existing_draft = mrns.find_one({
                            "customer_id": st.session_state.customer_id, 
                            "is_draft": True
                        })
                        
                        if existing_draft:
                            # Update existing draft
                            mrns.update_one(
                                {"_id": existing_draft["_id"]},
                                {"$set": draft_data}
                            )
                        else:
                            # Insert new draft
                            mrns.insert_one(draft_data)
                        
                        st.toast("Form data saved as draft", icon="✅")
                
                # Generate MRN button
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([3, 4, 3])
                with col2:
                    if st.button("Generate MRN & Save Form", key="generate_mrn", use_container_width=True):
                        # Generate MRN code
                        mrn_code = generate_sequential_code("MRN")
                        
                        # Combine the form data with the MRN information
                        mrn_data = st.session_state.mrn_form_data.copy()
                        mrn_data.update({
                            "customer_id": st.session_state.customer_id,
                            "mrn_code": mrn_code,
                            "created_at": datetime.datetime.now(),
                            "code": mrn_code  # To help with the sequential code search
                        })
                        
                        # Convert any non-serializable objects (like datetime.date) to strings
                        for key, value in mrn_data.items():
                            if isinstance(value, datetime.date):
                                mrn_data[key] = value.isoformat()
                        
                        # Insert MRN data
                        mrns.insert_one(mrn_data)
                        
                        # Update customer status
                        customers.update_one(
                            {"_id": ObjectId(st.session_state.customer_id)},
                            {"$set": {
                                "status.mrn_created": True,
                                "mrn_code": mrn_code
                            }}
                        )
                        
                        st.session_state.mrn_code = mrn_code
                        st.success(f"MRN Generated: {mrn_code}")
                        
                        # Navigation buttons after generating
                        st.markdown("<br>", unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("← Previous", key="prev_to_vendor_after_generate", use_container_width=True):
                                navigate_to_page("vendor_registration")
                        with col2:
                            if st.button("Next Step →", key="next_to_service_report_after_generate", use_container_width=True):
                                navigate_to_page("service_report")
                
                # Just the previous button if MRN not yet generated
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("← Previous", key="prev_to_vendor", use_container_width=True):
                        navigate_to_page("vendor_registration")
        else:
            st.error("Customer data not found. Please go back and retry.")
            if st.button("Back to CRM Entry"):
                navigate_to_page("crm_entry")
    else:
        st.error("No customer selected. Please start from the beginning.")
        if st.button("Back to CRM Entry"):
            navigate_to_page("crm_entry")
