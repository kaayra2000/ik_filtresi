import pandas as pd
from pathlib import Path
from app.services.file_writer import FileWriterFactory

def test_file_writer():
    print("Testing FileWriterFactory...")
    
    # Create test data
    df = pd.DataFrame({
        'Name': ['Ahmet', 'Mehmet', 'Ayşe'],
        'Age': [25, 30, 22],
        'City': ['Istanbul', 'Ankara', 'Izmir']
    })
    
    factory = FileWriterFactory()
    
    # Test 1: CSV Export
    csv_path = Path('test_output.csv')
    try:
        print(f"Testing CSV export to {csv_path}...")
        factory.write_file(df, csv_path)
        if csv_path.exists():
            print("CSV export successful!")
            # Verify content
            df_read = pd.read_csv(csv_path)
            if len(df_read) == 3:
                 print("CSV content verified.")
            else:
                 print("CSV content mismatch!")
        else:
            print("CSV export failed: File not found.")
    except Exception as e:
        print(f"CSV export failed with error: {e}")
    finally:
        if csv_path.exists():
            csv_path.unlink()
            print("Test CSV file cleaned up.")

    # Test 2: Excel Export
    xlsx_path = Path('test_output.xlsx')
    try:
        print(f"\nTesting Excel export to {xlsx_path}...")
        factory.write_file(df, xlsx_path)
        if xlsx_path.exists():
            print("Excel export successful!")
            # Verify content
            df_read = pd.read_excel(xlsx_path, engine='openpyxl')
            if len(df_read) == 3:
                 print("Excel content verified.")
            else:
                 print("Excel content mismatch!")
        else:
            print("Excel export failed: File not found.")
    except Exception as e:
        print(f"Excel export failed with error: {e}")
    finally:
        if xlsx_path.exists():
            xlsx_path.unlink()
            print("Test Excel file cleaned up.")

if __name__ == "__main__":
    test_file_writer()
