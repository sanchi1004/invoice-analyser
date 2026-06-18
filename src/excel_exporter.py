import os
import pandas as pd
from openpyxl import load_workbook


def export_to_excel(invoice_list):

    os.makedirs("output", exist_ok=True)

    columns = [
        "Invoice Date",
        "Invoice Number",
        "Invoice Total",
        "Billing Address",
        "Due Date",
        "Name",
        "Reference No.",
        "Rate",
        "CST Value",
        "Currency",
        "Delivery_and_Billing_Period",
        "Item Total",
        "Quantity",
        "Result",
        "File Path"
    ]

    df = pd.DataFrame(invoice_list)

    existing_columns = [
        col for col in columns
        if col in df.columns
    ]

    df = df[existing_columns]

    output_file = "output/invoices.xlsx"

    df.to_excel(
        output_file,
        index=False
    )

    workbook = load_workbook(output_file)
    sheet = workbook.active

    for column in sheet.columns:

        max_length = 0

        column_letter = column[0].column_letter

        for cell in column:

            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass

        adjusted_width = min(max_length + 5, 60)

        sheet.column_dimensions[
            column_letter
        ].width = adjusted_width

    workbook.save(output_file)

    print(f"Excel saved to {output_file}")