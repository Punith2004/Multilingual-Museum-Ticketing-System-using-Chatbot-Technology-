from flask import Flask, render_template, request, jsonify, send_file
import datetime
import random
import string
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# Simulated museum data
MUSEUMS = {
    "National Art Gallery": {"times": ["10:00 AM", "1:00 PM", "3:00 PM"], "price_per_ticket": 15},
    "Science Museum": {"times": ["9:00 AM", "12:00 PM", "2:00 PM"], "price_per_ticket": 20},
    "History Museum": {"times": ["11:00 AM", "1:30 PM", "4:00 PM"], "price_per_ticket": 12}
}

def generate_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def validate_date(date_str):
    try:
        visit_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        if visit_date < datetime.datetime.now():
            return False, "The date must be in the future!"
        return True, visit_date
    except ValueError:
        return False, "Invalid date format."

def validate_time(time_str, available_times):
    return time_str in available_times, "Invalid or unavailable time."

def validate_tickets(ticket_str):
    try:
        num = int(ticket_str)
        return num > 0, "Number of tickets must be greater than 0."
    except ValueError:
        return False, "Please enter a valid number."

def generate_pdf_ticket(booking):
    """Generate a PDF ticket with booking details."""
    # Use a path in the static folder or a temporary directory
    pdf_folder = os.path.join(app.static_folder, 'tickets')
    os.makedirs(pdf_folder, exist_ok=True)  # Create tickets folder if it doesn’t exist
    pdf_file = os.path.join(pdf_folder, f"ticket_{booking['reference']}.pdf")
    print(f"Generating PDF at: {pdf_file}")  # Debug: Print the file path

    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("Museum Ticket", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Booking details
    data = [
        ["Museum", booking['museum']],
        ["Date", booking['date']],
        ["Time", booking['time']],
        ["Number of Tickets", str(booking['tickets'])],
        ["Name", booking['name']],
        ["Phone Number", booking['phone']],
        ["Reference Number", booking['reference']],
        ["Total Cost", f"${MUSEUMS[booking['museum']]['price_per_ticket'] * booking['tickets']}"],
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Build the PDF
    doc.build(elements)
    return pdf_file

@app.route('/')
def index():
    return render_template('index.html', museums=MUSEUMS.keys())

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '').strip()
    step = data.get('step', 0)
    booking = data.get('booking', {})

    if step == 0:
        response = "Hi! I’m your Museum Ticket Assistant. Which museum would you like to visit?"
        return jsonify({"response": response, "step": 1})

    elif step == 1:  # Museum name
        if user_input in MUSEUMS:
            booking['museum'] = user_input
            response = f"Great! When would you like to visit {user_input}? (Enter date as YYYY-MM-DD)"
            return jsonify({"response": response, "step": 2, "booking": booking})
        else:
            response = f"Sorry, that museum isn’t available. Choose from: {', '.join(MUSEUMS.keys())}"
            return jsonify({"response": response, "step": 1})

    elif step == 2:  # Date
        is_valid, result = validate_date(user_input)
        if is_valid:
            booking['date'] = user_input
            times = MUSEUMS[booking['museum']]['times']
            response = f"Available times: {', '.join(times)}. What time would you like?"
            return jsonify({"response": response, "step": 3, "booking": booking})
        else:
            response = result
            return jsonify({"response": response, "step": 2})

    elif step == 3:  # Time
        times = MUSEUMS[booking['museum']]['times']
        is_valid, result = validate_time(user_input, times)
        if is_valid:
            booking['time'] = user_input
            response = "How many tickets would you like to book?"
            return jsonify({"response": response, "step": 4, "booking": booking})
        else:
            response = f"{result} Available times: {', '.join(times)}"
            return jsonify({"response": response, "step": 3})

    elif step == 4:  # Number of tickets
        is_valid, result = validate_tickets(user_input)
        if is_valid:
            booking['tickets'] = int(user_input)
            response = "What’s your name?"
            return jsonify({"response": response, "step": 5, "booking": booking})
        else:
            response = result
            return jsonify({"response": response, "step": 4})

    elif step == 5:  # Name
        if user_input:
            booking['name'] = user_input
            response = "What’s your phone number? (e.g., +12345678901 or 123-456-7890)"
            return jsonify({"response": response, "step": 6, "booking": booking})
        else:
            response = "Name cannot be empty."
            return jsonify({"response": response, "step": 5})

    elif step == 6:  # Phone number
        if user_input.replace('+', '').replace('-', '').isdigit() and len(user_input.replace('+', '').replace('-', '')) >= 10:
            booking['phone'] = user_input
            ticket_price = MUSEUMS[booking['museum']]['price_per_ticket']
            total_cost = booking['tickets'] * ticket_price
            summary = (
                f"Here’s your booking:\n"
                f"Museum: {booking['museum']}\n"
                f"Date: {booking['date']}\n"
                f"Time: {booking['time']}\n"
                f"Tickets: {booking['tickets']}\n"
                f"Total Cost: ${total_cost}\n"
                f"Name: {booking['name']}\n"
                f"Phone Number: {booking['phone']}\n"
                f"Confirm? (Yes/No)"
            )
            response = summary
            return jsonify({"response": response, "step": 7, "booking": booking})
        else:
            response = "Please enter a valid phone number."
            return jsonify({"response": response, "step": 6})

    elif step == 7:  # Confirmation
        if user_input.lower() == "yes":
            booking_reference = generate_reference()
            booking['reference'] = booking_reference
            # Generate PDF ticket
            try:
                pdf_path = generate_pdf_ticket(booking)
                print(f"PDF generated successfully at: {pdf_path}")  # Debug: Confirm PDF generation
                response = f"Booking confirmed! Your reference number is {booking_reference}. An SMS with your ticket has been sent to {booking['phone']}. Click 'Download Ticket' to get your ticket in PDF."
                return jsonify({
                    "response": response, 
                    "step": 0, 
                    "booking": {},
                    "pdf_path": os.path.basename(pdf_path)  # Send only the filename for simplicity
                })
            except Exception as e:
                print(f"Error generating PDF: {e}")
                response = f"Booking confirmed, but there was an error generating your ticket PDF. Reference number: {booking_reference}. Contact support."
                return jsonify({"response": response, "step": 0, "booking": {}})
        elif user_input.lower() == "no":
            response = "Booking canceled. Start over?"
            return jsonify({"response": response, "step": 0, "booking": {}})
        else:
            response = "Please enter 'Yes' or 'No'."
            return jsonify({"response": response, "step": 7, "booking": booking})

@app.route('/download_ticket/<path:pdf_path>')
def download_ticket(pdf_path):
    """Serve the PDF file for download."""
    full_path = os.path.join(app.static_folder, 'tickets', pdf_path)
    print(f"Attempting to send file: {full_path}")  # Debug: Confirm file path
    if os.path.exists(full_path):
        return send_file(full_path, as_attachment=True)
    else:
        return jsonify({"error": "Ticket not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)