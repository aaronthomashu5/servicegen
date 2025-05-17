import streamlit as st
import datetime
import pandas as pd
from bson.objectid import ObjectId
import base64
from io import BytesIO
import json

from utils.helpers import navigate_to_page, create_audit_log
from database.connection import customers, mrns, service_reports

def render():
    """Render the customer view page."""
    st.header("Customer Data View")
    
    # Check if we have a customer ID to display
    if not st.session_state.view_customer_id:
        st.error("No customer selected. Please return to the dashboard.")
        if st.button("Return to Dashboard"):
            navigate_to_page("home")
            st.rerun()
        return
    
    # Get the customer data
    customer = customers.find_one({"_id": ObjectId(st.session_state.view_customer_id)})
    if not customer:
        st.error("Customer not found. The record may have been deleted.")
        if st.button("Return to Dashboard"):
            navigate_to_page("home")
            st.rerun()
        return
    
    # Get related data
    mrn_data = mrns.find_one({"customer_id": st.session_state.view_customer_id, "is_draft": {"$ne": True}})
    service_report_data = service_reports.find_one({"customer_id": st.session_state.view_customer_id})
    
    # Show header with customer name
    st.subheader(f"Viewing data for: {customer.get('name', 'Unknown Customer')}")
    
    # Show tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Customer Information", 
        "Vendor Registration", 
        "MRN Details",
        "Service Report",
        "Telecontroller Data"
    ])
    
    with tab1:
        st.subheader("Customer Information")
        
        # View mode vs Edit mode
        if st.session_state.customer_view_mode == "view":
            # Display customer data in view mode
            st.markdown(f"""
            **Company Name:** {customer.get('name', 'Not specified')}  
            **Contact Name:** {customer.get('contact_name', 'Not specified')}  
            **Contact Phone:** {customer.get('contact_phone', 'Not specified')}  
            **Number of Machines:** {customer.get('machine_count', 0)}  
            **Creation Date:** {customer.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}  
            """)
        else:
            # Edit mode for customer data
            new_name = st.text_input("Company Name", value=customer.get('name', ''))
            new_contact_name = st.text_input("Contact Name", value=customer.get('contact_name', ''))
            new_contact_phone = st.text_input("Contact Phone", value=customer.get('contact_phone', ''))
            new_machine_count = st.number_input("Number of Machines", value=customer.get('machine_count', 0), min_value=0)
            
            if st.button("Save Customer Information", key="save_customer_info"):
                # Update the customer data
                updates = {
                    "name": new_name,
                    "contact_name": new_contact_name,
                    "contact_phone": new_contact_phone,
                    "machine_count": new_machine_count,
                    "updated_at": datetime.datetime.now()
                }
                
                # Record what changed
                changed_fields = {}
                for field, value in updates.items():
                    if field != "updated_at" and customer.get(field) != value:
                        changed_fields[field] = value
                
                # Update the database
                customers.update_one(
                    {"_id": ObjectId(st.session_state.view_customer_id)},
                    {"$set": updates}
                )
                
                # Create audit log entry
                create_audit_log(
                    "customers", 
                    st.session_state.view_customer_id, 
                    "update", 
                    changed_fields
                )
                
                st.success("Customer information updated successfully")
                st.rerun()
    
    with tab2:
        st.subheader("Vendor Registration Data")
        
        if customer.get('status', {}).get('vendor_registered', False):
            # Display vendor registration data
            st.markdown(f"""
            **Vendor Name:** {customer.get('vendor_name', 'Not specified')}  
            **Vendor Address:** {customer.get('vendor_address', 'Not specified')}  
            **Registration Date:** {customer.get('vendor_registered_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}  
            """)
            
            if st.session_state.customer_view_mode == "edit":
                # Edit vendor registration data
                new_vendor_name = st.text_input("Vendor Name", value=customer.get('vendor_name', ''))
                new_vendor_address = st.text_area("Vendor Address", value=customer.get('vendor_address', ''))
                
                if st.button("Save Vendor Information", key="save_vendor_info"):
                    # Update the vendor data
                    updates = {
                        "vendor_name": new_vendor_name,
                        "vendor_address": new_vendor_address,
                        "updated_at": datetime.datetime.now()
                    }
                    
                    # Record what changed
                    changed_fields = {}
                    for field, value in updates.items():
                        if field != "updated_at" and customer.get(field) != value:
                            changed_fields[field] = value
                    
                    # Update the database
                    customers.update_one(
                        {"_id": ObjectId(st.session_state.view_customer_id)},
                        {"$set": updates}
                    )
                    
                    # Create audit log entry
                    create_audit_log(
                        "customers", 
                        st.session_state.view_customer_id, 
                        "update", 
                        changed_fields
                    )
                    
                    st.success("Vendor information updated successfully")
                    st.rerun()
        else:
            st.info("Vendor registration has not been completed yet.")
    
    with tab3:
        st.subheader("MRN Details")
        
        if mrn_data:
            # Show MRN information in a well-structured format
            st.markdown(f"**MRN Code:** {mrn_data.get('mrn_code', 'Not available')}")
            st.markdown(f"**Created on:** {mrn_data.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}")
            
            # Use an expander for detailed information
            with st.expander("Receipt Information", expanded=False):
                st.markdown(f"""
                **Received By:** {mrn_data.get('received_by', 'Not specified')}  
                **Date of Receipt:** {mrn_data.get('date_of_receipt', 'Not specified')}  
                **Delivered By:** {mrn_data.get('delivered_by', 'Not specified')}  
                **Deliverer Contact:** {mrn_data.get('deliverer_contact', 'Not specified')}  
                **Email ID:** {mrn_data.get('email_id', 'Not specified')}  
                """)
            
            with st.expander("Machine Details", expanded=False):
                st.markdown(f"""
                **Model:** {mrn_data.get('model', 'Not specified')}  
                **Machine Type:** {mrn_data.get('machine_type', 'Not specified')}  
                **Serial Number:** {mrn_data.get('serial_no', 'Not specified')}  
                **Accessories Received:** {mrn_data.get('accessories_received', 'Not specified')}  
                """)
            
            with st.expander("Inspection Results", expanded=False):
                checklist_items = ["power_cable", "front_panel", "control_knobs_buttons", 
                                  "display_screen", "gas_hose_connectors", "cooling_fan_vents", 
                                  "welding_torch_socket"]
                
                for item in checklist_items:
                    display_name = item.replace('_', ' ').title()
                    status = mrn_data.get(f'{item}_status', 'Not checked')
                    remarks = mrn_data.get(f'{item}_remarks', '')
                    
                    st.markdown(f"**{display_name}:** {status}")
                    if remarks:
                        st.markdown(f"- Remarks: {remarks}")
                
                st.markdown(f"**Overall Visual Condition:** {mrn_data.get('overall_condition', 'Not assessed')}")
            
            with st.expander("Customer Report", expanded=False):
                st.markdown(f"""
                **Problem Reported:** {mrn_data.get('problem_reported', 'None reported')}  
                **Signature Received By:** {mrn_data.get('signature_received_by', 'Not signed')}  
                **Signature Date:** {mrn_data.get('signature_date', 'Not dated')}  
                **Customer Signature Status:** {'Completed' if mrn_data.get('customer_signature') else 'Not completed'}  
                **Office Notes:** {mrn_data.get('office_use_notes', 'No notes')}  
                """)
                
            # Edit mode for MRN data
            if st.session_state.customer_view_mode == "edit":
                st.markdown("---")
                st.subheader("Edit MRN Data")
                
                # Only allow editing certain fields
                new_serial_no = st.text_input("Serial Number", value=mrn_data.get('serial_no', ''))
                new_model = st.text_input("Model", value=mrn_data.get('model', ''))
                new_problem = st.text_area("Problem Reported", value=mrn_data.get('problem_reported', ''))
                new_notes = st.text_area("Office Notes", value=mrn_data.get('office_use_notes', ''))
                
                if st.button("Save MRN Changes", key="save_mrn_changes"):
                    # Update the MRN data
                    updates = {
                        "serial_no": new_serial_no,
                        "model": new_model,
                        "problem_reported": new_problem,
                        "office_use_notes": new_notes,
                        "updated_at": datetime.datetime.now()
                    }
                    
                    # Record what changed
                    changed_fields = {}
                    for field, value in updates.items():
                        if field != "updated_at" and mrn_data.get(field) != value:
                            changed_fields[field] = value
                    
                    # Update the database
                    mrns.update_one(
                        {"_id": mrn_data["_id"]},
                        {"$set": updates}
                    )
                    
                    # Create audit log entry
                    create_audit_log(
                        "mrns", 
                        str(mrn_data["_id"]), 
                        "update", 
                        changed_fields
                    )
                    
                    st.success("MRN information updated successfully")
                    st.rerun()
        else:
            st.info("MRN has not been created yet.")
    
    with tab4:
        st.subheader("Service Report")
        
        if service_report_data:
            # Show service report data
            st.markdown(f"**Service Report Code:** {service_report_data.get('sr_code', 'Not available')}")
            st.markdown(f"**Created on:** {service_report_data.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}")
            
            # Display other service report data
            with st.expander("Service Details", expanded=False):
                st.markdown(f"""
                **Service Engineer:** {service_report_data.get('service_engineer', 'Not specified')}  
                **Service Date:** {service_report_data.get('service_date', 'Not specified')}  
                **Service Type:** {service_report_data.get('service_type', 'Not specified')}  
                **Machine Status:** {service_report_data.get('machine_status', 'Not specified')}  
                """)
            
            with st.expander("Service Notes", expanded=False):
                st.markdown(f"""
                **Diagnosis:** {service_report_data.get('diagnosis', 'Not provided')}  
                **Work Performed:** {service_report_data.get('work_performed', 'Not provided')}  
                **Parts Replaced:** {service_report_data.get('parts_replaced', 'Not provided')}  
                **Recommendations:** {service_report_data.get('recommendations', 'Not provided')}  
                """)
            
            # Edit mode for Service Report
            if st.session_state.customer_view_mode == "edit":
                st.markdown("---")
                st.subheader("Edit Service Report")
                
                # Allow editing of diagnosis and recommendations
                new_diagnosis = st.text_area("Diagnosis", value=service_report_data.get('diagnosis', ''))
                new_work = st.text_area("Work Performed", value=service_report_data.get('work_performed', ''))
                new_parts = st.text_area("Parts Replaced", value=service_report_data.get('parts_replaced', ''))
                new_recommendations = st.text_area("Recommendations", value=service_report_data.get('recommendations', ''))
                
                if st.button("Save Service Report Changes", key="save_sr_changes"):
                    # Update the service report data
                    updates = {
                        "diagnosis": new_diagnosis,
                        "work_performed": new_work,
                        "parts_replaced": new_parts,
                        "recommendations": new_recommendations,
                        "updated_at": datetime.datetime.now()
                    }
                    
                    # Record what changed
                    changed_fields = {}
                    for field, value in updates.items():
                        if field != "updated_at" and service_report_data.get(field) != value:
                            changed_fields[field] = value
                    
                    # Update the database
                    service_reports.update_one(
                        {"_id": service_report_data["_id"]},
                        {"$set": updates}
                    )
                    
                    # Create audit log entry
                    create_audit_log(
                        "service_reports", 
                        str(service_report_data["_id"]), 
                        "update", 
                        changed_fields
                    )
                    
                    st.success("Service Report updated successfully")
                    st.rerun()
        else:
            st.info("Service Report has not been created yet.")
    
    with tab5:
        st.subheader("Telecontroller Data")
        
        if customer.get('status', {}).get('telecontroller_done', False):
            # Show telecontroller data
            st.markdown(f"""
            **Telecontroller Setup Date:** {customer.get('telecontroller_done_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}  
            **Telecontroller ID:** {customer.get('telecontroller_id', 'Not specified')}  
            **Connection Status:** {customer.get('telecontroller_status', 'Unknown')}  
            """)
        else:
            st.info("Telecontroller setup has not been completed yet.")
    
    # Add PDF/Print functionality
    st.markdown("---")
    st.subheader("Print Options")
    
    print_options = st.multiselect(
        "Select sections to include in the printed document:",
        ["Customer Information", "Vendor Registration", "MRN Details", "Service Report", "Telecontroller Data"],
        default=["Customer Information", "MRN Details", "Service Report"]
    )
    
    if st.button("Generate Printable Document", key="generate_print"):
        # Generate HTML for the selected sections
        html_content = generate_printable_document(customer, mrn_data, service_report_data, print_options)
        
        # Convert to PDF-ready format
        pdf_display_html = f'''
        <html>
        <body>
            <h1 style="text-align:center;">Customer Service Record</h1>
            <h2 style="text-align:center;">{customer.get('name', 'Unknown Customer')}</h2>
            <hr>
            {html_content}
            <hr>
            <p style="text-align:center;">Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p style="text-align:center;">Pofisian Service Management System</p>
        </body>
        </html>
        '''
        
        # Create a download link
        b64_html = base64.b64encode(pdf_display_html.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64_html}" download="customer_record_{customer.get("name", "unknown")}.html">Download HTML Document</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        # Display a preview
        st.subheader("Document Preview")
        st.components.v1.html(pdf_display_html, height=500, scrolling=True)
    
    # Navigation buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Return to Dashboard", key="return_to_dashboard", use_container_width=True):
            navigate_to_page("home")
            st.rerun()
    
    with col2:
        if st.session_state.customer_view_mode == "view":
            if st.button("Switch to Edit Mode", key="switch_to_edit", use_container_width=True):
                st.session_state.customer_view_mode = "edit"
                st.rerun()
        else:
            if st.button("Switch to View Mode", key="switch_to_view", use_container_width=True):
                st.session_state.customer_view_mode = "view"
                st.rerun()

