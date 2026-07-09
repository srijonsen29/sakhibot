# test_doc_generator.py
from datetime import date
from agents.doc_drafter import generate_dv_application, generate_posh_complaint

def test_dv_pdf():
    fields = {
        "complainant_name": "Anita Roy",
        "complainant_age": "32",
        "complainant_address": "45 Park Street, Kolkata",
        "complainant_phone": "9123456780",
        "accused_name": "Rajesh Roy",
        "accused_address": "45 Park Street, Kolkata",
        "accused_relationship": "Husband",
        "incident_date": "20 May 2026",
        "incident_description": "He hit me and threatened me over a financial dispute.",
        "relief_sought": "Protection Order, Residence Order, Monetary Relief, Compensation",
        "court_district": "Kolkata District Court",
    }
    pdf_bytes = generate_dv_application(fields)
    with open("test_dv_complaint.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("DV complaint PDF generated ✓")

def test_posh_pdf():
    fields = {
        "complainant_name": "Meera Singh",
        "complainant_designation": "Software Engineer",
        "complainant_department": "IT Department",
        "complainant_phone": "9876543210",
        "organization_name": "TechCorp Pvt Ltd",
        "accused_name": "Arun Kumar",
        "accused_designation": "Team Lead",
        "incident_date": "15 May 2026",
        "incident_place": "Office premises",
        "incident_description": "He made inappropriate comments and advances during a meeting.",
        "witnesses": "Colleague: Ritu Sharma, Email: ritu@techcorp.com",
        "evidence": "Screenshots of chat messages attached",
    }
    pdf_bytes = generate_posh_complaint(fields)
    with open("test_posh_complaint.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("POSH complaint PDF generated ✓")

if __name__ == "__main__":
    test_dv_pdf()
    test_posh_pdf()
