import io
import gzip

def process_dataframe_to_gzip(df):
    """
    Converts a Pandas DataFrame to an in-memory GZIP buffer.
    """
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=gzip_buffer, mode="wb") as gz_file:
        gz_file.write(csv_buffer.getvalue().encode("utf-8"))
    gzip_buffer.seek(0)

    print("Data successfully compressed in-memory.")
    return gzip_buffer
