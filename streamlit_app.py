import streamlit as st
import pymongo
import datetime
import time
import threading
import os
import gridfs
from bson.objectid import ObjectId
from typing import Dict, Any, Optional

# MongoDB connection setup
def get_mongo_client():
    """Create and return a MongoDB client using connection string."""
    connection_string = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://localhost:27017/")
    return pymongo.MongoClient(connection_string)

# Initialize MongoDB client and database
client = get_mongo_client()
db = client.service_workflow
fs = gridfs.GridFS(db)  # For file storage with GridFS

# Collections
customers = db.customers
mrns = db.mrns
service_reports = db.service_reports

# Initialize session state variables if not already present
if "page" not in st.session_state:
    st.session_state.page = 1

if "customer_id" not in st.session_state:
    st.session_state.customer_id = None

if "mrn_code" not in st.session_state:
    st.session_state.mrn_code = None

if "sr_code" not in st.session_state:
    st.session_state.sr_code = None

if "autosave_timer" not in st.session_state:
    st.session_state.autosave_timer = None

if "last_input_time" not in st.session_state:
    st.session_state.last_input_time = time.time()

# Function to navigate between pages
def navigate_to_page(page_num: int):
    """Set the current page in session state."""
    st.session_state.page = page_num

# Autosave functionality
def reset_autosave_timer(callback, *args, **kwargs):
    """Reset the autosave timer."""
    if st.session_state.autosave_timer:
        st.session_state.autosave_timer.cancel()
    
    st.session_state.autosave_timer = threading.Timer(2.0, callback, args=args, kwargs=kwargs)
    st.session_state.autosave_timer.daemon = True
    st.session_state.autosave_timer.start()
    st.session_state.last_input_time = time.time()

def generate_sequential_code(prefix: str) -> str:
    """Generate a sequential code with format PREFIX-YYYYMMDD-XXXX."""
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    # Find the highest number used today
    regex_pattern = f"^{prefix}-{today}-"
    highest_doc = db[f"{prefix.lower()}s"].find_one(
        {"code": {"$regex": regex_pattern}},
        sort=[("code", pymongo.DESCENDING)]
    )
    
    if highest_doc:
        # Extract the number and increment
        try:
            number = int(highest_doc["code"].split("-")[-1]) + 1
        except (ValueError, IndexError):
            number = 1
    else:
        number = 1
        
    return f"{prefix}-{today}-{number:04d}"

# Main app structure
st.title("Service Workflow Application")

# Page 1: CRM Entry
if st.session_state.page == 1:
    st.header("New Service Visit")
    
    # Input fields
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
    
    # Next button
    if st.button("Next", key="next_to_vendor_registration"):
        if not st.session_state.customer_id:
            # If no autosave happened yet, save immediately
            save_customer_data()
        navigate_to_page(2)

# Page 2: Vendor Registration
elif st.session_state.page == 2:
    st.header("Vendor Registration")
    
    # Load customer data
    if st.session_state.customer_id:
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        if customer:
            st.write(f"Company: {customer['name']}")
            
            # Vendor registered checkbox
            vendor_registered = st.checkbox(
                "Vendor is registered", 
                value=customer['status'].get('vendor_registered', False),
                key="vendor_registered"
            )
            
            # Save function for vendor registration
            def save_vendor_status(status):
                customers.update_one(
                    {"_id": ObjectId(st.session_state.customer_id)},
                    {"$set": {"status.vendor_registered": status}}
                )
                st.toast("Vendor status updated", icon="✅")
            
            # Check if checkbox was changed
            if "vendor_registered" in st.session_state and st.session_state.vendor_registered != customer['status'].get('vendor_registered', False):
                save_vendor_status(vendor_registered)
            
            # Next button (only enabled when vendor is registered)
            next_disabled = not vendor_registered
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Previous", key="prev_to_crm"):
                    navigate_to_page(1)
            with col2:
                if st.button("Next", key="next_to_mrn", disabled=next_disabled):
                    navigate_to_page(3)
        else:
            st.error("Customer data not found. Please go back and retry.")
            if st.button("Back to CRM Entry"):
                navigate_to_page(1)
    else:
        st.error("No customer selected. Please start from the beginning.")
        if st.button("Back to CRM Entry"):
            navigate_to_page(1)

