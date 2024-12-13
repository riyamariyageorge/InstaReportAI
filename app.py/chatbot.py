import random

def chatbot():
    print("Hello! I'm your Event Assistant Chatbot. Let's gather more details about your event.")

    # Collecting basic event details
    event_name = input("What is the name of your event? ")
    event_type = input("What type of event is this (e.g., workshop, seminar, conference)? ")

    # Asking specific questions based on the event type
    if event_type.lower() in ["workshop", "seminar"]:
        topic = input("What is the main topic of the event? ")
        audience = input("Who is the target audience (e.g., students, professionals)? ")
    elif event_type.lower() == "conference":
        keynote_speaker = input("Who is the keynote speaker? ")
        session_count = input("How many sessions will the conference have? ")
    elif event_type.lower() == "cultural fest":
        main_performance = input("What is the main performance or highlight of the fest? ")
        expected_attendance = input("What is the expected number of attendees? ")
    else:
        print("Great! Let's continue with the general details.")

    # Common questions for all events
    start_time = input("What time does the event start? ")
    end_time = input("What time does the event end? ")
    venue = input("Where is the event taking place? ")

    # Confirming the details collected
    print("\nThank you! Here is the summary of the event details you provided:")
    print(f"Event Name: {event_name}")
    print(f"Event Type: {event_type}")

    if event_type.lower() in ["workshop", "seminar"]:
        print(f"Topic: {topic}")
        print(f"Target Audience: {audience}")
    elif event_type.lower() == "conference":
        print(f"Keynote Speaker: {keynote_speaker}")
        print(f"Number of Sessions: {session_count}")
    elif event_type.lower() == "cultural fest":
        print(f"Main Performance: {main_performance}")
        print(f"Expected Attendance: {expected_attendance}")

    print(f"Start Time: {start_time}")
    print(f"End Time: {end_time}")
    print(f"Venue: {venue}")

    print("\nIf any details are incorrect, please re-run the chatbot to update them.")

# Run the chatbot
if _name_ == "_main_":
    chatbot()