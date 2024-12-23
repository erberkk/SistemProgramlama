from flask import Flask, request, jsonify, render_template
import os
import subprocess

app = Flask(__name__)

def execute_linux_command(command):
    """
    Linux komutu çalıştırır ve sonucunu döndürür.
    """
    try:
        result = subprocess.run(command, check=True, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        return {"success": True, "output": result.stdout.decode()}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr.decode()}


@app.route('/')
def index():
    current_directory = request.args.get('dir', os.getcwd())
    try:
        files = []
        for f in os.listdir(current_directory):
            full_path = os.path.join(current_directory, f)
            is_dir = os.path.isdir(full_path)
            st_mode = os.stat(full_path).st_mode
            permission = oct(st_mode & 0o777)[2:]
            files.append({
                "name": f,
                "is_dir": is_dir,
                "permission": permission
            })

        return render_template('index.html', files=files, current_directory=current_directory)
    except Exception as e:
        return str(e), 500


@app.route('/api/perform_action', methods=['POST'])
def perform_action():
    action = request.json.get('action')
    target = request.json.get('target', '')
    destination = request.json.get('destination', '')
    permission = request.json.get('permission', '')

    try:
        if action == 'create_file':
            if os.path.exists(target):
                return jsonify({"error": f"A file named '{os.path.basename(target)}' already exists."}), 400
            result = execute_linux_command(f'touch "{target}"')
        elif action == 'create_directory':
            if os.path.exists(target):
                return jsonify({"error": f"A directory named '{os.path.basename(target)}' already exists."}), 400
            result = execute_linux_command(f'mkdir -p "{target}"')
        elif action == 'delete':
            result = execute_linux_command(f'rm -rf "{target}"')
        elif action == 'move':
            result = execute_linux_command(f'mv "{target}" "{destination}"')
        elif action == 'copy':
            result = execute_linux_command(f'cp -r "{target}" "{destination}"')
        elif action == 'chmod':
            result = execute_linux_command(f'chmod {permission} "{target}"')
        else:
            return jsonify({'error': 'Invalid action'}), 400

        if not result["success"]:
            return jsonify({"error": result["error"]}), 500

        return jsonify({"success": True, "output": result["output"]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/read_file', methods=['POST'])
def read_file():
    file_path = request.json.get('file_path')

    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/save_file', methods=['POST'])
def save_file():
    """
    Düzenlenen dosya içeriğini kaydeder.
    """
    file_path = request.json.get('file_path')
    new_content = request.json.get('new_content', '')

    try:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list_directory', methods=['POST'])
def list_directory():
    directory = request.json.get('directory', os.getcwd())
    try:
        items = []
        for f in os.listdir(directory):
            full_path = os.path.join(directory, f)
            is_dir = os.path.isdir(full_path)
            items.append({"name": f, "is_dir": is_dir})
        return jsonify({"success": True, "items": items, "current_directory": directory})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)