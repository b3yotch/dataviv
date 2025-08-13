import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import time

# Configuration
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Image Dataset Explorer",
    page_icon="🖼️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
    }
    .stats-number {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .tree-item {
        padding: 2px 0;
        margin-left: 20px;
    }
    .ai-response {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def upload_dataset(file):
    """Upload dataset to the API"""
    files = {"file": (file.name, file, "application/zip")}
    
    try:
        response = requests.post(
            f"{API_URL}/api/upload", 
            files=files,
            timeout=300
        )
        return response.json()
    except requests.exceptions.Timeout:
        return {"success": False, "detail": "Upload timeout"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "detail": f"Network error: {str(e)}"}

def get_datasets():
    """Get list of available datasets"""
    try:
        response = requests.get(f"{API_URL}/api/datasets")
        return response.json()["datasets"]
    except:
        return []

def get_dataset_structure(dataset_name):
    """Get dataset structure"""
    try:
        response = requests.get(f"{API_URL}/api/dataset/{dataset_name}/structure")
        return response.json()
    except Exception as e:
        st.error(f"Error fetching dataset structure: {str(e)}")
        return None

def search_dataset_llm(dataset_name, query):
    """Search dataset using LLM"""
    try:
        response = requests.post(
            f"{API_URL}/api/dataset/{dataset_name}/search",
            json={"query": query},
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def index_dataset_for_search(dataset_name):
    """Index dataset for search"""
    try:
        response = requests.post(f"{API_URL}/api/dataset/{dataset_name}/index")
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_dataset_indexed(dataset_name):
    """Check if dataset is indexed"""
    try:
        response = requests.get(f"{API_URL}/api/dataset/{dataset_name}/indexed")
        return response.json()
    except:
        return {"indexed": False}

def safe_percentage(part, total):
    """Safely calculate percentage, avoiding division by zero"""
    if total == 0 or part == 0:
        return 0.0
    return (part / total) * 100

def safe_average(total, count):
    """Safely calculate average, avoiding division by zero"""
    if count == 0:
        return 0.0
    return total / count

def main():
    st.title("🖼️ Caltech 101 Dataset Explorer")
    st.markdown("Upload and explore the Caltech 101 image dataset with AI-powered search")
    
    # Sidebar
    with st.sidebar:
        st.header("📤 Upload Dataset")
        uploaded_file = st.file_uploader(
            "Choose a ZIP file",
            type=['zip'],
            help="Upload the Caltech 101 dataset ZIP file"
        )
        
        if uploaded_file is not None:
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size / (1024*1024):.1f} MB)")
            
            if st.button("Upload and Extract", type="primary"):
                upload_progress = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Starting upload...")
                    upload_progress.progress(10)
                    
                    status_text.text("Uploading file...")
                    result = upload_dataset(uploaded_file)
                    upload_progress.progress(50)
                    
                    if result.get("success"):
                        status_text.text("Processing dataset...")
                        upload_progress.progress(90)
                        
                        time.sleep(1)
                        upload_progress.progress(100)
                        status_text.text("Upload completed successfully!")
                        
                        st.success(result["message"])
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {result.get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Error uploading dataset: {str(e)}")
                finally:
                    upload_progress.empty()
                    status_text.empty()
        
        st.markdown("---")
        
        # Dataset selector
        datasets = get_datasets()
        if datasets:
            st.header("📊 Available Datasets")
            dataset_names = [d["name"] for d in datasets]
            selected_dataset = st.selectbox("Select a dataset", dataset_names)
        else:
            st.info("No datasets available. Please upload a dataset.")
            selected_dataset = None
    
    # Main content area
    if selected_dataset:
        try:
            # Get dataset details
            dataset_info = get_dataset_structure(selected_dataset)
            
            if dataset_info is None:
                st.error("Failed to load dataset information")
                return
                
            stats = dataset_info.get("stats", {})
            structure = dataset_info.get("structure", {})
            
            # Validate stats data
            if not stats or stats.get("total_images", 0) == 0:
                st.warning("⚠️ Dataset appears to be empty or not properly processed")
                st.info("Please try re-uploading your dataset")
                return
            
            # Create tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📈 Overview", 
                "📁 File Structure", 
                "📊 Visualizations", 
                "🔍 Class Details",
                "🤖 AI Search"
            ])
            
            with tab1:
                st.header("Dataset Overview")
                
                # Display key metrics with safe values
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Classes", stats.get("total_folders", 0))
                with col2:
                    st.metric("Total Images", stats.get("total_images", 0))
                with col3:
                    st.metric("Total Files", stats.get("total_files", 0))
                with col4:
                    st.metric("Dataset", stats.get("dataset_name", "Unknown"))
                
                st.markdown("---")
                
                # File types distribution
                file_types = stats.get("file_types", {})
                if file_types:
                    st.subheader("File Types Distribution")
                    file_types_df = pd.DataFrame([
                        {"Type": k, "Count": v} for k, v in file_types.items()
                    ])
                    
                    fig = px.pie(file_types_df, values='Count', names='Type', 
                                title="Distribution of File Types")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Top classes by image count
                classes = stats.get("classes", [])
                if classes and len(classes) > 0:
                    st.subheader("Top 10 Classes by Image Count")
                    top_classes = sorted(classes, key=lambda x: x.get("count", 0), reverse=True)[:10]
                    
                    if top_classes:
                        top_classes_df = pd.DataFrame([
                            {"Class": c.get("name", "Unknown"), "Images": c.get("count", 0)} 
                            for c in top_classes if c.get("count", 0) > 0
                        ])
                        
                        if not top_classes_df.empty:
                            fig = px.bar(top_classes_df, x='Class', y='Images',
                                        title="Top 10 Classes by Number of Images")
                            fig.update_layout(
                                xaxis_tickangle=45,
                                xaxis_title="Class Name",
                                yaxis_title="Number of Images"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No valid class data to display")
                    else:
                        st.info("No class data available")
                else:
                    st.info("No classes found in the dataset")
            
            with tab2:
                st.header("File Structure")
                st.markdown("Explore the dataset directory structure")
                
                if structure and "name" in structure:
                    st.subheader(f"📁 {structure['name']}")
                    
                    if "children" in structure and structure["children"]:
                        for child in structure["children"]:
                            if child.get("type") == "directory":
                                st.markdown(f"**📁 {child.get('name', 'Unknown')}**")
                                if "children" in child:
                                    file_count = len([c for c in child["children"] if c.get("type") == "file"])
                                    st.text(f"   📊 Contains {file_count} files")
                            else:
                                st.text(f"📄 {child.get('name', 'Unknown')}")
                    else:
                        st.info("No structure data available")
                else:
                    st.info("No structure information available")
            
            with tab3:
                st.header("Dataset Visualizations")
                
                classes = stats.get("classes", [])
                total_images = stats.get("total_images", 0)
                
                if not classes or total_images == 0:
                    st.warning("No visualization data available")
                    return
                
                # Class distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Class Distribution")
                    all_classes_df = pd.DataFrame([
                        {"Class": c.get("name", "Unknown"), "Count": c.get("count", 0)} 
                        for c in classes if c.get("count", 0) > 0
                    ])
                    
                    if not all_classes_df.empty:
                        fig = px.histogram(all_classes_df, x='Count', 
                                         title="Distribution of Images per Class",
                                         labels={'Count': 'Number of Images'})
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No data for histogram")
                
                with col2:
                    st.subheader("Class Statistics")
                    total_classes = len(classes)
                    avg_images = safe_average(total_images, total_classes)
                    
                    class_counts = [c.get("count", 0) for c in classes if c.get("count", 0) > 0]
                    min_images = min(class_counts) if class_counts else 0
                    max_images = max(class_counts) if class_counts else 0
                    
                    stats_data = {
                        'Metric': ['Total Classes', 'Average Images/Class', 'Min Images', 'Max Images'],
                        'Value': [
                            str(total_classes),
                            f"{avg_images:.1f}",
                            str(min_images),
                            str(max_images)
                        ]
                    }
                    
                    stats_df = pd.DataFrame(stats_data)
                    st.table(stats_df)
                
                # Sunburst chart
                st.subheader("Hierarchical View of Dataset")
                
                if classes and len(classes) > 0:
                    sunburst_data = []
                    dataset_name = stats.get("dataset_name", "Dataset")
                    
                    for cls in classes[:20]:  # Top 20 classes
                        if cls.get("count", 0) > 0:
                            sunburst_data.append({
                                "labels": cls.get("name", "Unknown"),
                                "parents": dataset_name,
                                "values": cls.get("count", 0)
                            })
                    
                    if sunburst_data:
                        sunburst_data.append({
                            "labels": dataset_name,
                            "parents": "",
                            "values": 0
                        })
                        
                        sunburst_df = pd.DataFrame(sunburst_data)
                        
                        fig = px.sunburst(sunburst_df, 
                                        names='labels', 
                                        parents='parents', 
                                        values='values',
                                        title="Dataset Structure (Top 20 Classes)")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No data available for sunburst chart")
            
            with tab4:
                st.header("Class Details")
                
                classes = stats.get("classes", [])
                total_images = stats.get("total_images", 0)
                
                if not classes:
                    st.info("No class information available")
                    return
                
                # Class selector
                class_names = [c.get("name", f"Class_{i}") for i, c in enumerate(classes)]
                selected_class = st.selectbox("Select a class to view details", class_names)
                
                if selected_class:
                    class_info = next((c for c in classes if c.get("name") == selected_class), None)
                    
                    if class_info:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Class Name", selected_class)
                        with col2:
                            st.metric("Number of Images", class_info.get("count", 0))
                        with col3:
                            percentage = safe_percentage(class_info.get("count", 0), total_images)
                            st.metric("Percentage of Dataset", f"{percentage:.1f}%")
                        
                        # Display file list
                        st.subheader(f"Files in '{selected_class}' class")
                        
                        files = class_info.get("files", [])
                        if files:
                            files_per_row = 4
                            
                            for i in range(0, min(len(files), 20), files_per_row):
                                cols = st.columns(files_per_row)
                                for j, col in enumerate(cols):
                                    if i + j < len(files):
                                        with col:
                                            st.info(f"📄 {files[i + j]}")
                            
                            if len(files) > 20:
                                st.info(f"... and {len(files) - 20} more files")
                        else:
                            st.info("No file details available")
                        
                        # Compare with other classes
                        st.subheader("Comparison with Other Classes")
                        
                        compare_classes = sorted(classes, key=lambda x: x.get("count", 0), reverse=True)[:10]
                        compare_df = pd.DataFrame([
                            {"Class": c.get("name", "Unknown"), "Images": c.get("count", 0), 
                             "Highlight": "Selected" if c.get("name") == selected_class else "Other"} 
                            for c in compare_classes
                        ])
                        
                        if not compare_df.empty:
                            fig = px.bar(compare_df, x='Class', y='Images', color='Highlight',
                                        title=f"'{selected_class}' compared to Top 10 Classes",
                                        color_discrete_map={"Selected": "#ff6b6b", "Other": "#4ecdc4"})
                            fig.update_layout(xaxis_tickangle=45)
                            st.plotly_chart(fig, use_container_width=True)
            
            with tab5:
                st.header("🤖 AI-Powered Dataset Search")
                st.markdown("Ask natural language questions about your dataset using Google Gemini!")
                
                # Check if dataset is indexed
                index_status = check_dataset_indexed(selected_dataset)
                
                if not index_status.get("indexed", False):
                    st.warning("⚠️ Dataset needs to be indexed for AI search")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.info("💡 Click 'Index Dataset' to enable AI-powered search capabilities")
                    with col2:
                        if st.button("🔄 Index Dataset", type="primary"):
                            with st.spinner("🤖 Indexing dataset for AI search..."):
                                try:
                                    result = index_dataset_for_search(selected_dataset)
                                    if result.get("success"):
                                        st.success(f"✅ Indexed {result.get('classes_indexed', 0)} classes with {result.get('total_images', 0)} images!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Indexing failed: {result.get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                else:
                    st.success(f"✅ Dataset indexed with {index_status.get('classes', 0)} classes and {index_status.get('total_images', 0)} images")
                    
                    st.markdown("---")
                    
                    # Example queries
                    with st.expander("💡 Example Queries", expanded=False):
                        st.markdown("""
                        **Try asking questions like:**
                        
                        📊 **Dataset Statistics:**
                        - "How many images are in the dataset?"
                        - "What are the top 5 classes with the most images?"
                        - "Which classes have fewer than 50 images?"
                        - "What's the average number of images per class?"
                        
                        🔍 **Finding Specific Content:**
                        - "Find me classes related to animals"
                        - "Show me vehicle classes"
                        - "Which classes contain faces or people?"
                        - "What objects are in the dataset?"
                        
                        📈 **Comparisons & Analysis:**
                        - "Compare the airplane and car classes"
                        - "Which class has the most images?"
                        - "Show me classes with similar image counts"
                        - "What's the distribution of images across classes?"
                        
                        🎯 **Specific Searches:**
                        - "How many accordion images are there?"
                        - "Find classes related to music instruments"
                        - "Show me all animal classes and their counts"
                        """)
                    
                    # Search interface
                    st.subheader("🔍 Ask Your Question")
                    
                    # Quick search buttons
                    st.markdown("**Quick Searches:**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    quick_searches = {
                        "🐾 Animals": "Show me all animal classes in the dataset",
                        "🚗 Vehicles": "Find vehicle and transportation related classes",
                        "📊 Top Classes": "What are the top 10 classes with most images?",
                        "📈 Statistics": "Give me overall dataset statistics"
                    }
                    
                    selected_quick_search = None
                    with col1:
                        if st.button("🐾 Animals"):
                            selected_quick_search = quick_searches["🐾 Animals"]
                    with col2:
                        if st.button("🚗 Vehicles"):
                            selected_quick_search = quick_searches["🚗 Vehicles"]
                    with col3:
                        if st.button("📊 Top Classes"):
                            selected_quick_search = quick_searches["📊 Top Classes"]
                    with col4:
                        if st.button("📈 Statistics"):
                            selected_quick_search = quick_searches["📈 Statistics"]
                    
                    # Search input
                    search_query = st.text_area(
                        "Ask a question about your dataset:",
                        value=selected_quick_search or "",
                        height=100,
                        placeholder="e.g., How many images are in each class? or Find classes with animals",
                        help="Ask natural language questions about your dataset"
                    )
                    
                    # Search button
                    if st.button("🔍 Search with AI", type="primary", disabled=not search_query.strip()):
                        if search_query.strip():
                            with st.spinner("🤖 AI is analyzing your dataset..."):
                                try:
                                    result = search_dataset_llm(selected_dataset, search_query.strip())
                                    
                                    if result.get("success"):
                                        # Display AI response
                                        st.markdown("### 🤖 AI Response")
                                        
                                        # Custom styled response box
                                        st.markdown(f"""
                                        <div class="ai-response">
                                        {result["response"]}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Show relevant classes if any
                                        if result.get("relevant_classes"):
                                            st.markdown("### 📊 Relevant Classes")
                                            
                                            relevant_classes = result["relevant_classes"]
                                            
                                            if relevant_classes:
                                                # Create visualization
                                                relevant_df = pd.DataFrame(relevant_classes)
                                                
                                                # Bar chart
                                                fig = px.bar(
                                                    relevant_df, 
                                                    x='name', 
                                                    y='count',
                                                    title="Classes Relevant to Your Query",
                                                    labels={'name': 'Class Name', 'count': 'Number of Images'},
                                                    color='count',
                                                    color_continuous_scale='viridis'
                                                )
                                                fig.update_layout(xaxis_tickangle=45)
                                                st.plotly_chart(fig, use_container_width=True)
                                                
                                                # Detailed table
                                                st.markdown("**Detailed Information:**")
                                                for cls in relevant_classes:
                                                    col1, col2, col3 = st.columns([3, 1, 2])
                                                    with col1:
                                                        st.markdown(f"**{cls['name']}**")
                                                    with col2:
                                                        st.markdown(f"{cls['count']} images")
                                                    with col3:
                                                        st.markdown(f"{cls['percentage']:.1f}% of dataset")
                                        
                                        # Show query statistics
                                        if result.get("dataset_stats"):
                                            st.markdown("### 📈 Query Context")
                                            stats_info = result["dataset_stats"]
                                            
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Total Classes", stats_info.get("total_classes", "N/A"))
                                            with col2:
                                                st.metric("Total Images", stats_info.get("total_images", "N/A"))
                                            with col3:
                                                st.metric("Query Processed", "✅" if stats_info.get("query_processed") else "❌")
                                    
                                    else:
                                        st.error(f"❌ Search failed: {result.get('error', 'Unknown error')}")
                                        
                                        # Helpful error message
                                        if "not indexed" in result.get('error', '').lower():
                                            st.info("💡 Please index the dataset first using the 'Index Dataset' button above")
                                        elif "api" in result.get('error', '').lower():
                                            st.info("💡 Make sure your Google API key is configured in the .env file")
                                
                                except Exception as e:
                                    st.error(f"❌ Error during search: {str(e)}")
                                    
                                    # Debugging info
                                    with st.expander("🔧 Debug Information"):
                                        st.code(f"Error: {str(e)}")
                                        st.code(f"Query: {search_query}")
                                        st.code(f"Dataset: {selected_dataset}")
                                        st.info("💡 Make sure both FastAPI backend and Gemini integration are working")
                    
                    # Search tips
                    st.markdown("---")
                    st.markdown("### 💡 Search Tips")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        **For Better Results:**
                        - Be specific in your questions
                        - Ask about class names, counts, or comparisons
                        - Use natural language
                        - Try different phrasings if needed
                        """)
                    
                    with col2:
                        st.markdown("""
                        **AI Can Help With:**
                        - Finding specific classes
                        - Counting images and statistics
                        - Comparing different classes
                        - Dataset analysis and insights
                        """)
        
        except Exception as e:
            st.error(f"Error loading dataset: {str(e)}")
            
            # Debug information
            with st.expander("🔧 Debug Information"):
                st.code(f"Selected dataset: {selected_dataset}")
                st.code(f"Error: {str(e)}")
                st.info("💡 Make sure FastAPI is running on http://localhost:8000")
    
    else:
        # No dataset selected - landing page
        st.info("👈 Please upload a dataset using the sidebar to begin exploring")
        
        # Getting started guide
        st.markdown("""
        ## 🚀 Getting Started
        
        1. **📤 Upload Dataset**: Use the sidebar to upload your Caltech 101 ZIP file
        2. **📁 Explore Structure**: View the file structure and organization  
        3. **📊 Analyze Statistics**: See detailed statistics about classes and images
        4. **📈 Visualize Data**: Interactive charts and graphs
        5. **🤖 AI Search**: Ask natural language questions about your dataset
        
        ## 🤖 AI-Powered Features
        
        Once your dataset is uploaded and indexed, you can:
        - Ask questions in plain English
        - Get intelligent insights about your data
        - Find specific classes or image types
        - Compare different categories
        - Get statistical summaries
        
        ## 📊 Dataset Features
        
        - ✅ Automatic ZIP extraction
        - ✅ File structure visualization  
        - ✅ Class distribution analysis
        - ✅ Interactive visualizations
        - ✅ Detailed class information
        - ✅ AI-powered search with Google Gemini
        - ✅ Natural language queries
        
        ## 📁 About Caltech 101
        
        The Caltech 101 dataset contains pictures of objects belonging to 101 categories.
        About 40 to 800 images per category. Most categories have about 50 images.
        
        Perfect for exploring computer vision datasets and understanding data distribution!
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📷 Dataset Contents
            - **101 object categories**
            - **~9,000 images total**  
            - **Variable size images**
            - **JPEG format**
            - **Diverse object types**
            """)
        
        with col2:
            st.markdown("""
            ### 🎯 Sample Classes
            - 👤 Faces & People
            - ✈️ Airplanes & Vehicles
            - 🐆 Animals (Leopards, Elephants, etc.)
            - 🎵 Musical Instruments
            - 🏠 Objects & Furniture  
            - **And 96+ more categories!**
            """)

if __name__ == "__main__":
    main()