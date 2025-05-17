import streamlit as st
from bson.objectid import ObjectId
from utils.helpers import navigate_to_page, create_workflow_steps_indicator
from database.connection import customers

def render():
    # Display workflow steps indicator
    create_workflow_steps_indicator("vendor_registration")
    
    st.header("Vendor Registration")
    
    # Instructions in a card
    st.markdown("""
    <div class="css-card">
        <h3>Vendor Confirmation</h3>
        <p>Confirm that the vendor is registered in the system before proceeding.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            
            # Better button styling
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous", key="prev_to_crm", use_container_width=True):
                    navigate_to_page("crm_entry")
                    st.rerun()
            with col2:
                if st.button("Next Step →", key="next_to_mrn", disabled=next_disabled, use_container_width=True):
                    navigate_to_page("mrn_creation")
                    st.rerun()
        else:
            st.error("Customer data not found. Please go back and retry.")
            if st.button("Back to CRM Entry"):
                navigate_to_page("crm_entry")
                st.rerun()
    else:
        st.error("No customer selected. Please start from the beginning.")
        if st.button("Back to CRM Entry"):
            navigate_to_page("crm_entry")
            st.rerun()
