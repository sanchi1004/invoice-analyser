import os
import pandas as pd

def export_to_excel(invoice_list):

    os.makedirs(
        "output",
        exist_ok=True
    )

    df = pd.DataFrame(invoice_list)

    columns = [

    "Invoice Date",
    "Invoice Number",
    "Invoice Total",

    "Company Name",

    "Billing Address",

    "Due Date",

    "Name",

    "Reference No",

    "Contract Number",

    "PAN Number",

    "Supplier GST",

    "Buyer GST",

    "Rate",

    "CST Value",

    "Currency",

    "Delivery_and_Billing_Period",

    "Item Total",

    "Quantity",

    "Result",

    "File Path",

    "File Name"
    ]

    df = df.reindex(columns=columns)

    output_file = "output/invoices.xlsx"

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False
        )

        sheet = writer.sheets["Sheet1"]

        for column in sheet.columns:

            max_length = 0

            column_letter = column[0].column_letter

            for cell in column:

                try:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )
                except:
                    pass

            sheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 5,
                50
            )

    print(
        f"Excel saved to {output_file}"
    )