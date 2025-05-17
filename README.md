# Pofisian Service Workflow Application

A comprehensive service management application built with Streamlit to streamline the process of handling service visits, from customer registration to service completion.

## Features

- **Modern User Interface**: Clean, responsive layout with sidebar navigation
- **Multi-step Workflow Process**:
  - Customer registration
  - Vendor verification
  - MRN (Material Return Number) generation
  - Service report documentation
  - Telecontroller completion
- **Real-time Progress Tracking**: Visual step indicators and progress bars
- **Autosave Functionality**: Automatically saves data after 2 seconds of user inactivity
- **Dashboard Overview**: Comprehensive view of all clients and service statuses
- **MongoDB Integration**: Persistent data storage with GridFS for file uploads
- **Modular Structure**: Well-organized code base with separate components

## Installation Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pofisian-service-workflow.git
   cd pofisian-service-workflow
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up MongoDB:
   - Install MongoDB locally or use MongoDB Atlas for cloud hosting
   - Set the connection string as an environment variable:
     ```bash
     export MONGO_CONNECTION_STRING="mongodb://localhost:27017/"
     ```
   - Or configure it directly in the application

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Application Structure

- **app.py**: Main application entry point and home/dashboard page
- **database/**: MongoDB connection and data access
- **pages/**: Individual workflow step pages
- **utils/**: Helper functions and shared utilities
- **.streamlit/**: Configuration and styling

## Workflow Process

1. **Customer Registration**: Enter basic client information
2. **Vendor Registration**: Confirm vendor is registered in the system
3. **MRN Creation**: Generate a unique Material Return Number
4. **Service Report**: Document service details, issues, and actions
5. **Telecontroller**: Upload final documentation

## Screenshots

(Screenshots will be added here)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

bashexport MONGO_CONNECTION_STRING="mongodb://username:password@host:port/dbname"
Alternatively, you can create a .env file with:
MONGO_CONNECTION_STRING="mongodb://username:password@host:port/dbname"

Run the application:

bashstreamlit run app.py
Application Workflow
The application follows a 6-step workflow:

CRM Entry: Capture basic customer information
Vendor Registration: Mark if the vendor is registered
MRN Creation: Generate a unique Material Request Number
Service Report: Document service details and actions
Telecontroller: Upload telecontroller PDF or access external site
Dashboard: Overview of all service workflows and their completion status

Data Model
The application uses the following MongoDB collections:

customers: Main customer records with workflow status
mrns: Material Request Number records
service_reports: Service report details
fs.files and fs.chunks: GridFS collections for file storage

Development Notes

The autosave functionality uses threading to save data after 2 seconds of inactivity
Session state manages the page flow and current customer context
Sequential code generation ensures unique identifiers for MRNs and SRs

Future Enhancements

User authentication and authorization
Email notifications
PDF generation for reports
Enhanced dashboard filtering and analytics



Modular Structure:

Reorganized the code into multiple files using a clear directory structure
Created separate modules for database, pages, and utilities
User Interface Improvements:

Added a welcome screen for Pofisian
Implemented a sidebar with navigation and progress tracking
Created a dashboard showing client statistics
Added workflow progress indicators
Improved button styling and layout
Functionality Enhancements:

Added workflow progress bars
Created interactive client selection in the dashboard
Implemented searching and sorting in the dashboard
Added visualization charts for better data representation
Enhanced navigation between workflow steps
User Experience:

Added informative cards and instructions
Improved the visual workflow progress indicators
Added current date display
Created a user profile display in the sidebar
Documentation:

Updated the README.md with comprehensive information
Added code comments throughout the application
These changes have transformed the original single-file application into a modular, well-organized, and user-friendly service workflow management system that provides Pofisian with an excellent tool for tracking and managing client service visits.


