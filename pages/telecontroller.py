import streamlit as st
from bson.objectid import ObjectId
from utils.helpers import navigate_to_page, create_workflow_steps_indicator
from database.connection import customers, fs

def render():
    # Display workflow steps indicator
    create_workflow_steps_indicator("telecontroller")
    
    st.header("Telecontroller")
    
    # Instructions in a card
    st.markdown("""
    <div class="css-card">
        <h3>Final Documentation</h3>
        <p>Complete the workflow by uploading the telecontroller PDF document.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous", key="prev_to_service_report", use_container_width=True):
                    navigate_to_page("service_report")
            with col2:
                if st.button("Complete Workflow ✓", key="complete_workflow", disabled=not telecontroller_done, use_container_width=True):
                    navigate_to_page("home")
                    st.toast("Service workflow completed successfully!", icon="🎉")
        else:
            st.error("Customer data not found. Please go back and retry.")
            if st.button("Back to Service Report"):
                navigate_to_page("service_report")
    else:
        st.error("No customer selected. Please start from the beginning.")
        if st.button("Back to CRM Entry"):
            navigate_to_page("crm_entry")
