import csv

def transform_student_csv(input_path, output_path):
    """Transform student CSV from school format to bulk upload format"""
    with open(input_path, 'r', encoding='utf-8-sig') as infile, \
         open(output_path, 'w', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile, delimiter='\t')
        
        # Write header row
        writer.writerow(['First Name', 'Last Name', 'Email', 'Password'])
        
        # Process each student
        for row in reader:
            first_name = row['First Name']
            last_name = row['Last Name']
            email = f"{first_name.lower()}.{last_name.lower()}@mathfluency.com"
            password = f"{first_name[0].upper()}{last_name.lower()}123!"
            
            writer.writerow([first_name, last_name, email, password])

if __name__ == '__main__':
    input_csv = '/Users/kennethweiss/Downloads/Per2.CSV'
    output_csv = '/Users/kennethweiss/Downloads/Per2_UploadReady.tsv'
    transform_student_csv(input_csv, output_csv)
    print(f"Transformed file saved to {output_csv}")
