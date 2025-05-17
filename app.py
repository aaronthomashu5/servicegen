import streamlit as st
import atexit
import datetime
import os
from bson.objectid import ObjectId
from utils.helpers import init_session_state, create_sidebar, cleanup, navigate_to_page
from database.connection import customers

# Import all page modules
from pages import crm_entry, vendor_registration, mrn_creation, service_report, telecontroller, customer_view

# Load custom CSS
def load_css():
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.streamlit', 'style.css')
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Register cleanup handler
atexit.register(cleanup)

# Initialize session state
init_session_state()

# Page title and sidebar
st.set_page_config(
    page_title="Pofisian Service Workflow",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# Create sidebar
create_sidebar()

# Routing to the correct page
if st.session_state.page == "home":
    # Display current date in the top right
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    st.markdown(f"<div style='text-align: right; color: #666; margin-bottom: 20px;'>{current_date}</div>", 
                unsafe_allow_html=True)
    
    # Welcome header with custom styling
    st.markdown("<div class='welcome-message'>Welcome, Pofisian! 👋</div>", unsafe_allow_html=True)
    
    # Show summary statistics
    st.header("Service Overview")
    
    # Calculate statistics
    total_customers = customers.count_documents({})
    total_machines = sum([c.get('machine_count', 0) for c in customers.find({}, {"machine_count": 1})])
    
    # Calculate completion statistics
    completion_stats = {
        "Complete": 0,
        "In Progress": 0,
        "Not Started": 0
    }
    
    for cust in customers.find({}, {"status": 1}):
        status = cust.get('status', {})
        completed_steps = sum([
            status.get('vendor_registered', False),
            status.get('mrn_created', False),
            status.get('service_report_created', False),
            status.get('telecontroller_done', False)
        ])
        
        if completed_steps == 4:
            completion_stats["Complete"] += 1
        elif completed_steps > 0:
            completion_stats["In Progress"] += 1
        else:
            completion_stats["Not Started"] += 1
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Total Clients</div>
        </div>
        """.format(total_customers), unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Total Machines Under Service</div>
        </div>
        """.format(total_machines), unsafe_allow_html=True)
    with col3:
        avg_machines = round(total_machines / total_customers, 1) if total_customers > 0 else 0
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Avg. Machines per Client</div>
        </div>
        """.format(avg_machines), unsafe_allow_html=True)
    
    # Add a visual representation of completion status using a chart
    if total_customers > 0:
        st.subheader("Service Completion Status")
        
        # Create a simple bar chart to visualize completion status
        chart_data = {
            "Status": list(completion_stats.keys()),
            "Count": list(completion_stats.values())
        }
        
        # Add some styling to the chart
        st.bar_chart(chart_data, x="Status", y="Count", color="#FF5733")
        
        # Add a pie chart showing percentage breakdown
        try:
            import pandas as pd
            import plotly.express as px
            
            df = pd.DataFrame({
                "Status": list(completion_stats.keys()),
                "Count": list(completion_stats.values())
            })
            
            if sum(df["Count"]) > 0:
                fig = px.pie(df, values="Count", names="Status", 
                            title="Service Workflows Status Distribution",
                            color_discrete_sequence=["#28a745", "#ffc107", "#dc3545"])
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            # Fallback if plotly is not available
            st.write("Status breakdown:", completion_stats)
    
    # Show dashboard with client info
    st.subheader("Client Overview")
    
    # Advanced filter options
    st.subheader("Filter Options")
    with st.expander("Advanced Filters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            show_incomplete = st.checkbox("Show only incomplete records", value=False)
        with col2:
            show_complete = st.checkbox("Show only complete records", value=False)
        
        # Filter by date range
        st.write("Filter by creation date:")
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("Start date", value=None)
        with date_col2:
            end_date = st.date_input("End date", value=None)
        
        # Search by company name
        search_term = st.text_input("Search by company name", "")
    
    # Sorting options
    sort_options = {
        "Company Name (A-Z)": ("name", 1),
        "Company Name (Z-A)": ("name", -1),
        "Newest First": ("created_at", -1),
        "Oldest First": ("created_at", 1),
        "Most Machines": ("machine_count", -1),
        "Fewest Machines": ("machine_count", 1),
        "Highest Completion": ("completion_score", -1),
        "Lowest Completion": ("completion_score", 1)
    }
    
    sort_by = st.selectbox("Sort by:", options=list(sort_options.keys()))
    sort_field, sort_direction = sort_options[sort_by]
    
    # Query parameters
    query = {}
    
    # Handle filter logic
    if show_incomplete and show_complete:
        # If both are checked, show all (no filter)
        pass
    elif show_incomplete:
        query["$or"] = [
            {"status.vendor_registered": False},
            {"status.mrn_created": False},
            {"status.service_report_created": False},
            {"status.telecontroller_done": False}
        ]
    elif show_complete:
        query["$and"] = [
            {"status.vendor_registered": True},
            {"status.mrn_created": True},
            {"status.service_report_created": True},
            {"status.telecontroller_done": True}
        ]
    
    # Date range filtering
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.datetime.combine(start_date, datetime.time.min)
        if end_date:
            date_query["$lte"] = datetime.datetime.combine(end_date, datetime.time.max)
        if date_query:
            query["created_at"] = date_query
    
    # Company name search
    if search_term:
        query["name"] = {"$regex": search_term, "$options": "i"}  # Case-insensitive search
    
    # Get all customers matching the query with sorting
    all_customers = list(customers.find(query).sort(sort_field, sort_direction))
    
    # Filter by machine serial number (search in MRNs)
    serial_search = st.text_input("Search by machine serial number:", "")
    if serial_search.strip():
        from database.connection import mrns
        # Find MRNs with matching serial numbers
        matching_mrns = list(mrns.find({"serial_no": {"$regex": serial_search, "$options": "i"}}))
        if matching_mrns:
            # Get customer IDs from matching MRNs
            customer_ids = [mrn.get("customer_id") for mrn in matching_mrns]
            # Filter customers to only those with matching MRNs
            all_customers = [c for c in all_customers if str(c.get("_id")) in customer_ids]
            st.success(f"Found {len(all_customers)} customer(s) with machines matching serial number pattern: {serial_search}")
        else:
            st.info(f"No machines found with serial number matching: {serial_search}")
            all_customers = []
    
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
            "Actions": "🔍📝",  # Edit/View action icons
            "_id": str(cust.get('_id', ''))
        })
    
    # Display dataframe
    if dashboard_data:
        # Create a selection mechanism
        st.markdown("**Click on any row to continue or view that workflow**")
        
        # Create the dataframe with selection
        selection = st.dataframe(
            dashboard_data,
            column_config={
                "_id": None,  # Hide the ID column
                "Completion": st.column_config.ProgressColumn(
                    "Completion",
                    help="Workflow completion percentage",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                ),
                "Actions": st.column_config.Column(
                    "Actions",
                    help="View or edit customer data",
                    width="small"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Add a row selection mechanism for editing/viewing
        st.markdown("### View or Edit Customer Data")
        customer_for_edit = st.selectbox(
            "Select a customer to view or edit:",
            range(len(dashboard_data)),
            format_func=lambda i: dashboard_data[i]["Company"] if i < len(dashboard_data) else ""
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 View Customer Data", key="view_customer_data", use_container_width=True):
                if customer_for_edit is not None and customer_for_edit < len(dashboard_data):
                    selected_customer_id = dashboard_data[customer_for_edit]["_id"]
                    st.session_state.view_customer_id = selected_customer_id
                    st.session_state.customer_view_mode = "view"
                    st.session_state.page = "customer_view"
                    st.rerun()
        
        with col2:
            if st.button("📝 Edit Customer Data", key="edit_customer_data", use_container_width=True):
                if customer_for_edit is not None and customer_for_edit < len(dashboard_data):
                    selected_customer_id = dashboard_data[customer_for_edit]["_id"]
                    st.session_state.view_customer_id = selected_customer_id
                    st.session_state.customer_view_mode = "edit"
                    st.session_state.page = "customer_view"
                    st.rerun()
        
        # Add timeline visualization for selected customer
        if dashboard_data:
            st.subheader("Service Workflow Timeline View")
            selected_customer_index = st.selectbox(
                "Select a customer to view their service timeline:",
                range(len(dashboard_data)),
                format_func=lambda i: dashboard_data[i]["Company"] if i < len(dashboard_data) else ""
            )
            
            if selected_customer_index is not None and selected_customer_index < len(dashboard_data):
                selected_customer_id = dashboard_data[selected_customer_index]["_id"]
                selected_customer = customers.find_one({"_id": ObjectId(selected_customer_id)})
                
                if selected_customer:
                    # Display service timeline
                    # Using datetime module that's already imported at the top of the file
                    
                    # Get all dates from database
                    timeline_data = {
                        "CRM Entry": selected_customer.get("created_at", datetime.datetime.now()),
                    }
                    
                    # Get vendor registration date (need to query historical data)
                    # For now just use a placeholder
                    if selected_customer['status'].get('vendor_registered', False):
                        timeline_data["Vendor Registration"] = selected_customer.get("vendor_registered_at", timeline_data["CRM Entry"])
                    
                    # Get MRN date from mrns collection
                    from database.connection import mrns
                    mrn_record = mrns.find_one({"customer_id": selected_customer_id, "is_draft": {"$ne": True}})
                    if mrn_record:
                        timeline_data["MRN Creation"] = mrn_record.get("created_at", timeline_data["CRM Entry"])
                    
                    # Get Service Report date
                    from database.connection import service_reports
                    sr_record = service_reports.find_one({"customer_id": selected_customer_id})
                    if sr_record:
                        timeline_data["Service Report"] = sr_record.get("created_at", timeline_data["CRM Entry"])
                    
                    # Telecontroller date
                    if selected_customer['status'].get('telecontroller_done', False):
                        timeline_data["Telecontroller"] = selected_customer.get("telecontroller_done_at", timeline_data["CRM Entry"])
                    
                    # Create a timeline visualization
                    import pandas as pd
                    
                    # Convert to list of dicts for display
                    timeline_list = []
                    for stage, date in timeline_data.items():
                        # Convert date to string for display
                        if isinstance(date, datetime.datetime):
                            date_str = date.strftime("%Y-%m-%d %H:%M")
                        else:
                            date_str = str(date)
                        
                        timeline_list.append({
                            "Stage": stage,
                            "Date": date_str
                        })
                    
                    # Create a DataFrame
                    timeline_df = pd.DataFrame(timeline_list)
                    
                    # Display as table with custom formatting
                    st.table(timeline_df)
                    
                    # Add a service completion time calculation
                    if len(timeline_data) > 1 and "Telecontroller" in timeline_data:
                        start_date = timeline_data["CRM Entry"]
                        end_date = timeline_data["Telecontroller"]
                        
                        if isinstance(start_date, datetime.datetime) and isinstance(end_date, datetime.datetime):
                            service_time = end_date - start_date
                            days = service_time.days
                            hours = service_time.seconds // 3600
                            
                            st.success(f"Total service completion time: {days} days and {hours} hours")
        
        # Below the dataframe, add buttons for each customer
        st.markdown("### Continue Workflow")
        st.markdown("Select a customer to continue their workflow:")
        
        # Create a selectbox with customer names
        customer_options = [f"{cust['Company']} ({cust['Completion']} complete)" for cust in dashboard_data]
        customer_index = st.selectbox("Select customer:", 
                                       options=range(len(customer_options)),
                                       format_func=lambda i: customer_options[i] if i < len(customer_options) else "")
        
        if st.button("Continue Selected Workflow", use_container_width=True):
            if customer_index is not None and customer_index < len(dashboard_data):
                selected_customer_id = dashboard_data[customer_index]["_id"]
                
                # Set customer ID in session state
                st.session_state.customer_id = selected_customer_id
                
                # Get customer data
                customer = customers.find_one({"_id": ObjectId(selected_customer_id)})
                
                # Determine which page to navigate to based on workflow progress
                if not customer['status'].get('vendor_registered', False):
                    navigate_to_page("vendor_registration")
                elif not customer['status'].get('mrn_created', False):
                    navigate_to_page("mrn_creation")
                elif not customer['status'].get('service_report_created', False):
                    navigate_to_page("service_report")
                elif not customer['status'].get('telecontroller_done', False):
                    navigate_to_page("telecontroller")
                else:
                    # If all steps are complete, just stay on the dashboard
                    st.success(f"Workflow for {customer.get('name', 'Unknown')} is already complete!")
                    
                # Get MRN code if exists
                if customer.get('mrn_code'):
                    st.session_state.mrn_code = customer.get('mrn_code')
                    
                # Get SR code if exists
                if customer.get('sr_code'):
                    st.session_state.sr_code = customer.get('sr_code')
        
    else:
        st.info("No records found matching the filter criteria.")
    
    # Create new service visit button with better styling
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create a card-like container for the button
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px;">
        <h3>Start a New Service Workflow</h3>
        <p>Click below to begin a new customer service workflow</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        if st.button("✨ Create New Service Visit", key="create_new_visit", use_container_width=True):
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
            
            # Reset any other form input values that might be in session state
            if "company_name" in st.session_state:
                del st.session_state.company_name
            if "contact_name" in st.session_state:
                del st.session_state.contact_name
            if "contact_phone" in st.session_state:
                del st.session_state.contact_phone
            if "machine_count" in st.session_state:
                del st.session_state.machine_count
            
            # Show a success message
            st.toast("New customer record created. Please fill in the details.", icon="✅")
            
            # Navigate to the CRM entry page
            navigate_to_page("crm_entry")
            st.rerun()
              
# Render other pages based on the current page in session state
elif st.session_state.page == "crm_entry":
    crm_entry.render()
elif st.session_state.page == "vendor_registration":
    vendor_registration.render()
elif st.session_state.page == "mrn_creation":
    mrn_creation.render()
elif st.session_state.page == "service_report":
    service_report.render()
elif st.session_state.page == "telecontroller":
    telecontroller.render()
elif st.session_state.page == "customer_view":
    customer_view.render()
