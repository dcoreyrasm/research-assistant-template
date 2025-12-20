import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
import networkx as nx 
import matplotlib.pyplot as plt

# Optional: WordCloud
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

# Page Config
st.set_page_config(page_title="Research Ops Dashboard", layout="wide", page_icon="🎓")

st.title("🎓 Research Ops Dashboard")
st.markdown("### Automated Intelligence for Academic Research")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    data = {}
    if os.path.exists("research_ops_log.csv"):
        try:
            data['log'] = pd.read_csv("research_ops_log.csv")
            data['log']['Timestamp'] = pd.to_datetime(data['log']['Timestamp'])
        except Exception as e:
            st.error(f"Error reading log file: {e}")
            return {}
    
    if os.path.exists("literature_matrix.csv"):
        try:
            data['matrix'] = pd.read_csv("literature_matrix.csv")
            for col in ['Topic', 'Author', 'Tag', 'AI_Note', 'Title']:
                if col in data['matrix'].columns:
                    data['matrix'][col] = data['matrix'][col].astype(str)
            
            # Ensure numeric columns
            if 'Citations' in data['matrix'].columns:
                data['matrix']['Citations'] = pd.to_numeric(data['matrix']['Citations'], errors='coerce').fillna(0)
            if 'Year' in data['matrix'].columns:
                data['matrix']['Year'] = pd.to_numeric(data['matrix']['Year'], errors='coerce').fillna(0)

        except Exception as e:
            st.error(f"Error reading matrix file: {e}")
            return {}
            
    return data

data = load_data()

if 'log' not in data:
    st.error("❌ No log file found (research_ops_log.csv). Run the extraction script first.")
    st.stop()

log_df = data['log']
matrix_df = data.get('matrix', pd.DataFrame())

# --- KPI ROW ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Papers Processed", len(log_df[log_df['Action'] == 'Import']))
with col2:
    success_rate = (len(log_df[log_df['Status'] == 'Success']) / len(log_df) * 100) if len(log_df) > 0 else 0
    st.metric("Success Rate", f"{success_rate:.1f}%")
with col3:
    if not log_df.empty:
        last_run = log_df['Timestamp'].max().strftime('%m-%d %H:%M')
    else:
        last_run = "N/A"
    st.metric("Last Robot Run", last_run)
with col4:
    total_matrix = len(matrix_df) if not matrix_df.empty else 0
    if not log_df.empty:
        days_active = (datetime.now() - log_df['Timestamp'].min()).days
        # Prevent division by zero
        weeks = max(1, days_active / 7)
        avg_weekly = len(log_df[log_df['Action'] == 'Import']) / weeks
        projected = int(total_matrix + (avg_weekly * 4)) 
    else:
        projected = total_matrix
    st.metric("Matrix Size (Proj. +1 Mo)", f"{total_matrix} ➜ {projected}")

# --- TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Trends", "🕸️ Network Graph", "🗺️ Knowledge Maps", "🔬 Deep Analysis", "📚 Deep Search", "⚙️ Audit"])

# --- TAB 1: TRENDS ---
with tab1:
    st.subheader("Weekly Research Velocity & Forecast")
    if not log_df.empty:
        weekly = log_df[log_df['Action'] == 'Import'].set_index('Timestamp').resample('W').count().reset_index()
        fig_weekly = px.bar(weekly, x='Timestamp', y='Paper_Title', title="Papers Imported per Week")
        weekly['Trend'] = weekly['Paper_Title'].rolling(window=3, min_periods=1).mean()
        fig_weekly.add_scatter(x=weekly['Timestamp'], y=weekly['Trend'], mode='lines', name='3-Week Moving Avg', line=dict(color='orange'))
        st.plotly_chart(fig_weekly, use_container_width=True)
    else:
        st.info("No data available for trends.")
    
    if not matrix_df.empty and 'Topic' in matrix_df.columns:
        st.subheader("Topic Momentum")
        topic_counts = matrix_df['Topic'].value_counts().reset_index()
        topic_counts.columns = ['Topic', 'Count']
        fig_topics = px.pie(topic_counts, names='Topic', values='Count', title="Current Research Mix", hole=0.4)
        st.plotly_chart(fig_topics, use_container_width=True)

