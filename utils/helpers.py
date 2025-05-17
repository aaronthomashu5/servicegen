import streamlit as st
import datetime
import time
import threading
import pymongo
from database.connection import db

# Function to navigate between pages
def navigate_to_page(page_name: str):
    """Set the current page in session state."""
    st.session_state.page = page_name

# Autosave functionality
def reset_autosave_timer(callback, *args, **kwargs):
    """Reset the autosave timer."""
    if "autosave_timer" in st.session_state and st.session_state.autosave_timer:
        st.session_state.autosave_timer.cancel()
    
    # Set a shorter timer for faster saving (1 second)
    st.session_state.autosave_timer = threading.Timer(1.0, callback, args=args, kwargs=kwargs)
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

# Calculate progress based on workflow steps
def calculate_workflow_progress(status: dict) -> float:
    """Calculate the workflow progress percentage."""
    completed_steps = sum([
        status.get('vendor_registered', False),
        status.get('mrn_created', False),
        status.get('service_report_created', False),
        status.get('telecontroller_done', False)
    ])
    return (completed_steps / 4) * 100

# Create a horizontal workflow progress bar
def create_workflow_steps_indicator(current_step):
    """Create a horizontal workflow steps indicator."""
    # Display current date in the top right
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    st.markdown(f"<div style='text-align: right; color: #666; margin-bottom: 20px;'>{current_date}</div>", 
                unsafe_allow_html=True)
    
    if st.session_state.customer_id:
        from database.connection import customers
        from bson.objectid import ObjectId
        
        customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
        if customer:
            status = customer.get('status', {})
            
            # Define all steps with their completion status
            steps = [
                {"name": "CRM Entry", "page": "crm_entry", "completed": True},  # Always completed if we have a customer
                {"name": "Vendor Registration", "page": "vendor_registration", "completed": status.get('vendor_registered', False)},
                {"name": "MRN Creation", "page": "mrn_creation", "completed": status.get('mrn_created', False)},
                {"name": "Service Report", "page": "service_report", "completed": status.get('service_report_created', False)},
                {"name": "Telecontroller", "page": "telecontroller", "completed": status.get('telecontroller_done', False)}
            ]
            
            # Create columns for each step
            cols = st.columns(len(steps))
            
            # Render each step in its column
            for i, step in enumerate(steps):
                with cols[i]:
                    # Determine step status class
                    if step["page"] == current_step:
                        class_suffix = "active"
                    elif step["completed"]:
                        class_suffix = "completed"
                    else:
                        class_suffix = ""
                    
                    # Create HTML for the step
                    st.markdown(f"""
                    <div class="step step-{class_suffix}">
                        <div class="step-line"></div>
                        <div class="step-circle">{i+1}</div>
                        <div class="step-name">{step["name"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Add some space after the steps indicator
    st.markdown("<br>", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables if not already present."""
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    if "customer_id" not in st.session_state:
        st.session_state.customer_id = None
    
    if "view_customer_id" not in st.session_state:
        st.session_state.view_customer_id = None
    
    if "customer_view_mode" not in st.session_state:
        st.session_state.customer_view_mode = "view"
    
    if "mrn_code" not in st.session_state:
        st.session_state.mrn_code = None
    
    if "sr_code" not in st.session_state:
        st.session_state.sr_code = None
    
    if "autosave_timer" not in st.session_state:
        st.session_state.autosave_timer = None
    
    if "last_input_time" not in st.session_state:
        st.session_state.last_input_time = time.time()

# Handle cleanup of timer when app reruns
def cleanup():
    if hasattr(st.session_state, 'autosave_timer') and st.session_state.autosave_timer:
        st.session_state.autosave_timer.cancel()

# Create sidebar menu
def create_sidebar():
    with st.sidebar:
        st.title("Pofisian Services")
        st.image("https://via.placeholder.com/150?text=Pofisian", width=150)  # Placeholder logo
        
        # User info
        st.markdown("""
        <div style="background-color: rgba(255,87,51,0.1); padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <div style="font-weight: bold; font-size: 1.2em;">Welcome, Pofisian!</div>
            <div style="font-size: 0.9em; color: #666;">Service Technician</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.subheader("Navigation")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.customer_id = None
            st.session_state.mrn_code = None
            st.session_state.sr_code = None
            navigate_to_page("home")
            st.rerun()
        
        if st.button("🆕 New Service Visit", use_container_width=True):
            import datetime
            from database.connection import customers
            
            # Reset session state for a new customer
            st.session_state.customer_id = None
            st.session_state.mrn_code = None
            st.session_state.sr_code = None
            
            # Create a temporary customer record to ensure we have an ID
            temp_customer_data = {
                "name": "New Customer",
                "contact_name": "",
                "contact_phone": "",
                "machine_count": 0,
                "created_at": datetime.datetime.now(),
                "is_temporary": True,  # Flag to identify this as a new record
                "status": {
                    "vendor_registered": False,
                    "mrn_created": False,
                    "service_report_created": False,
                    "telecontroller_done": False
                }
            }
            
            # Insert the temporary customer and store the ID
            result = customers.insert_one(temp_customer_data)
            st.session_state.customer_id = str(result.inserted_id)
            
            # Reset any form input values that might be in session state
            if "company_name" in st.session_state:
                del st.session_state.company_name
            if "contact_name" in st.session_state:
                del st.session_state.contact_name
            if "contact_phone" in st.session_state:
                del st.session_state.contact_phone
            if "machine_count" in st.session_state:
                del st.session_state.machine_count
                
            # Navigate to the CRM entry page
            navigate_to_page("crm_entry")
            st.toast("New customer record created. Please fill in the details.", icon="✅")
            st.rerun()
            
            # Show success message
            st.sidebar.success("Starting a new customer service workflow")
            
            navigate_to_page("crm_entry")
            st.rerun()
        
        # Display current workflow progress if in a workflow
        if st.session_state.customer_id:
            from database.connection import customers
            from bson.objectid import ObjectId
            
            customer = customers.find_one({"_id": ObjectId(st.session_state.customer_id)})
            if customer:
                st.divider()
                st.subheader("Current Workflow")
                st.write(f"Company: {customer.get('name', 'Unknown')}")
                
                # Progress bar
                status = customer.get('status', {})
                progress = calculate_workflow_progress(status)
                st.progress(progress/100, f"Progress: {progress:.0f}%")
                
                # Create the workflow step indicators
                steps = [
                    ("1. CRM Entry", True),  # Always completed if we have a customer
                    ("2. Vendor Registration", status.get('vendor_registered', False)),
                    ("3. MRN Creation", status.get('mrn_created', False)),
                    ("4. Service Report", status.get('service_report_created', False)),
                    ("5. Telecontroller", status.get('telecontroller_done', False))
                ]
                
                # Display workflow steps with icons
                for step, completed in steps:
                    if completed:
                        st.markdown(f"<div class='completion-step'><span class='icon'>✅</span> {step}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='completion-step'><span class='icon'>⬜</span> {step}</div>", unsafe_allow_html=True)
                
                # Cancel button
                if st.button("❌ Cancel Workflow", use_container_width=True):
                    st.session_state.customer_id = None
                    st.session_state.mrn_code = None
                    st.session_state.sr_code = None
                    navigate_to_page("home")
                    st.rerun()
        
        # Add logout and app management buttons at the bottom
        st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
        st.sidebar.markdown("<hr>", unsafe_allow_html=True)
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄 Restart App", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                # Reinitialize
                init_session_state()
                navigate_to_page("home")
                st.rerun()
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                # In a real app, this would handle authentication logout
                st.sidebar.success("Logged out successfully!")
                # For now, just redirect to home
                st.session_state.customer_id = None
                st.session_state.mrn_code = None
                st.session_state.sr_code = None
                navigate_to_page("home")
                st.rerun()

# Create data versioning and audit helpers
def create_audit_log(collection_name, document_id, action, changed_fields=None, user_id="system"):
    """Create an audit log entry for data changes.
    
    Args:
        collection_name: The name of the collection being modified
        document_id: The ID of the document being modified
        action: The action being performed (create, update, delete)
        changed_fields: Dictionary of fields that were changed {field_name: new_value}
        user_id: The ID of the user making the change
    """
    from database.connection import db
    import datetime
    
    audit_entry = {
        "collection": collection_name,
        "document_id": str(document_id),
        "action": action,
        "changed_fields": changed_fields or {},
        "user_id": user_id,
        "timestamp": datetime.datetime.now()
    }
    
    # Insert into audit collection
    db.audit_logs.insert_one(audit_entry)
    
def create_document_version(collection_name, document_id, document_data):
    """Create a version record of a document at a point in time.
    
    Args:
        collection_name: The name of the collection
        document_id: The ID of the document
        document_data: The full document data to version
    """
    from database.connection import db
    import datetime
    
    # Add version metadata
    version_data = document_data.copy()
    version_data["_original_id"] = str(document_id)
    version_data["_collection"] = collection_name
    version_data["_version_date"] = datetime.datetime.now()
    
    # Insert into versions collection
    db.document_versions.insert_one(version_data)

def get_document_history(collection_name, document_id):
    """Get the version history of a document.
    
    Args:
        collection_name: The name of the collection
        document_id: The ID of the document
        
    Returns:
        List of document versions in chronological order
    """
    from database.connection import db
    
    # Query for versions of this document
    versions = list(db.document_versions.find(
        {"_original_id": str(document_id), "_collection": collection_name}
    ).sort("_version_date", 1))
    
    return versions

# Data validation helpers
def validate_phone_number(phone):
    """Validate a phone number format."""
    import re
    # Allow various phone formats with optional country code
    pattern = r'^\+?[0-9]{1,4}?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    """Validate an email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
