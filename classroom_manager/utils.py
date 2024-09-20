import os

def create_submission_file(name, submission_id, file_bytes):
    submission_dir = os.getenv('SUBMISSION_DIR')
    if submission_dir:
        submission_dir = os.path.join(submission_dir, str(submission_id))
        os.makedirs(submission_dir, exist_ok=True)
        file_path = os.path.join(submission_dir, name)
        with open(file_path, 'wb') as file:
            file.write(file_bytes)
        return file_path
    else:
        raise ValueError('SUBMISSION_DIR environment variable is not set')

def create_task_file(name, task_id, file_bytes):
    task_dir = os.getenv('CLASSROOM_TASK_FILE_DIR')
    if task_dir:
        task_dir = os.path.join(task_dir, str(task_id))
        os.makedirs(task_dir, exist_ok=True)
        file_path = os.path.join(task_dir, name)
        with open(file_path, 'wb') as file:
            file.write(file_bytes)
        return file_path
    else:
        raise ValueError('CLASSROOM_TASK_FILE_DIR environment variable is not set')

def get_file_path_by_name_and_id(name, id, directory):
    file_dir = os.path.join(directory, str(id))
    file_path = os.path.join(file_dir, name)
    return file_path

def delete_file_by_name_and_id(name, id, directory):
    file_path = get_file_path_by_name_and_id(name, id, directory)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    else:
        return False
