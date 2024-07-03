import git
import re
import os
import csv
import argparse
from datetime import datetime
import tempfile
import shutil
from collections import defaultdict

# Function to count the lines of code in a Java file, excluding comments and blank lines
def count_java_lines_of_code(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    code_lines = 0
    in_block_comment = False

    for line in lines:
        line = line.strip()

        # Check for block comments
        if in_block_comment:
            if '*/' in line:
                in_block_comment = False
            continue
        if '/*' in line:
            in_block_comment = True
            continue

        # Check for single line comments
        if line.startswith('//'):
            continue

        # Count only non-empty, non-comment lines
        if line and not line.startswith('//'):
            code_lines += 1

    return code_lines

# Function to count the lines of code in a Python file, excluding comments and blank lines
def count_python_lines_of_code(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()

    code_lines = 0
    in_block_comment = False

    for line in lines:
        line = line.strip()

        # Check for block comments
        if line.startswith('"""') or line.startswith("'''"):
            if in_block_comment:
                in_block_comment = False
            else:
                in_block_comment = True
            continue

        if in_block_comment:
            continue

        # Check for single line comments
        if line.startswith('#'):
            continue

        # Count only non-empty, non-comment lines
        if line:
            code_lines += 1

    return code_lines

# Main function to process the git repository
def process_repository(repo_path, output_csv):
    print ("Processing repository: ", repo_path)
    repo = git.Repo(repo_path)
    branch_name = repo.active_branch.name
    commits = list(repo.iter_commits(branch_name))

    # Dictionary to store aggregated data by month
    monthly_data = defaultdict(lambda: {'java': 0, 'python': 0, 'count': 0})

    # Prepare CSV file for writing
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['Month', 'Branch', 'Average Java Lines of Code', 'Average Python Lines of Code', 'Average Total Lines of Code']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for commit in commits:
            repo.git.checkout(commit)
            checkout_commit = commit.hexsha[:7]
            checkout_date = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d')
            print ("Checking out commit: ", checkout_commit, " from ", checkout_date)
            java_files = []
            python_files = []

            # Find all Java and Python files in the repository
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.java'):
                        java_files.append(os.path.join(root, file))
                    elif file.endswith('.py'):
                        python_files.append(os.path.join(root, file))

            total_java_lines_of_code = 0
            total_python_lines_of_code = 0

            # Count lines of code for each Java file
            for java_file in java_files:
                total_java_lines_of_code += count_java_lines_of_code(java_file)

            # Count lines of code for each Python file
            for python_file in python_files:
                total_python_lines_of_code += count_python_lines_of_code(python_file)

            total_lines_of_code = total_java_lines_of_code + total_python_lines_of_code
            checkin_date = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m')

            # Update monthly data
            monthly_data[checkin_date]['java'] += total_java_lines_of_code
            monthly_data[checkin_date]['python'] += total_python_lines_of_code
            monthly_data[checkin_date]['count'] += 1

        # Write aggregated data to CSV
        for month, data in sorted(monthly_data.items()):
            avg_java_lines_of_code = data['java'] / data['count']
            avg_python_lines_of_code = data['python'] / data['count']
            avg_total_lines_of_code = (data['java'] + data['python']) / data['count']

            writer.writerow({
                'Month': month,
                'Branch': branch_name,
                'Average Java Lines of Code': avg_java_lines_of_code,
                'Average Python Lines of Code': avg_python_lines_of_code,
                'Average Total Lines of Code': avg_total_lines_of_code
            })

    print(f"Output written to {output_csv}")

# Entry point for the command-line interface
def main():
    parser = argparse.ArgumentParser(description="Analyze lines of code in Java and Python files in a git repository.")
    parser.add_argument('repo_url', help="URL of the git repository on GitHub")
    parser.add_argument('--output_csv', help="Path to the output CSV file", default='lines_of_code.csv')
    args = parser.parse_args()

    # Create a temporary directory to clone the repo
    temp_dir = tempfile.mkdtemp()

    try:
        # Clone the repository
        git.Repo.clone_from(args.repo_url, temp_dir)
        # Process the repository
        process_repository(temp_dir, args.output_csv)
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    main()