def generate_printable_document(customer, mrn_data, service_report_data, sections):
    """Generate HTML content for the printable document."""
    html_content = ""
    
    # Add each selected section
    if "Customer Information" in sections:
        html_content += f'''
        <div style="margin-bottom:20px;">
            <h3>Customer Information</h3>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Company Name</strong></td><td>{customer.get('name', 'Not specified')}</td></tr>
                <tr><td><strong>Contact Name</strong></td><td>{customer.get('contact_name', 'Not specified')}</td></tr>
                <tr><td><strong>Contact Phone</strong></td><td>{customer.get('contact_phone', 'Not specified')}</td></tr>
                <tr><td><strong>Number of Machines</strong></td><td>{customer.get('machine_count', 0)}</td></tr>
                <tr><td><strong>Creation Date</strong></td><td>{customer.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}</td></tr>
            </table>
        </div>
        '''
    
    if "Vendor Registration" in sections and customer.get('status', {}).get('vendor_registered', False):
        html_content += f'''
        <div style="margin-bottom:20px;">
            <h3>Vendor Registration Data</h3>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Vendor Name</strong></td><td>{customer.get('vendor_name', 'Not specified')}</td></tr>
                <tr><td><strong>Vendor Address</strong></td><td>{customer.get('vendor_address', 'Not specified')}</td></tr>
                <tr><td><strong>Registration Date</strong></td><td>{customer.get('vendor_registered_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}</td></tr>
            </table>
        </div>
        '''
    
    if "MRN Details" in sections and mrn_data:
        html_content += f'''
        <div style="margin-bottom:20px;">
            <h3>MRN Details</h3>
            <p><strong>MRN Code:</strong> {mrn_data.get('mrn_code', 'Not available')}</p>
            <p><strong>Created on:</strong> {mrn_data.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}</p>
            
            <h4>Receipt Information</h4>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Received By</strong></td><td>{mrn_data.get('received_by', 'Not specified')}</td></tr>
                <tr><td><strong>Date of Receipt</strong></td><td>{mrn_data.get('date_of_receipt', 'Not specified')}</td></tr>
                <tr><td><strong>Delivered By</strong></td><td>{mrn_data.get('delivered_by', 'Not specified')}</td></tr>
                <tr><td><strong>Deliverer Contact</strong></td><td>{mrn_data.get('deliverer_contact', 'Not specified')}</td></tr>
                <tr><td><strong>Email ID</strong></td><td>{mrn_data.get('email_id', 'Not specified')}</td></tr>
            </table>
            
            <h4>Machine Details</h4>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Model</strong></td><td>{mrn_data.get('model', 'Not specified')}</td></tr>
                <tr><td><strong>Machine Type</strong></td><td>{mrn_data.get('machine_type', 'Not specified')}</td></tr>
                <tr><td><strong>Serial Number</strong></td><td>{mrn_data.get('serial_no', 'Not specified')}</td></tr>
                <tr><td><strong>Accessories Received</strong></td><td>{mrn_data.get('accessories_received', 'Not specified')}</td></tr>
            </table>
            
            <h4>Inspection Results</h4>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
        '''
        
        # Add inspection items
        checklist_items = ["power_cable", "front_panel", "control_knobs_buttons", 
                          "display_screen", "gas_hose_connectors", "cooling_fan_vents", 
                          "welding_torch_socket"]
        
        for item in checklist_items:
            display_name = item.replace('_', ' ').title()
            status = mrn_data.get(f'{item}_status', 'Not checked')
            remarks = mrn_data.get(f'{item}_remarks', '')
            
            html_content += f'<tr><td><strong>{display_name}</strong></td><td>{status}</td><td>{remarks}</td></tr>'
        
        html_content += f'''
            </table>
            <p><strong>Overall Visual Condition:</strong> {mrn_data.get('overall_condition', 'Not assessed')}</p>
            
            <h4>Customer Report</h4>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Problem Reported</strong></td><td>{mrn_data.get('problem_reported', 'None reported')}</td></tr>
                <tr><td><strong>Signature Received By</strong></td><td>{mrn_data.get('signature_received_by', 'Not signed')}</td></tr>
                <tr><td><strong>Signature Date</strong></td><td>{mrn_data.get('signature_date', 'Not dated')}</td></tr>
                <tr><td><strong>Customer Signature Status</strong></td><td>{'Completed' if mrn_data.get('customer_signature') else 'Not completed'}</td></tr>
                <tr><td><strong>Office Notes</strong></td><td>{mrn_data.get('office_use_notes', 'No notes')}</td></tr>
            </table>
        </div>
        '''
    
    if "Service Report" in sections and service_report_data:
        html_content += f'''
        <div style="margin-bottom:20px;">
            <h3>Service Report</h3>
            <p><strong>Service Report Code:</strong> {service_report_data.get('sr_code', 'Not available')}</p>
            <p><strong>Created on:</strong> {service_report_data.get('created_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}</p>
            
            <h4>Service Details</h4>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Service Engineer</strong></td><td>{service_report_data.get('service_engineer', 'Not specified')}</td></tr>
                <tr><td><strong>Service Date</strong></td><td>{service_report_data.get('service_date', 'Not specified')}</td></tr>
                <tr><td><strong>Service Type</strong></td><td>{service_report_data.get('service_type', 'Not specified')}</td></tr>
                <tr><td><strong>Machine Status</strong></td><td>{service_report_data.get('machine_status', 'Not specified')}</td></tr>
            </table>
            
            <h4>Service Notes</h4>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Diagnosis</strong></td><td>{service_report_data.get('diagnosis', 'Not provided')}</td></tr>
                <tr><td><strong>Work Performed</strong></td><td>{service_report_data.get('work_performed', 'Not provided')}</td></tr>
                <tr><td><strong>Parts Replaced</strong></td><td>{service_report_data.get('parts_replaced', 'Not provided')}</td></tr>
                <tr><td><strong>Recommendations</strong></td><td>{service_report_data.get('recommendations', 'Not provided')}</td></tr>
            </table>
        </div>
        '''
    
    if "Telecontroller Data" in sections and customer.get('status', {}).get('telecontroller_done', False):
        html_content += f'''
        <div style="margin-bottom:20px;">
            <h3>Telecontroller Data</h3>
            <table border="1" cellpadding="5" cellspacing="0" width="100%">
                <tr><td><strong>Telecontroller Setup Date</strong></td><td>{customer.get('telecontroller_done_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')}</td></tr>
                <tr><td><strong>Telecontroller ID</strong></td><td>{customer.get('telecontroller_id', 'Not specified')}</td></tr>
                <tr><td><strong>Connection Status</strong></td><td>{customer.get('telecontroller_status', 'Unknown')}</td></tr>
            </table>
        </div>
        '''
    
    return html_content
