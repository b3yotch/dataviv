import google.generativeai as genai
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

class GeminiDatasetSearch:
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please add it to your .env file.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Dataset metadata cache
        self.dataset_metadata = {}
    
    def index_dataset(self, dataset_name: str, stats: Dict[str, Any], structure: Dict[str, Any]):
        """Index dataset for search"""
        
        # Create comprehensive metadata
        metadata = {
            "dataset_name": dataset_name,
            "total_classes": stats.get("total_folders", 0),
            "total_images": stats.get("total_images", 0),
            "total_files": stats.get("total_files", 0),
            "file_types": stats.get("file_types", {}),
            "classes": [],
            "class_details": {}
        }
        
        # Process classes
        for class_info in stats.get("classes", []):
            class_name = class_info["name"]
            class_count = class_info["count"]
            
            metadata["classes"].append(class_name)
            metadata["class_details"][class_name] = {
                "count": class_count,
                "percentage": (class_count / metadata["total_images"] * 100) if metadata["total_images"] > 0 else 0,
                "files": class_info.get("files", [])[:5]  # Store first 5 files as examples
            }
        
        # Sort classes by count
        metadata["classes_by_count"] = sorted(
            metadata["classes"], 
            key=lambda x: metadata["class_details"][x]["count"], 
            reverse=True
        )
        
        # Calculate statistics
        if metadata["classes"]:
            counts = [metadata["class_details"][c]["count"] for c in metadata["classes"]]
            metadata["stats"] = {
                "max_images_per_class": max(counts),
                "min_images_per_class": min(counts),
                "avg_images_per_class": sum(counts) / len(counts),
                "largest_class": metadata["classes_by_count"][0],
                "smallest_class": min(metadata["classes"], key=lambda x: metadata["class_details"][x]["count"])
            }
        
        self.dataset_metadata[dataset_name] = metadata
        print(f"Dataset {dataset_name} indexed with {len(metadata['classes'])} classes")
        return metadata
    
    def create_context_prompt(self, dataset_name: str) -> str:
        """Create context prompt for Gemini"""
        
        if dataset_name not in self.dataset_metadata:
            return "No dataset information available."
        
        metadata = self.dataset_metadata[dataset_name]
        
        # Create a comprehensive context
        context = f"""You are an AI assistant helping users explore the {metadata['dataset_name']} dataset.

DATASET OVERVIEW:
- Dataset Name: {metadata['dataset_name']}
- Total Classes: {metadata['total_classes']}
- Total Images: {metadata['total_images']}
- Total Files: {metadata['total_files']}

FILE TYPES DISTRIBUTION:
"""
        
        for file_type, count in metadata['file_types'].items():
            context += f"- {file_type}: {count} files\n"
        
        context += f"\nTOP 20 CLASSES BY IMAGE COUNT:\n"
        for i, class_name in enumerate(metadata['classes_by_count'][:20], 1):
            details = metadata['class_details'][class_name]
            context += f"{i:2d}. {class_name}: {details['count']} images ({details['percentage']:.1f}%)\n"
        
        if len(metadata['classes']) > 20:
            context += f"... and {len(metadata['classes']) - 20} more classes\n"
        
        if metadata.get('stats'):
            stats = metadata['stats']
            context += f"""
DATASET STATISTICS:
- Largest class: {stats['largest_class']} ({metadata['class_details'][stats['largest_class']]['count']} images)
- Smallest class: {stats['smallest_class']} ({metadata['class_details'][stats['smallest_class']]['count']} images)
- Average images per class: {stats['avg_images_per_class']:.1f}
- Maximum images in a class: {stats['max_images_per_class']}
- Minimum images in a class: {stats['min_images_per_class']}
"""
        
        context += """
ALL AVAILABLE CLASSES:
"""
        # List all classes for reference
        for class_name in sorted(metadata['classes']):
            context += f"- {class_name}\n"
        
        context += """

INSTRUCTIONS:
You are helping users explore this image dataset. Provide accurate, specific, and helpful responses based on the data above.

- When asked about specific classes, provide exact counts and percentages
- When asked for comparisons, use the actual numbers
- When asked about finding specific types of images, suggest relevant classes
- If asked about statistics, reference the actual dataset statistics
- Be conversational but precise
- If you don't have specific information about something, clearly state that
- When suggesting classes, explain why they're relevant to the user's query
"""
        
        return context
    
    async def search_dataset(self, dataset_name: str, query: str) -> Dict[str, Any]:
        """Search dataset using natural language query"""
        
        if dataset_name not in self.dataset_metadata:
            return {
                "success": False,
                "error": f"Dataset '{dataset_name}' not indexed. Please index the dataset first."
            }
        
        try:
            # Create context prompt
            context = self.create_context_prompt(dataset_name)
            
            # Create the full prompt
            full_prompt = f"""
{context}

USER QUERY: {query}

Please provide a helpful and accurate response based on the dataset information above. Include specific numbers, class names, and actionable suggestions where relevant. Be conversational and helpful.
"""
            
            print(f"Processing query for {dataset_name}: {query}")
            
            # Get response from Gemini
            response = self.model.generate_content(full_prompt)
            
            # Extract relevant classes mentioned in the query
            relevant_classes = self.extract_relevant_classes(dataset_name, query)
            
            return {
                "success": True,
                "response": response.text,
                "relevant_classes": relevant_classes,
                "dataset_stats": {
                    "total_classes": self.dataset_metadata[dataset_name]["total_classes"],
                    "total_images": self.dataset_metadata[dataset_name]["total_images"],
                    "query_processed": True
                }
            }
            
        except Exception as e:
            print(f"Error in Gemini search: {str(e)}")
            return {
                "success": False,
                "error": f"Error processing query: {str(e)}"
            }
    
    def extract_relevant_classes(self, dataset_name: str, query: str) -> List[Dict[str, Any]]:
        """Extract classes relevant to the query"""
        
        if dataset_name not in self.dataset_metadata:
            return []
        
        metadata = self.dataset_metadata[dataset_name]
        relevant = []
        
        # Simple keyword matching
        query_lower = query.lower()
        
        # Check for direct class name mentions
        for class_name in metadata["classes"]:
            class_lower = class_name.lower()
            class_details = metadata["class_details"][class_name]
            
            # Direct match
            if class_lower in query_lower or any(word in class_lower for word in query_lower.split()):
                relevant.append({
                    "name": class_name,
                    "count": class_details["count"],
                    "percentage": class_details["percentage"],
                    "reason": "Class name matches query"
                })
        
        # Check for category-based matching
        category_mapping = {
            "animal": ["leopard", "ant", "elephant", "crocodile", "dolphin", "flamingo", "kangaroo", "lobster", "octopus", "sea_horse", "starfish", "stegosaurus", "trilobite"],
            "vehicle": ["car", "airplane", "motorbike", "ferry", "helicopter"],
            "face": ["face", "person"],
            "object": ["accordion", "anchor", "barrel", "bass", "bell", "bonsai", "bottle", "brain", "buddha", "calculator", "camera", "cannon", "chair", "chandelier", "clock", "cup", "dalmatian", "dragonfly", "electric_guitar", "garfield", "gramophone", "guitar", "hammer", "hawksbill", "headphone", "inline_skate", "joshua_tree", "ketch", "lamp", "laptop", "llama", "mandolin", "mayfly", "metronome", "minaret", "nautilus", "pagoda", "panda", "piano", "pigeon", "pizza", "platypus", "pyramid", "revolver", "rhino", "rooster", "saxophone", "schooner", "scissors", "scorpion", "soccer_ball", "stapler", "stop_sign", "strawberry", "sunflower", "table", "tick", "umbrella", "watch", "water_lilly", "wheelchair", "wild_cat", "windsor_chair", "wrench", "yin_yang"]
        }
        
        for category, keywords in category_mapping.items():
            if category in query_lower:
                for class_name in metadata["classes"]:
                    if any(keyword in class_name.lower() for keyword in keywords):
                        if not any(r["name"] == class_name for r in relevant):  # Avoid duplicates
                            class_details = metadata["class_details"][class_name]
                            relevant.append({
                                "name": class_name,
                                "count": class_details["count"],
                                "percentage": class_details["percentage"],
                                "reason": f"Matches {category} category"
                            })
        
        # Sort by count (most images first) and limit to top 10
        relevant.sort(key=lambda x: x["count"], reverse=True)
        return relevant[:10]
    
    def get_class_suggestions(self, dataset_name: str, search_term: str) -> List[str]:
        """Get class name suggestions based on search term"""
        
        if dataset_name not in self.dataset_metadata:
            return []
        
        metadata = self.dataset_metadata[dataset_name]
        suggestions = []
        
        search_lower = search_term.lower()
        
        for class_name in metadata["classes"]:
            if search_lower in class_name.lower():
                suggestions.append(class_name)
        
        return sorted(suggestions)[:10]

# Global instance
gemini_search = GeminiDatasetSearch()