# Page 3: MRN Creation
elif st.session_state.page == 3:
    st.header("Create MRN")
    
    # Load customer data
    if st.session_state.customer_id:
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        if customer:
            # Display customer info
            st.write(f"Company: {customer['name']}")
            st.write(f"Contact: {customer['contact_name']}")
            st.write(f"Machines: {customer['machine_count']}")
            
            # Check if MRN already exists
            existing_mrn = mrns.find_one({"customer_id": st.session_state.customer_id})
            
            if existing_mrn:
                st.session_state.mrn_code = existing_mrn['mrn_code']
                st.success(f"MRN already generated: {st.session_state.mrn_code}")
                st.button("Next", key="next_to_service_report", on_click=lambda: navigate_to_page(4))
            else:
                # Generate MRN button
                if st.button("Generate MRN", key="generate_mrn"):
                    # Generate MRN code
                    mrn_code = generate_sequential_code("MRN")
                    
                    # Create MRN document
                    mrn_data = {
                        "customer_id": st.session_state.customer_id,
                        "mrn_code": mrn_code,
                        "created_at": datetime.datetime.now(),
                        "code": mrn_code  # To help with the sequential code search
                    }
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
                    st.button("Next", key="next_to_service_report_after_generate", on_click=lambda: navigate_to_page(4))
            
            # Previous button
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Previous", key="prev_to_vendor"):
                    navigate_to_page(2)
        else:
            st.error("Customer data not found. Please go back and retry.")
            if st.button("Back to CRM Entry"):
                navigate_to_page(1)
    else:
        st.error("No customer selected. Please start from the beginning.")
        if st.button("Back to CRM Entry"):
            navigate_to_page(1)