# --- TAB 2: INTERACTIVE NETWORK GRAPH (IMPROVED READABILITY) ---
with tab2:
    st.subheader("Research Connectivity Network")
    st.markdown("An interactive view of how Papers connect to Topics.")
    
    if not matrix_df.empty:
        # Build Graph
        G = nx.Graph()
        sample_matrix = matrix_df.head(50) 
        
        for idx, row in sample_matrix.iterrows():
            # Shorten title but keep enough context
            full_title = str(row['Title'])
            paper_label = full_title[:25] + "..." if len(full_title) > 25 else full_title
            topic = str(row['Topic'])
            
            G.add_node(paper_label, type='Paper', title=full_title) # Store full title for hover
            G.add_node(topic, type='Topic', title=topic)
            G.add_edge(paper_label, topic)
            
        # Generate Layout (k controls spacing - higher is more spread out)
        pos = nx.spring_layout(G, seed=42, k=0.5)
        
        # Create Plotly traces
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_color = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node) # Short label for graph
            node_hover.append(G.nodes[node].get('title', node)) # Full title for hover
            
            # Color/Size logic
            if G.nodes[node]['type'] == 'Topic':
                node_color.append('#1f77b4') # Blue for Topics
                node_size.append(25) # Larger Topics
            else:
                node_color.append('#ff7f0e') # Orange for Papers
                node_size.append(12) # Smaller Papers

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text', # Show text AND dots
            text=node_text,
            textposition="top center",
            hovertext=node_hover, # Show full title on hover
            hoverinfo='text',
            marker=dict(
                showscale=False,
                color=node_color,
                size=node_size,
                line_width=2))

        # Increase overall figure size for better spacing
        fig_network = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                        title='Research Network (Top 50 Papers)',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        height=700, # Taller graph
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )
        
        st.plotly_chart(fig_network, use_container_width=True)
        st.caption("Hover over dots to see full titles. Zoom in to explore clusters.")
    else:
        st.info("No matrix data available.")


# --- TAB 3: KNOWLEDGE MAPS (Hierarchical) ---
with tab3:
    st.subheader("Hierarchical Research Maps")
    if not matrix_df.empty:
        map_type = st.radio("Select Map Style:", ["Treemap (Hierarchical)", "Sunburst (Radial)", "Scatter Plot (Impact vs Time)"], horizontal=True)
        if map_type == "Treemap (Hierarchical)":
            fig = px.treemap(matrix_df, path=['Topic', 'Title'], values='Citations', color='Citations', hover_data=['Author', 'Year'], color_continuous_scale='RdBu')
            st.plotly_chart(fig, use_container_width=True)
        elif map_type == "Sunburst (Radial)":
            fig = px.sunburst(matrix_df, path=['Topic', 'Title'], values='Citations', color='Citations')
            st.plotly_chart(fig, use_container_width=True)
        elif map_type == "Scatter Plot (Impact vs Time)":
            fig = px.scatter(matrix_df, x="Year", y="Citations", color="Topic", size="Citations", hover_data=['Title', 'Author'])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No matrix data available.")

# --- TAB 4: DEEP ANALYSIS ---
with tab4:
    st.subheader("Advanced Research Analytics")
    if not matrix_df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🔥 Topic Heatmap (Frequency by Year)")
            heatmap_data = matrix_df.groupby(['Topic', 'Year']).size().reset_index(name='Count')
            heatmap_pivot = heatmap_data.pivot(index='Topic', columns='Year', values='Count').fillna(0)
            fig_heat = px.imshow(heatmap_pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues")
            st.plotly_chart(fig_heat, use_container_width=True)

        with col_b:
            st.markdown("#### 👩‍🏫 Author Impact Analysis")
            if 'Author' in matrix_df.columns:
                author_stats = matrix_df.groupby('Author').agg(
                    Paper_Count=('Title', 'count'),
                    Total_Citations=('Citations', 'sum'),
                    Avg_Citations=('Citations', 'mean')
                ).reset_index()
                author_stats = author_stats[(author_stats['Paper_Count'] > 1) | (author_stats['Total_Citations'] > 5)]
                fig_bubble = px.scatter(author_stats, x="Paper_Count", y="Avg_Citations", size="Total_Citations", color="Total_Citations", hover_name="Author", title="Productivity vs. Impact")
                st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.info("Need more data to generate deep analysis.")

# --- TAB 5: DEEP SEARCH ---
with tab5:
    st.subheader("Search Your Knowledge Base")
    if not matrix_df.empty:
        search_query = st.text_input("Search by Title, Author, or Note Content...", "")
        if search_query:
            mask = (
                matrix_df['Title'].str.contains(search_query, case=False, na=False) |
                matrix_df['Author'].str.contains(search_query, case=False, na=False) |
                matrix_df['AI_Note'].str.contains(search_query, case=False, na=False)
            )
            results = matrix_df[mask]
            st.success(f"Found {len(results)} matches.")
            st.dataframe(results[['Year', 'Title', 'Author', 'Topic', 'Citations']])
            if not results.empty:
                with st.expander("View Abstract/Summary for Top Result"):
                    st.markdown(results.iloc[0]['AI_Note'], unsafe_allow_html=True)
        else:
            st.dataframe(matrix_df)
    else:
        st.info("No literature matrix found yet.")

# --- TAB 6: AUDIT LOG ---
with tab6:
    st.subheader("System Health Log")
    st.dataframe(log_df.sort_values('Timestamp', ascending=False), use_container_width=True)
    errors = log_df[log_df['Status'] == 'Error']
    if not errors.empty:
        st.error(f"Found {len(errors)} errors.")
        st.write(errors[['Timestamp', 'Details']])
