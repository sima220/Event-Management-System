import streamlit as st
import pandas as pd
from datetime import date
from backend_event_mgmt import (
    get_or_create_user, create_event, create_ticket, register_attendee,
    get_user_events, get_event_tickets, get_event_insights, 
    get_event_tickets_for_registration, get_attendees_by_ticket_type
)

# Set page configuration
st.set_page_config(
    page_title="Event Management System Sima 30190",
    page_icon="🎉",
    layout="wide",
)

st.title("🎉 Event Management System")
st.title("Sima Rani Patra (PGDM 30190)")
st.markdown("Easily create, manage, and analyze your events.")

# --- Session State for User Management ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'selected_event_name' not in st.session_state:
    st.session_state['selected_event_name'] = None

# User login/creation section
if st.session_state['user_id'] is None:
    st.subheader("Login / Create Profile")
    with st.form("user_profile_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        organization = st.text_input("Organization")
        submitted = st.form_submit_button("Submit")
        if submitted:
            user_id = get_or_create_user(name, email, organization)
            if user_id:
                st.session_state['user_id'] = user_id
                st.success("Profile created/logged in successfully!")
                st.rerun()
            else:
                st.error("Could not create/login user. Please check your email or database connection.")
else:
    # --- Main Application Layout ---
    st.sidebar.header("Navigation")
    app_mode = st.sidebar.radio("Go to", ["Dashboard", "Create New Event"])

    if app_mode == "Dashboard":
        st.subheader("Dashboard")
        events_df = get_user_events(st.session_state['user_id'])
        
        if not events_df.empty:
            st.write("### Your Events")
            
            event_names = events_df['event_name'].tolist()
            
            selected_event_name = st.selectbox(
                "Select an Event", 
                event_names, 
                index=event_names.index(st.session_state['selected_event_name']) if st.session_state['selected_event_name'] in event_names else 0
            )

            if selected_event_name != st.session_state['selected_event_name']:
                st.session_state['selected_event_name'] = selected_event_name
                st.rerun()

            selected_event_id = events_df[events_df['event_name'] == selected_event_name]['event_id'].iloc[0]

            st.markdown("---")
            
            # --- Business Insights Section ---
            st.subheader("📊 Event Insights")
            insights = get_event_insights(selected_event_id)
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                st.metric("Total Attendees", insights.get('total_attendees', 0))
            with col2:
                st.metric("Total Revenue", f"${insights.get('total_revenue', 0) if insights.get('total_revenue') is not None else 0:.2f}")
            with col3:
                st.metric("Tickets Available", insights.get('total_tickets_available', 0) if insights.get('total_tickets_available') is not None else 0)
            with col4:
                st.metric("Min Ticket Price", f"${insights.get('min_ticket_price', 0) if insights.get('min_ticket_price') is not None else 0:.2f}")
            with col5:
                st.metric("Max Ticket Price", f"${insights.get('max_ticket_price', 0) if insights.get('max_ticket_price') is not None else 0:.2f}")
            with col6:
                st.metric("Avg Ticket Price", f"${insights.get('avg_ticket_price', 0) if insights.get('avg_ticket_price') is not None else 0:.2f}")

            st.markdown("---")

            # --- Attendee and Ticket Management ---
            st.subheader("Attendees & Tickets")

            col_a, col_b = st.columns(2)
            with col_a:
                st.write("### Event Tickets")
                tickets_df = get_event_tickets(selected_event_id)
                if not tickets_df.empty:
                    st.dataframe(tickets_df, use_container_width=True)
                else:
                    st.info("No tickets created for this event.")
            
            with col_b:
                st.write("### Register Attendee")
                with st.form("attendee_form"):
                    tickets_for_dropdown = get_event_tickets_for_registration(selected_event_id)
                    if tickets_for_dropdown:
                        ticket_options = {f"{t[1]} - ${t[2]:.2f}": t[0] for t in tickets_for_dropdown}
                        selected_ticket_label = st.selectbox("Select Ticket Type", list(ticket_options.keys()))
                        ticket_id_to_register = ticket_options[selected_ticket_label]
                        
                        attendee_name = st.text_input("Attendee Name")
                        attendee_email = st.text_input("Attendee Email")
                        
                        reg_submitted = st.form_submit_button("Register")
                        if reg_submitted:
                            if attendee_name and attendee_email:
                                if register_attendee(ticket_id_to_register, attendee_name, attendee_email):
                                    st.success("Attendee registered successfully! (Confirmation email not sent in this demo)")
                                    st.rerun()
                                else:
                                    st.error("Registration failed. Please try again.")
                            else:
                                st.warning("Please fill in attendee name and email.")
                    else:
                        st.warning("Please create ticket types for this event first.")

            st.markdown("---")

            # --- Attendee List with Filtering ---
            st.subheader("Registered Attendees")
            tickets_for_dropdown = get_event_tickets_for_registration(selected_event_id)
            if tickets_for_dropdown:
                ticket_types = ["All"] + [t[1] for t in tickets_for_dropdown]
                selected_ticket_type = st.selectbox("Filter Attendees by Ticket Type", ticket_types)

                if selected_ticket_type == "All":
                    all_attendees_df = pd.DataFrame()
                    for ticket_info in tickets_for_dropdown:
                        ticket_type = ticket_info[1] # Correctly get the ticket type from the tuple
                        df = get_attendees_by_ticket_type(selected_event_id, ticket_type)
                        all_attendees_df = pd.concat([all_attendees_df, df], ignore_index=True)
                    if not all_attendees_df.empty:
                        st.dataframe(all_attendees_df, use_container_width=True)
                    else:
                        st.info("No attendees to display. Register someone first!")
                else:
                    attendees_df = get_attendees_by_ticket_type(selected_event_id, selected_ticket_type)
                    if not attendees_df.empty:
                        st.dataframe(attendees_df, use_container_width=True)
                    else:
                        st.info(f"No attendees registered for '{selected_ticket_type}' tickets.")
            else:
                st.info("No attendees to display. Register someone first!")

        else:
            st.info("You haven't created any events yet. Please create one on the 'Create New Event' page.")

    elif app_mode == "Create New Event":
        st.subheader("Create a New Event")
        with st.form("event_creation_form"):
            event_name = st.text_input("Event Name")
            event_date = st.date_input("Event Date", date.today())
            event_time = st.time_input("Event Time")
            location = st.text_input("Location")
            description = st.text_area("Description")
            
            st.markdown("---")
            st.write("#### Add Ticket Types")
            ticket_types_data = []
            num_tickets = st.number_input("Number of ticket types to add:", min_value=1, step=1, value=1)
            for i in range(int(num_tickets)):
                st.markdown(f"**Ticket Type {i+1}**")
                ticket_type = st.text_input(f"Name (e.g., VIP, General)", key=f"ticket_type_{i}")
                price = st.number_input(f"Price ($)", min_value=0.0, format="%.2f", key=f"price_{i}")
                quantity = st.number_input(f"Quantity Available", min_value=0, step=1, key=f"quantity_{i}")
                ticket_types_data.append({'ticket_type': ticket_type, 'price': price, 'quantity': quantity})
            
            submitted = st.form_submit_button("Create Event & Tickets")

            if submitted:
                if event_name and location:
                    event_created = create_event(st.session_state['user_id'], event_name, event_date, event_time, location, description)
                    if event_created:
                        st.success("Event created successfully!")
                        events_df = get_user_events(st.session_state['user_id'])
                        new_event_id = events_df[events_df['event_name'] == event_name]['event_id'].iloc[0]
                        st.session_state['selected_event_name'] = event_name
                        
                        all_tickets_created = True
                        for ticket in ticket_types_data:
                            if ticket['ticket_type'] and ticket['quantity']:
                                if not create_ticket(new_event_id, ticket['ticket_type'], ticket['price'], ticket['quantity']):
                                    all_tickets_created = False
                        
                        if all_tickets_created:
                            st.success("All ticket types created successfully!")
                        else:
                            st.error("Failed to create all ticket types.")
                        
                        st.rerun()
                    else:
                        st.error("Failed to create event.")
                else:
                    st.warning("Please fill in event name and location.")
