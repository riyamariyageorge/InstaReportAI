from fpdf import FPDF

class PDFGenerator(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Event Report", align="C", ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_event_report(event_data, output_path):
    pdf = PDFGenerator()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add event details
    pdf.cell(0, 10, f"Event Title: {event_data['event_name']}", ln=True)
    pdf.cell(0, 10, f"Date: {event_data['date']}", ln=True)
    pdf.cell(0, 10, f"Time: {event_data['time']}", ln=True)
    pdf.cell(0, 10, f"Venue: {event_data['venue']}", ln=True)
    pdf.ln(10)
    
    # Add description
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Generated Description:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, event_data.get('description', "No description available."))

    # Save the PDF
    pdf.output(output_path)




'''
def generate_event_report(event_details, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Event Report", ln=True, align='C')
    pdf.ln(10)  # Add line break

    for key, value in event_details.items():
        formatted_key = key.replace('_', ' ').title()
        pdf.multi_cell(0, 10, txt=f"{formatted_key}: {value if value else 'N/A'}")

    pdf.output(output_path)

    '''