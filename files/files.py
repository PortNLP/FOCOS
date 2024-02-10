import shutil

def delete_files_and_directories(directory):
    try:
        shutil.rmtree(directory)
        print(f"Deleted: {directory}")
    except Exception as e:
        print(f"Error deleting {directory}: {e}")