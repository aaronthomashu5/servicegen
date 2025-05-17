import streamlit as st
import datetime
import pandas as pd
from bson.objectid import ObjectId
from utils.helpers import navigate_to_page, reset_autosave_timer, generate_sequential_code, create_workflow_steps_indicator, validate_phone_number, validate_email
from database.connection import customers, service_reports, mrns

def render():
    # Display workflow steps indicator
    create_workflow_steps_indicator("service_report")
    
    st.header("Service Report")
    
    # Instructions in a card
    st.markdown("""
    <div class="css-card">
        <h3>Detailed Service Documentation</h3>
        <p>Document the complete service performed, parts used, and customer acceptance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load customer and MRN data
    if st.session_state.customer_id and st.session_state.mrn_code:
        # Display MRN
        st.write(f"MRN Code: {st.session_state.mrn_code}")
        
        # Get customer data for auto-filling
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        # Get MRN data for prefilling machine details
        mrn_data = mrns.find_one({"customer_id": st.session_state.customer_id, "is_draft": {"$ne": True}})
        
        # Check if service report already exists
        existing_report = service_reports.find_one({"customer_id": st.session_state.customer_id})
        
        # Create tabs for better organization of the form
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Basic Information", "Job Details", "Inspection Checklist", "Parts & Materials", "Labor & Costs", "Signatures"])
        
        with tab1:
            st.subheader("Service Report Information")
            
            # Date field with format DD/MM/YYYY
            service_date = st.date_input(
                "Date", 
                value=existing_report.get('service_date', datetime.datetime.now()) if existing_report else datetime.datetime.now(),
                format="DD/MM/YYYY",
                key="service_date"
            )
            
            # Customer information (auto-filled but editable)
            customer_name = st.text_input(
                "Customer Name", 
                value=customer.get('name', '') if customer else '',
                key="customer_name"
            )
            
            contact_number = st.text_input(
                "Contact Number", 
                value=customer.get('contact_phone', '') if customer else '',
                key="contact_number"
            )
            
            # Validate phone number format
            if contact_number and not validate_phone_number(contact_number):
                st.warning("Please enter a valid phone number")
            
            email_id = st.text_input(
                "Email ID", 
                value=customer.get('email', '') if customer else '',
                key="email_id"
            )
            
            # Validate email format
            if email_id and not validate_email(email_id):
                st.warning("Please enter a valid email address")
            
            # Machine information
            st.subheader("Machine Information")
            
            # Auto-fill from MRN if available
            type_of_machine = st.text_input(
                "Type Of Machine", 
                value=mrn_data.get('machine_type', '') if mrn_data else '',
                key="type_of_machine"
            )
            
            # MRN code (display only)
            st.text_input(
                "MRN", 
                value=st.session_state.mrn_code,
                disabled=True,
                key="mrn_display"
            )
            
            # Job Card Number
            jc_no = st.text_input(
                "JC No.", 
                value=existing_report.get('jc_no', '') if existing_report else '',
                key="jc_no"
            )
            
            # Types of Service (checkboxes)
            st.subheader("Type of Service")
            col1, col2 = st.columns(2)
            with col1:
                ws_selected = st.checkbox(
                    "WS (Warranty Service)", 
                    value=existing_report.get('service_type_ws', False) if existing_report else False,
                    key="service_type_ws"
                )
            with col2:
                gs_selected = st.checkbox(
                    "GS (General Service)", 
                    value=existing_report.get('service_type_gs', False) if existing_report else False,
                    key="service_type_gs"
                )
            
            # Additional service types
            other_service_types = st.multiselect(
                "Other Service Types",
                ["Scheduled Maintenance", "Repair", "Installation", "Training", "Inspection", "Other"],
                default=existing_report.get('other_service_types', []) if existing_report else [],
                key="other_service_types"
            )
            
            # Machine details
            make_model = st.text_input(
                "Make & Model", 
                value=mrn_data.get('model', '') if mrn_data else '',
                key="make_model"
            )
            
            serial_number = st.text_input(
                "Serial Number", 
                value=mrn_data.get('serial_no', '') if mrn_data else '',
                key="serial_number"
            )
            
            running_hours = st.number_input(
                "Running Hours", 
                min_value=0, 
                value=existing_report.get('running_hours', 0) if existing_report else 0,
                key="running_hours"
            )
        
        with tab2:
            st.subheader("Service Details")
            
            # Reported fault
            reported_fault = st.text_area(
                "Reported Fault", 
                value=existing_report.get('reported_fault', '') if existing_report else (mrn_data.get('problem_reported', '') if mrn_data else ''),
                height=100,
                key="reported_fault"
            )
            
            # Problem diagnosis
            problem_diagnosis = st.text_area(
                "Problem Diagnosis", 
                value=existing_report.get('problem_diagnosis', '') if existing_report else '',
                height=100,
                key="problem_diagnosis"
            )
            
            # Job carried out
            job_carried_out = st.text_area(
                "Job Carried Out", 
                value=existing_report.get('job_carried_out', '') if existing_report else '',
                height=150,
                key="job_carried_out"
            )
            
            # Technical difficulties encountered
            technical_difficulties = st.text_area(
                "Technical Difficulties Encountered", 
                value=existing_report.get('technical_difficulties', '') if existing_report else '',
                height=100,
                key="technical_difficulties"
            )
            
            # Recommendations
            recommendations = st.text_area(
                "Recommendations for Future", 
                value=existing_report.get('recommendations', '') if existing_report else '',
                height=100,
                key="recommendations"
            )
            
            # Staff assigned section
            st.subheader("Staff Assigned / Job Details")
            
            # Initialize staff list if not in session state
            if "staff_list" not in st.session_state:
                if existing_report and "staff_assigned" in existing_report:
                    st.session_state.staff_list = existing_report.get('staff_assigned', [])
                else:
                    st.session_state.staff_list = [{}]  # Start with one empty entry
            
            # Function to add a new staff entry
            def add_staff_entry():
                st.session_state.staff_list.append({})
            
            # Function to remove a staff entry
            def remove_staff_entry(index):
                if len(st.session_state.staff_list) > 1:  # Keep at least one entry
                    st.session_state.staff_list.pop(index)
            
            # Display each staff entry
            for i, staff_entry in enumerate(st.session_state.staff_list):
                with st.container():
                    st.markdown(f"**Staff Entry #{i+1}**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        staff_entry['name'] = st.text_input(
                            "Staff Assigned", 
                            value=staff_entry.get('name', ''),
                            key=f"staff_name_{i}"
                        )
                        
                        staff_entry['service_date'] = st.date_input(
                            "Service Date", 
                            value=datetime.datetime.strptime(staff_entry.get('service_date', datetime.datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() 
                                if isinstance(staff_entry.get('service_date', ''), str) and staff_entry.get('service_date', '') 
                                else datetime.datetime.now(),
                            key=f"staff_service_date_{i}"
                        )
                        
                        staff_entry['travel_time'] = st.text_input(
                            "Travel Time (hours)", 
                            value=staff_entry.get('travel_time', ''),
                            key=f"staff_travel_time_{i}"
                        )
                    
                    with col2:
                        # Job start and end times
                        staff_entry['job_start'] = st.time_input(
                            "Job Start", 
                            value=datetime.datetime.strptime(staff_entry.get('job_start', '09:00'), '%H:%M').time() 
                                if isinstance(staff_entry.get('job_start', ''), str) and staff_entry.get('job_start', '') 
                                else datetime.time(9, 0),
                            key=f"staff_job_start_{i}"
                        )
                        
                        staff_entry['job_end'] = st.time_input(
                            "Job End", 
                            value=datetime.datetime.strptime(staff_entry.get('job_end', '17:00'), '%H:%M').time() 
                                if isinstance(staff_entry.get('job_end', ''), str) and staff_entry.get('job_end', '') 
                                else datetime.time(17, 0),
                            key=f"staff_job_end_{i}"
                        )
                        
                        staff_entry['job_status'] = st.selectbox(
                            "Job Status", 
                            options=["Completed", "In Progress", "Pending", "Cancelled"],
                            index=["Completed", "In Progress", "Pending", "Cancelled"].index(staff_entry.get('job_status', 'Completed')) 
                                if staff_entry.get('job_status', '') in ["Completed", "In Progress", "Pending", "Cancelled"] 
                                else 0,
                            key=f"staff_job_status_{i}"
                        )
                    
                    staff_entry['job_type'] = st.selectbox(
                        "Job Type", 
                        options=["Repair", "Maintenance", "Installation", "Training", "Inspection", "Other"],
                        index=["Repair", "Maintenance", "Installation", "Training", "Inspection", "Other"].index(staff_entry.get('job_type', 'Repair')) 
                            if staff_entry.get('job_type', '') in ["Repair", "Maintenance", "Installation", "Training", "Inspection", "Other"] 
                            else 0,
                        key=f"staff_job_type_{i}"
                    )
                    
                    # Remove button for this entry
                    if len(st.session_state.staff_list) > 1:  # Only show remove button if there's more than one entry
                        if st.button("Remove Entry", key=f"remove_staff_{i}"):
                            remove_staff_entry(i)
                            st.rerun()
                    
                    st.markdown("---")
            
            # Button to add more staff entries
            if st.button("Add Another Staff Entry", key="add_staff"):
                add_staff_entry()
                st.rerun()
            
            # Job status/customer comments
            st.subheader("Job Status / Customer Comments")
            job_status_comments = st.text_area(
                "Customer Feedback and Status Notes", 
                value=existing_report.get('job_status_comments', '') if existing_report else '',
                height=100,
                key="job_status_comments"
            )
        
        with tab3:
            st.subheader("Equipment Inspection Checklist")
            
            # Inspection checklist items with status options
            checklist_categories = {
                "Electrical Systems": [
                    "Power Supply Voltage",
                    "Control Circuits",
                    "Electronic Components",
                    "Wiring Condition",
                    "Emergency Stop Function"
                ],
                "Mechanical Systems": [
                    "Safety Guards and Covers",
                    "Lubrication of Moving Parts",
                    "Wear and Tear of Components",
                    "Belt/Chain Tension",
                    "Hydraulic Systems"
                ],
                "General Condition": [
                    "Hoses and Connections",
                    "Leaks (Oil/Water/Gas)",
                    "Operational Test Run",
                    "Sound/Vibration Test",
                    "Cleaning of Equipment"
                ],
                "Specialized Checks": [
                    "Cooling System",
                    "Heating Elements",
                    "Pressure Test",
                    "Calibration (if applicable)",
                    "Software/Firmware Version"
                ]
            }
            
            # Initialize checklist status in session state if not already done
            if "inspection_checklist" not in st.session_state:
                if existing_report and "inspection_checklist" in existing_report:
                    st.session_state.inspection_checklist = existing_report.get('inspection_checklist', {})
                else:
                    st.session_state.inspection_checklist = {}
                    for category, items in checklist_categories.items():
                        for item in items:
                            st.session_state.inspection_checklist[item] = {
                                "status": "Not Checked",
                                "notes": ""
                            }
            
            # Display each category with its checklist items
            for category, items in checklist_categories.items():
                st.markdown(f"#### {category}")
                
                for item in items:
                    col1, col2, col3 = st.columns([3, 2, 3])
                    
                    with col1:
                        st.write(f"**{item}**")
                    
                    with col2:
                        # Get the current status or default to "Not Checked"
                        current_status = "Not Checked"
                        if item in st.session_state.inspection_checklist:
                            current_status = st.session_state.inspection_checklist[item].get("status", "Not Checked")
                        
                        # Status options
                        status_options = ["Not Checked", "Pass", "Fail", "N/A", "Repaired"]
                        
                        # Get the index of the current status
                        status_index = 0
                        if current_status in status_options:
                            status_index = status_options.index(current_status)
                        
                        # Display the status select box
                        selected_status = st.selectbox(
                            "Status",
                            options=status_options,
                            index=status_index,
                            key=f"checklist_status_{item}"
                        )
                        
                        # Update the status in the session state
                        if item not in st.session_state.inspection_checklist:
                            st.session_state.inspection_checklist[item] = {}
                        st.session_state.inspection_checklist[item]["status"] = selected_status
                    
                    with col3:
                        # Get the current notes or default to empty string
                        current_notes = ""
                        if item in st.session_state.inspection_checklist:
                            current_notes = st.session_state.inspection_checklist[item].get("notes", "")
                        
                        # Display the notes text input
                        notes = st.text_input(
                            "Notes",
                            value=current_notes,
                            key=f"checklist_notes_{item}"
                        )
                        
                        # Update the notes in the session state
                        st.session_state.inspection_checklist[item]["notes"] = notes
                
                st.markdown("---")
            
            # Comments or additional notes for the inspection
            inspection_comments = st.text_area(
                "Additional Comments or Findings", 
                value=existing_report.get('inspection_comments', '') if existing_report else '',
                height=100,
                key="inspection_comments"
            )
        
        with tab4:
            st.subheader("Parts & Materials Used / Recommended")
            
            # Initialize parts list if not in session state
            if "parts_list" not in st.session_state:
                if existing_report and "parts_list" in existing_report:
                    st.session_state.parts_list = existing_report.get('parts_list', [])
                else:
                    st.session_state.parts_list = [{}]  # Start with one empty entry
            
            # Function to add a new part entry
            def add_part_entry():
                st.session_state.parts_list.append({})
            
            # Function to remove a part entry
            def remove_part_entry(index):
                if len(st.session_state.parts_list) > 1:  # Keep at least one entry
                    st.session_state.parts_list.pop(index)
            
            # Display each part entry
            for i, part_entry in enumerate(st.session_state.parts_list):
                with st.container():
                    st.markdown(f"**Part/Material Entry #{i+1}**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        part_entry['part_number'] = st.text_input(
                            "Part Number", 
                            value=part_entry.get('part_number', ''),
                            key=f"part_number_{i}"
                        )
                        
                        part_entry['description'] = st.text_input(
                            "Item Description", 
                            value=part_entry.get('description', ''),
                            key=f"part_description_{i}"
                        )
                        
                        part_entry['make'] = st.text_input(
                            "Make", 
                            value=part_entry.get('make', ''),
                            key=f"part_make_{i}"
                        )
                        
                        part_entry['status'] = st.selectbox(
                            "Status",
                            options=["Used", "Replaced", "Pending", "On Order", "Recommended"],
                            index=["Used", "Replaced", "Pending", "On Order", "Recommended"].index(part_entry.get('status', 'Used')) 
                                if part_entry.get('status', '') in ["Used", "Replaced", "Pending", "On Order", "Recommended"] 
                                else 0,
                            key=f"part_status_{i}"
                        )
                    
                    with col2:
                        part_entry['quantity'] = st.number_input(
                            "Quantity", 
                            min_value=0, 
                            value=int(part_entry.get('quantity', 0)) if part_entry.get('quantity', 0) else 0,
                            key=f"part_quantity_{i}"
                        )
                        
                        part_entry['unit_price'] = st.number_input(
                            "Unit Price", 
                            min_value=0.0, 
                            value=float(part_entry.get('unit_price', 0.0)) if part_entry.get('unit_price', 0) else 0.0,
                            format="%.2f",
                            key=f"part_unit_price_{i}"
                        )
                        
                        part_entry['remark'] = st.text_input(
                            "Remark", 
                            value=part_entry.get('remark', ''),
                            key=f"part_remark_{i}"
                        )
                    
                    # Calculate total price for this part
                    part_entry['total_price'] = part_entry['quantity'] * part_entry['unit_price']
                    st.write(f"Total Price: ${part_entry['total_price']:.2f}")
                    
                    # Remove button for this entry
                    if len(st.session_state.parts_list) > 1:  # Only show remove button if there's more than one entry
                        if st.button("Remove Part", key=f"remove_part_{i}"):
                            remove_part_entry(i)
                            st.rerun()
                    
                    st.markdown("---")
            
            # Button to add more part entries
            if st.button("Add Another Part", key="add_part"):
                add_part_entry()
                st.rerun()
            
            # Calculate and display total cost
            total_parts_cost = sum(part['total_price'] for part in st.session_state.parts_list)
            st.subheader(f"Total Parts Cost: ${total_parts_cost:.2f}")
        
        with tab5:
            st.subheader("Labor & Additional Costs")
            
            # Initialize labor costs if not in session state
            if "labor_costs" not in st.session_state:
                if existing_report and "labor_costs" in existing_report:
                    st.session_state.labor_costs = existing_report.get('labor_costs', [])
                else:
                    st.session_state.labor_costs = [{}]  # Start with one empty entry
            
            # Function to add a new labor entry
            def add_labor_entry():
                st.session_state.labor_costs.append({})
            
            # Function to remove a labor entry
            def remove_labor_entry(index):
                if len(st.session_state.labor_costs) > 1:  # Keep at least one entry
                    st.session_state.labor_costs.pop(index)
            
            # Display each labor entry
            for i, labor_entry in enumerate(st.session_state.labor_costs):
                with st.container():
                    st.markdown(f"**Labor/Cost Entry #{i+1}**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        labor_entry['description'] = st.text_input(
                            "Description", 
                            value=labor_entry.get('description', ''),
                            key=f"labor_description_{i}"
                        )
                        
                        labor_entry['type'] = st.selectbox(
                            "Type",
                            options=["Standard Labor", "Overtime Labor", "Travel", "Accommodation", "Other"],
                            index=["Standard Labor", "Overtime Labor", "Travel", "Accommodation", "Other"].index(labor_entry.get('type', 'Standard Labor')) 
                                if labor_entry.get('type', '') in ["Standard Labor", "Overtime Labor", "Travel", "Accommodation", "Other"] 
                                else 0,
                            key=f"labor_type_{i}"
                        )
                    
                    with col2:
                        labor_entry['hours'] = st.number_input(
                            "Hours/Quantity", 
                            min_value=0.0, 
                            value=float(labor_entry.get('hours', 0.0)) if labor_entry.get('hours', 0) else 0.0,
                            format="%.2f",
                            key=f"labor_hours_{i}"
                        )
                        
                        labor_entry['rate'] = st.number_input(
                            "Rate", 
                            min_value=0.0, 
                            value=float(labor_entry.get('rate', 0.0)) if labor_entry.get('rate', 0) else 0.0,
                            format="%.2f",
                            key=f"labor_rate_{i}"
                        )
                        
                        labor_entry['notes'] = st.text_input(
                            "Notes", 
                            value=labor_entry.get('notes', ''),
                            key=f"labor_notes_{i}"
                        )
                    
                    # Calculate total cost for this labor entry
                    labor_entry['total_cost'] = labor_entry['hours'] * labor_entry['rate']
                    st.write(f"Total Cost: ${labor_entry['total_cost']:.2f}")
                    
                    # Remove button for this entry
                    if len(st.session_state.labor_costs) > 1:  # Only show remove button if there's more than one entry
                        if st.button("Remove Entry", key=f"remove_labor_{i}"):
                            remove_labor_entry(i)
                            st.rerun()
                    
                    st.markdown("---")
            
            # Button to add more labor entries
            if st.button("Add Another Labor/Cost Entry", key="add_labor"):
                add_labor_entry()
                st.rerun()
            
            # Calculate and display total labor cost
            total_labor_cost = sum(labor['total_cost'] for labor in st.session_state.labor_costs)
            st.subheader(f"Total Labor & Additional Costs: ${total_labor_cost:.2f}")
            
            # Calculate grand total
            grand_total = total_parts_cost + total_labor_cost
            st.subheader(f"Grand Total: ${grand_total:.2f}")
            
            # Additional cost notes
            cost_notes = st.text_area(
                "Additional Cost Notes", 
                value=existing_report.get('cost_notes', '') if existing_report else '',
                height=100,
                key="cost_notes"
            )
        
        with tab6:
            st.subheader("Signatures and Approval")
            
            # Service completion status
            service_status = st.selectbox(
                "Service Completion Status",
                options=["Completed Successfully", "Completed with Issues", "Partially Completed", "Not Completed", "Pending Follow-up"],
                index=["Completed Successfully", "Completed with Issues", "Partially Completed", "Not Completed", "Pending Follow-up"].index(existing_report.get('service_status', 'Completed Successfully')) 
                    if existing_report and existing_report.get('service_status', '') in ["Completed Successfully", "Completed with Issues", "Partially Completed", "Not Completed", "Pending Follow-up"] 
                    else 0,
                key="service_status"
            )
            
            # Follow-up required?
            follow_up_required = st.checkbox(
                "Follow-up Required", 
                value=existing_report.get('follow_up_required', False) if existing_report else False,
                key="follow_up_required"
            )
            
            # Follow-up details
            if follow_up_required:
                follow_up_details = st.text_area(
                    "Follow-up Details", 
                    value=existing_report.get('follow_up_details', '') if existing_report else '',
                    height=100,
                    key="follow_up_details"
                )
                
                follow_up_date = st.date_input(
                    "Follow-up Date", 
                    value=existing_report.get('follow_up_date', datetime.datetime.now() + datetime.timedelta(days=7)) if existing_report else (datetime.datetime.now() + datetime.timedelta(days=7)),
                    key="follow_up_date"
                )
            
            st.markdown("---")
            
            # Service advisor information
            service_advisor = st.text_input(
                "Service Advisor", 
                value=existing_report.get('service_advisor', '') if existing_report else '',
                key="service_advisor"
            )
            
            service_advisor_date = st.date_input(
                "Service Advisor Date", 
                value=existing_report.get('service_advisor_date', datetime.datetime.now()) if existing_report else datetime.datetime.now(),
                key="service_advisor_date"
            )
            
            # For signature, we could use text input as a placeholder
            # In a real app, you might want to implement a signature pad
            st.write("Service Advisor Signature")
            service_advisor_signature = st.text_input(
                "Type name to acknowledge", 
                value=existing_report.get('service_advisor_signature', '') if existing_report else '',
                key="service_advisor_signature",
                help="In a production environment, this would be replaced with a proper signature pad."
            )
            
            # Customer representative information
            st.markdown("---")
            customer_rep = st.text_input(
                "Customer Representative", 
                value=existing_report.get('customer_rep', '') if existing_report else '',
                key="customer_rep"
            )
            
            customer_rep_date = st.date_input(
                "Customer Representative Date", 
                value=existing_report.get('customer_rep_date', datetime.datetime.now()) if existing_report else datetime.datetime.now(),
                key="customer_rep_date"
            )
            
            # For signature, we could use text input as a placeholder
            st.write("Customer Representative Signature")
            customer_rep_signature = st.text_input(
                "Type name to acknowledge", 
                value=existing_report.get('customer_rep_signature', '') if existing_report else '',
                key="customer_rep_signature",
                help="In a production environment, this would be replaced with a proper signature pad."
            )
            
            # Customer satisfaction
            st.markdown("---")
            st.subheader("Customer Satisfaction")
            
            satisfaction_level = st.slider(
                "Customer Satisfaction Level", 
                min_value=1, 
                max_value=5, 
                value=existing_report.get('satisfaction_level', 5) if existing_report else 5,
                key="satisfaction_level",
                help="1: Very Dissatisfied, 5: Very Satisfied"
            )
            
            # Display satisfaction level as stars
            satisfaction_stars = "⭐" * satisfaction_level
            st.write(f"Rating: {satisfaction_stars}")
            
            # Customer feedback
            customer_feedback = st.text_area(
                "Customer Feedback", 
                value=existing_report.get('customer_feedback', '') if existing_report else '',
                height=100,
                key="customer_feedback"
            )
        
        # Function to save the service report
        def save_service_report():
            # Convert date objects to datetime for MongoDB
            service_datetime = datetime.datetime.combine(service_date, datetime.time())
            service_advisor_datetime = datetime.datetime.combine(service_advisor_date, datetime.time())
            customer_rep_datetime = datetime.datetime.combine(customer_rep_date, datetime.time())
            
            # Follow-up date if it exists
            follow_up_datetime = None
            if follow_up_required:
                follow_up_datetime = datetime.datetime.combine(follow_up_date, datetime.time())
            
            # Prepare the report data
            report_data = {
                "customer_id": st.session_state.customer_id,
                "mrn_code": st.session_state.mrn_code,
                "service_date": service_datetime,
                "customer_name": customer_name,
                "contact_number": contact_number,
                "email_id": email_id,
                "type_of_machine": type_of_machine,
                "jc_no": jc_no,
                "service_type_ws": ws_selected,
                "service_type_gs": gs_selected,
                "other_service_types": other_service_types,
                "make_model": make_model,
                "serial_number": serial_number,
                "running_hours": running_hours,
                
                # Job details tab
                "reported_fault": reported_fault,
                "problem_diagnosis": problem_diagnosis,
                "job_carried_out": job_carried_out,
                "technical_difficulties": technical_difficulties,
                "recommendations": recommendations,
                "staff_assigned": st.session_state.staff_list,
                "job_status_comments": job_status_comments,
                
                # Inspection checklist tab
                "inspection_checklist": st.session_state.inspection_checklist,
                "inspection_comments": inspection_comments,
                
                # Parts & Materials tab
                "parts_list": st.session_state.parts_list,
                "total_parts_cost": total_parts_cost,
                
                # Labor & Costs tab
                "labor_costs": st.session_state.labor_costs,
                "total_labor_cost": total_labor_cost,
                "grand_total": grand_total,
                "cost_notes": cost_notes,
                
                # Signatures tab
                "service_status": service_status,
                "follow_up_required": follow_up_required,
                "follow_up_details": follow_up_details if follow_up_required else "",
                "follow_up_date": follow_up_datetime,
                "service_advisor": service_advisor,
                "service_advisor_date": service_advisor_datetime,
                "service_advisor_signature": service_advisor_signature,
                "customer_rep": customer_rep,
                "customer_rep_date": customer_rep_datetime,
                "customer_rep_signature": customer_rep_signature,
                "satisfaction_level": satisfaction_level,
                "customer_feedback": customer_feedback,
                
                "updated_at": datetime.datetime.now()
            }
            
            if existing_report:
                # Update existing report
                service_reports.update_one(
                    {"_id": existing_report["_id"]},
                    {"$set": report_data}
                )
                st.toast("Service report updated", icon="✅")
                
                # Ensure we have the sr_code in session state
                st.session_state.sr_code = existing_report.get("sr_code")
            else:
                # Generate SR code
                sr_code = generate_sequential_code("SR")
                report_data["sr_code"] = sr_code
                report_data["created_at"] = datetime.datetime.now()
                report_data["code"] = sr_code  # For sequential code generation
                
                # Insert new report
                service_reports.insert_one(report_data)
                
                # Update customer status
                customers.update_one(
                    {"_id": ObjectId(st.session_state.customer_id)},
                    {"$set": {
                        "status.service_report_created": True,
                        "sr_code": sr_code
                    }}
                )
                
                st.session_state.sr_code = sr_code
                st.toast("Service report created", icon="✅")
        
        # Manual save button (more prominent)
        st.markdown("<br>", unsafe_allow_html=True)
        save_col1, save_col2, save_col3 = st.columns([1, 2, 1])
        with save_col2:
            if st.button("💾 Save Service Report", key="manual_save", use_container_width=True):
                save_service_report()
        
        # Set up input change detection for autosave
        # List of keys to monitor for changes
        input_keys = [
            "service_date", "customer_name", "contact_number", "email_id", 
            "type_of_machine", "jc_no", "service_type_ws", "service_type_gs",
            "make_model", "serial_number", "running_hours", "reported_fault",
            "problem_diagnosis", "job_carried_out", "technical_difficulties", 
            "recommendations", "job_status_comments", "inspection_comments",
            "cost_notes", "service_status", "follow_up_required", "follow_up_details",
            "service_advisor", "service_advisor_signature", "customer_rep", 
            "customer_rep_signature", "satisfaction_level", "customer_feedback"
        ]
        
        # Check if any of these keys are in the session state and have changed
        for key in input_keys:
            if key in st.session_state:
                reset_autosave_timer(save_service_report)
        
        # Navigation buttons
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Previous", key="prev_to_mrn", use_container_width=True):
                navigate_to_page("mrn_creation")
        with col2:
            if st.button("Next Step →", key="next_to_telecontroller", use_container_width=True):
                # Make sure we save before moving on
                save_service_report()
                navigate_to_page("telecontroller")
    else:
        st.error("MRN not generated. Please complete the previous steps.")
        if st.button("Back to MRN Creation"):
            navigate_to_page("mrn_creation")
