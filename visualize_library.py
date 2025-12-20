import pandas as pd
from pyvis.network import Network
import os

# --- CONFIGURATION ---
INPUT_FILE = "literature_matrix.csv"
OUTPUT_FILE = "interactive_library_graph.html"

def clean_str(val):
    """Sanitizes strings to prevent JS errors."""
    if pd.isna(val): return "Unknown"
    # Remove quotes that might break the generated Javascript
    return str(val).replace("'", "").replace('"', "")

def clean_title(title):
    title = clean_str(title)
    return title[:20] + "..." if len(title) > 20 else title

def build_graph():
    if not os.path.exists(INPUT_FILE):
        print("Error: Matrix file not found.")
        return

    print("🕸️  Building Advanced Knowledge Graph...")
    df = pd.read_csv(INPUT_FILE)
    
    # Initialize Network with In-Line resources (Fixes loading issues)
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", select_menu=True, cdn_resources='in_line')
    
    # 1. OPTION: "God Mode" (Settings Menu)
    # This adds the control panel to the bottom of the HTML file
    net.show_buttons(filter_=['physics']) 

    topic_map = {}
    author_map = {}

    for index, row in df.iterrows():
        try:
            # Data Extraction & Cleaning
            title = clean_str(row.get('Title', 'Untitled'))
            short_label = clean_title(title)
            topic = clean_str(row.get('Topic', 'Uncategorized'))
            author = clean_str(row.get('Author', 'Unknown')).split(',')[0] # Main author only
            priority = clean_str(row.get('Priority', 'Low'))
            
            # 2. OPTION: Dynamic Sizing (Based on Citations)
            try:
                citations = int(row.get('Citations', 0))
            except:
                citations = 0
            
            # Base size 15 + 1 point for every 20 citations (capped at size 60)
            paper_size = 15 + (citations / 20)
            if paper_size > 60: paper_size = 60

            # Color Logic (Priority)
            color = "#97c2fc" # Default Blue
            if "Critical" in priority: color = "#ff0000" # Red
            elif "High" in priority: color = "#fb7e81" # Pink

            # 3. OPTION: Semantic Shapes
            # Add PAPER Node (Dot)
            hover_text = f"{title}\nCitations: {citations}\nPriority: {priority}"
            net.add_node(title, label=short_label, title=hover_text, color=color, shape="dot", size=paper_size)

            # Add TOPIC Node (Box)
            if topic not in topic_map:
                topic_map[topic] = True
                # 'box' makes it look like a label/tag
                net.add_node(topic, label=topic, color="#ffff00", shape="box", font={'color': 'black'}, size=25) 
            net.add_edge(title, topic, color="rgba(255,255,255,0.2)")

            # Add AUTHOR Node (Star)
            if author and author.lower() != "unknown":
                if author not in author_map:
                    author_map[author] = True
                    # 'star' highlights the key players
                    net.add_node(author, label=author, color="#7BE141", shape="star", size=20)
                net.add_edge(title, author, color="rgba(255,255,255,0.2)")

        except Exception as e:
            print(f"Skipping row {index} due to data error: {e}")

    # Save the graph
    try:
        net.save_graph(OUTPUT_FILE)
        print(f"  [Success] Graph saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"  [Error] Could not save graph: {e}")

if __name__ == "__main__":
    build_graph()
