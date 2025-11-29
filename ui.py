from flask import Flask, render_template, request, jsonify
import webbrowser
import threading
import time
import os
from manager import GreenSpaceManager  # Import your existing classes

def launch_green_space_explorer(pbf_file_path: str, host: str = 'localhost', port: int = 5000, open_browser: bool = True):
    """
    Main function to launch Flask site with predefined PBF file
    
    Args:
        pbf_file_path: Path to the OSM PBF file (set server-side)
        host: Host to run the server on
        port: Port to run the server on
        open_browser: Whether to automatically open the browser
    """
    
    app = Flask(__name__)
    
    # Load data once at startup
    print(f"Loading green spaces from: {pbf_file_path}")
    manager = GreenSpaceManager()
    
    try:
        green_spaces = manager.get_green_spaces(pbf_file_path)
        print(f"✅ Successfully loaded {len(green_spaces)} green spaces")
    except Exception as e:
        print(f"❌ Failed to load PBF file: {e}")
        green_spaces = []
    
    @app.route('/')
    def index():
        """Main page"""
        return render_template('index.html', 
                             total_spaces=len(green_spaces),
                             source_file=os.path.basename(pbf_file_path))

    @app.route('/api/spaces')
    def get_spaces():
        """API endpoint to get filtered green spaces"""
        space_type = request.args.get('type', 'all')
        name_filter = request.args.get('name', '').lower()
        
        filtered = green_spaces
        
        if space_type != 'all':
            filtered = [s for s in filtered if s.space_type.value == space_type]
        
        if name_filter:
            filtered = [s for s in filtered if name_filter in s.name.lower()]
        
        return jsonify([space.to_dict() for space in filtered])

    @app.route('/api/stats')
    def get_stats():
        """API endpoint to get statistics"""
        from collections import Counter
        
        if not green_spaces:
            return jsonify({'error': 'No data loaded'})
            
        type_counts = Counter(space.space_type.value for space in green_spaces)
        named_count = sum(1 for space in green_spaces if space.has_name)
        
        return jsonify({
            'total_spaces': len(green_spaces),
            'named_spaces': named_count,
            'type_counts': dict(type_counts),
            'source_file': os.path.basename(pbf_file_path)
        })

    @app.route('/api/view/<int:osm_id>')
    def view_space(osm_id):
        """API endpoint to view a space on OSM"""
        webbrowser.open(f"https://www.openstreetmap.org/way/{osm_id}")
        return jsonify({'success': True})

    # Open browser after delay
    def open_browser_delayed():
        time.sleep(1.5)
        url = f"http://{host}:{port}"
        print(f"🌐 Opening browser to: {url}")
        webbrowser.open(url)

    # Start server
    print(f"🚀 Starting Green Space Explorer...")
    print(f"📁 Source file: {pbf_file_path}")
    print(f"📍 Server: http://{host}:{port}")
    print(f"📊 Green spaces loaded: {len(green_spaces)}")
    
    if open_browser:
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    app.run(host=host, port=port, debug=False)

# Usage - just specify your PBF file path here
if __name__ == "__main__":
    # SET YOUR PBF FILE PATH HERE
    PBF_FILE = "west-midlands-251128.osm.pbf"  # Change this to your actual file path
    
    launch_green_space_explorer(
        pbf_file_path=PBF_FILE,
        host='localhost', 
        port=5000,
        open_browser=True
    )