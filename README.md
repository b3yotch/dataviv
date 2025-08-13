# Caltech 101 Explorer

A comprehensive web application for uploading, analyzing, and exploring the Caltech 101 image dataset with AI-powered search capabilities using **Google Gemini**.

---

## 📋 Table of Contents
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Configuration](#%EF%B8%8F-configuration)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## ✨ Features

### 🚀 Core Functionality
- 📤 **Dataset Upload**: Drag-and-drop ZIP file upload with progress tracking
- 🔄 **Automatic Extraction**: Intelligent ZIP extraction with nested directory handling
- 📊 **Statistical Analysis**: Comprehensive dataset statistics and metrics
- 📁 **File Structure Visualization**: Interactive exploration of dataset organization
- 📈 **Interactive Charts**: Dynamic visualizations using Plotly

### 🤖 AI-Powered Features
- 🧠 **Google Gemini Integration**: Natural language queries about your dataset
- 🔍 **Intelligent Search**: Ask questions like _"Show me all animal classes"_ or _"Compare airplane and car classes"_
- 📋 **Smart Indexing**: Automatic dataset indexing for AI search capabilities
- 💬 **Conversational Interface**: Chat-like interaction with your dataset

### 📊 Visualization & Analysis
- 📈 **Overview Dashboard**: Key metrics and file type distributions
- 🌅 **Class Distribution**: Histograms and statistical summaries
- 🌞 **Sunburst Charts**: Hierarchical visualization of dataset structure
- 🔄 **Class Comparisons**: Side-by-side analysis of different categories

---

## 🚀 Quick Start

### 1️⃣ Clone and Setup
git clone <your-repo>
cd caltech101-explorer
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt

## Run Application
# Terminal 1 - FastAPI Backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Streamlit Frontend
python -m streamlit run streamlit_app.py --server.port 8501

## Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1
streamlit==1.28.1
requests==2.31.0
pandas==2.1.3
plotly==5.18.0
google-generativeai==0.3.2
python-dotenv==1.0.0
jinja2==3.1.2
## Usage
Uploading a Dataset
Prepare Your Dataset

Download the Caltech 101 dataset as ZIP

Ensure it contains class directories with images

Upload via Web Interface

Go to http://localhost:8501

Use the sidebar upload widget

Wait for Processing

Progress bar shows extraction status

Exploring Your Dataset
Overview Tab: View total classes, images, file types, top classes

File Structure Tab: Navigate directories, check file counts

Visualizations Tab: Class distribution histograms, sunburst charts

Class Details Tab: Detailed per-class analysis, comparisons

AI Search Tab: Index and query dataset with natural language
