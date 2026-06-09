import os
import pandas as pd

def export_to_excel(invoice_list):

    os.makedirs("output", exist_ok=True)

    df = pd.DataFrame(invoice_list)

    df.to_excel(
        "output/invoices.xlsx",
        index=False
    )

    print("Excel saved to output/invoices.xlsx")