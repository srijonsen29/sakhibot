from agents.doc_drafter import generate_fir_complaint_letter
fields = {
    'complainant_name':     'Priya Sharma',
    'complainant_age':      '28',
    'complainant_address':  '123 MG Road, Dharavi, Mumbai 400017',
    'complainant_phone':    '9876543210',
    'guardian_name':        'Ramesh Sharma',
    'police_station':       'Dharavi',
    'district':             'Mumbai',
    'incident_date':        '15 May 2026',
    'incident_time':        '10:30 PM',
    'incident_place':       'Our home at 123 MG Road',
    'accused_name':         'Ramesh Sharma',
    'accused_relationship': 'Husband',
    'incident_description': 'My husband Ramesh Sharma physically assaulted me, causing injuries to my face and arms. He also verbally abused me and threatened to throw me out of the house.',
}
pdf = generate_fir_complaint_letter(fields)
with open('test_complaint_letter.pdf', 'wb') as f:
    f.write(pdf)
print('PDF generated — open test_complaint_letter.pdf')
