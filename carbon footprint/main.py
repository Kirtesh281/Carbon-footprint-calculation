import matplotlib
matplotlib.use('Agg')  # Use non-interactive Agg backend

from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from io import BytesIO
import matplotlib.pyplot as plt
import os
from datetime import datetime

app = Flask(__name__)

# Function to calculate carbon footprint
def calculate_footprint(energy_kwh, distance_km, waste_kg):
    energy_emission = 0.233  # Emission factor for electricity
    emission_energy = energy_kwh * energy_emission

    emission_transport = 0.192  # Emission factor for transportation
    emission_transport = distance_km * emission_transport

    emission_waste = 0.1  # Emission factor for waste
    emission_waste = waste_kg * emission_waste

    total_emission = emission_energy + emission_transport + emission_waste

    return emission_energy, emission_transport, emission_waste, total_emission

# Function to generate the carbon emission distribution chart
def generate_emission_chart(energy, transport, waste):
    categories = ['Energy', 'Transport', 'Waste']
    values = [energy, transport, waste]

    # Create a pie chart
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(values, labels=categories, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
    ax.set_title("Carbon Emission Distribution")

    # Save the chart as an image (PNG)
    chart_path = 'carbon_emission_chart.png'
    plt.savefig(chart_path, format='png')
    plt.close()
    return chart_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            energy_kwh = float(request.form["electricity"])
            distance_km = float(request.form["distance"])
            waste_kg = float(request.form["waste"])

            emission_energy, emission_transport, emission_waste, total_emission = calculate_footprint(energy_kwh, distance_km, waste_kg)

            result = {
                "energy": emission_energy,
                "transport": emission_transport,
                "waste": emission_waste,
                "total": total_emission
            }

            generated_date = datetime.now().strftime("%d %B %Y, %I:%M %p")

            return render_template("result.html", result=result, generated_date=generated_date)
        except ValueError:
            return "Invalid input, please enter valid numbers."

    return render_template("index.html")

@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    energy = request.args.get('energy')
    transport = request.args.get('transport')
    waste = request.args.get('waste')
    total = request.args.get('total')

    # Validate parameters
    if not all([energy, transport, waste, total]):
        return "Missing parameters for PDF generation", 400

    try:
        energy = float(energy)
        transport = float(transport)
        waste = float(waste)
        total = float(total)
    except ValueError:
        return "Invalid parameter values", 400

    # Generate the carbon emission distribution chart
    chart_path = generate_emission_chart(energy, transport, waste)

    # Create PDF buffer
    buffer = BytesIO()
    c = canvas.Canvas(buffer)

    # Add Title and Date
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "Carbon Footprint Report")
    c.setFont("Helvetica", 10)
    c.drawString(450, 780, f"Date: {datetime.now().strftime('%d %B %Y')}")

    # Add Emission Data
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Summary of Emissions:")
    c.setFont("Helvetica", 10)
    c.drawString(100, 725, f"Energy Emissions: {energy:.2f} kg CO2")
    c.drawString(100, 705, f"Transportation Emissions: {transport:.2f} kg CO2")
    c.drawString(100, 685, f"Waste Emissions: {waste:.2f} kg CO2")
    c.drawString(100, 665, f"Total Carbon Footprint: {total:.2f} kg CO2")

    # Draw a line for separation
    c.line(100, 650, 500, 650)

    # Add Chart Image
    c.drawString(100, 630, "Carbon Emission Distribution:")
    c.drawImage(chart_path, 100, 300, width=400, height=300)

    # Save PDF
    c.showPage()
    c.save()

    # Clean up and return PDF
    os.remove(chart_path)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="carbon_footprint_report.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