# Page 4: Service Report
elif st.session_state.page == 4:
    st.header("Service Report")
    
    # Load customer and MRN data
    if st.session_state.customer_id and st.session_state.mrn_code:
        # Display MRN
        st.write(f"MRN Code: {st.session_state.mrn_code}")
        
        # Check if service report already exists
        existing_report = service_reports.find_one({"customer_id": st.session_state.customer_id})
        
        # Initialize inputs with existing data if available
        service_date_default = existing_report.get('service_date') if existing_report else datetime.datetime.now()
        issues_default = existing_report.get('issues_found', '') if existing_report else ''
        actions_default = existing_report.get('actions_taken', '') if existing_report else ''
        
        # Input fields
        service_date = st.date_input("Service date", value=service_date_default, key="service_date")
        issues_found = st.text_area("Issues found", value=issues_default, key="issues_found")
        actions_taken = st.text_area("Actions taken", value=actions_default, key="actions_taken")
        
        # Autosave function for service report
        def save_service_report():
            # Convert date to datetime
            service_datetime = datetime.datetime.combine(service_date, datetime.time())
            
            report_data = {
                "customer_id": st.session_state.customer_id,
                "mrn_code": st.session_state.mrn_code,
                "service_date": service_datetime,
                "issues_found": issues_found,
                "actions_taken": actions_taken,
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
        
        # Set up input change detection for autosave
        for key in ["service_date", "issues_found", "actions_taken"]:
            if key in st.session_state:
                reset_autosave_timer(save_service_report)
        
        # Navigation buttons
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Previous", key="prev_to_mrn"):
                navigate_to_page(3)
        with col2:
            if st.button("Next", key="next_to_telecontroller"):
                # Make sure we save before moving on
                save_service_report()
                navigate_to_page(5)
    else:
        st.error("MRN not generated. Please complete the previous steps.")
        if st.button("Back to MRN Creation"):
            navigate_to_page(3)

# Page 5: Telecontroller Step
elif st.session_state.page == 5:
    st.header("Telecontroller")
    
    # Load customer data
    if st.session_state.customer_id:
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        if customer:
            # Display customer info
            st.write(f"Company: {customer['name']}")
            
            # Check telecontroller status
            telecontroller_done = customer['status'].get('telecontroller_done', False)
            
            # Radio button for telecontroller status
            telecontroller_option = st.radio(
                "Have you filled the telecontroller?",
                ("No", "Yes"),
                index=1 if telecontroller_done else 0,
                key="telecontroller_option"
            )
            
            if telecontroller_option == "Yes":
                # Show file uploader if yes
                uploaded_file = st.file_uploader("Upload telecontroller PDF", type="pdf")
                
                if uploaded_file is not None:
                    # Save file to GridFS
                    file_id = fs.put(
                        uploaded_file.getvalue(), 
                        filename=uploaded_file.name,
                        customer_id=st.session_state.customer_id,
                        content_type="application/pdf"
                    )
                    
                    # Update customer status
                    customers.update_one(
                        {"_id": ObjectId(st.session_state.customer_id)},
                        {"$set": {
                            "status.telecontroller_done": True,
                            "telecontroller_file_id": str(file_id)
                        }}
                    )
                    
                    st.success("Telecontroller PDF uploaded successfully")
                    telecontroller_done = True
                
                elif telecontroller_done:
                    st.success("Telecontroller already completed")
            else:
                # Show link to external site
                st.markdown("[Go to external telecontroller site](https://external-telecontroller-site.com)")
            
            # Navigation buttons
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Previous", key="prev_to_service_report"):
                    navigate_to_page(4)
            with col2:
                if st.button("Next", key="next_to_dashboard", disabled=not telecontroller_done):
                    navigate_to_page(6)
        else:
            st.error("Customer data not found. Please go back and retry.")
            if st.button("Back to Service Report"):
                navigate_to_page(4)
    else:
        st.error("No customer selected. Please start from the beginning.")
        if st.button("Back to CRM Entry"):
            navigate_to_page(1)

# Page 6: Dashboard
elif st.session_state.page == 6:
    st.header("Overview Dashboard")
    
    # Filter options
    st.subheader("Filters")
    show_incomplete = st.checkbox("Show only incomplete records", value=False)
    
    # Query parameters
    query = {}
    if show_incomplete:
        query["$or"] = [
            {"status.vendor_registered": False},
            {"status.mrn_created": False},
            {"status.service_report_created": False},
            {"status.telecontroller_done": False}
        ]
    
    # Get all customers matching the query
    all_customers = list(customers.find(query))
    
    # Prepare data for dataframe
    dashboard_data = []
    for cust in all_customers:
        # Calculate completion percentage
        status = cust.get('status', {})
        completed_steps = sum([
            status.get('vendor_registered', False),
            status.get('mrn_created', False),
            status.get('service_report_created', False),
            status.get('telecontroller_done', False)
        ])
        completion_percentage = (completed_steps / 4) * 100
        
        dashboard_data.append({
            "Company": cust.get('name', ''),
            "Contact": cust.get('contact_name', ''),
            "# Machines": cust.get('machine_count', 0),
            "Vendor": "✓" if status.get('vendor_registered', False) else "❌",
            "MRN": f"✓ ({cust.get('mrn_code', '')})" if status.get('mrn_created', False) else "❌",
            "SR": f"✓ ({cust.get('sr_code', '')})" if status.get('service_report_created', False) else "❌",
            "Telecontroller": "✓" if status.get('telecontroller_done', False) else "❌",
            "Completion": f"{completion_percentage:.0f}%",
            "_id": str(cust.get('_id', ''))
        })
    
    # Display dataframe
    if dashboard_data:
        df = st.dataframe(
            dashboard_data,
            column_config={
                "_id": None,  # Hide the ID column
                "Completion": st.column_config.ProgressColumn(
                    "Completion",
                    help="Workflow completion percentage",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                )
            },
            hide_index=True
        )
        
        # Allow clicking on a row to edit that customer
        if st.button("Create New Service Visit"):
            st.session_state.customer_id = None
            st.session_state.mrn_code = None
            st.session_state.sr_code = None
            navigate_to_page(1)
    else:
        st.info("No records found matching the filter criteria.")
        if st.button("Create New Service Visit"):
            st.session_state.customer_id = None
            st.session_state.mrn_code = None
            st.session_state.sr_code = None
            navigate_to_page(1)

# Handle cleanup of timer when app reruns
def cleanup():
    if hasattr(st.session_state, 'autosave_timer') and st.session_state.autosave_timer:
        st.session_state.autosave_timer.cancel()

# Register cleanup handler
import atexit
atexit.register(cleanup)