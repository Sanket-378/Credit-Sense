import chromadb
import os
from typing import List, Dict
import json

class VectorDBService:
    def __init__(self):
        # Initialize ChromaDB with persistent storage (new API)
        self.client = chromadb.PersistentClient(path="./chroma_db")
    
    def get_user_collection(self, user_id: str):
        """Get or create a collection for a specific user"""
        collection_name = f"user_{user_id}_financial_data"
        try:
            collection = self.client.get_collection(name=collection_name)
        except:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"user_id": user_id}
            )
        return collection
    
    def add_user_financial_data(self, user_id: str, document_id: int, financial_data: Dict):
        """Add user's financial data to their vector collection"""
        collection = self.get_user_collection(user_id)
        
        # Create a text representation of financial data
        text_data = self._create_financial_text(financial_data)
        
        # Add to vector database
        collection.add(
            documents=[text_data],
            metadatas=[{
                "document_id": str(document_id),
                "user_id": user_id,
                **{k: str(v) for k, v in financial_data.items() if v}
            }],
            ids=[f"doc_{document_id}_{user_id}"]
        )
        
        print(f"Added financial data to vector DB for user {user_id}, document {document_id}")
    
    def _create_financial_text(self, data: Dict) -> str:
        """Convert financial data to searchable text"""
        text_parts = []
        
        if data.get('person_name'):
            text_parts.append(f"Person: {data['person_name']}")
        if data.get('company_name'):
            text_parts.append(f"Works at: {data['company_name']}")
        if data.get('job_role'):
            text_parts.append(f"Job: {data['job_role']}")
        if data.get('salary'):
            text_parts.append(f"Salary: {data['salary']}")
        if data.get('tax_payable'):
            text_parts.append(f"Tax: {data['tax_payable']}")
        if data.get('bank_account_number'):
            text_parts.append(f"Has bank account")
        if data.get('pan_card_number'):
            text_parts.append(f"PAN: {data['pan_card_number']}")
        if data.get('address'):
            text_parts.append(f"Address: {data['address']}")
        if data.get('document_type'):
            text_parts.append(f"Document: {data['document_type']}")
            
        return " | ".join(text_parts)
    
    def get_user_profile(self, user_id: str) -> Dict:
        """Retrieve all financial data for a user"""
        collection = self.get_user_collection(user_id)
        
        try:
            results = collection.get()
            
            # Aggregate user data
            profile = {
                "total_documents": len(results['ids']),
                "financial_data": [],
                "person_name": "",
                "salary": "",
                "company_name": "",
                "job_role": "",
                "address": ""
            }
            
            for metadata in results['metadatas']:
                profile['financial_data'].append(metadata)
                # Use the most recent data
                if metadata.get('person_name') and not profile['person_name']:
                    profile['person_name'] = metadata['person_name']
                if metadata.get('salary') and not profile['salary']:
                    profile['salary'] = metadata['salary']
                if metadata.get('company_name') and not profile['company_name']:
                    profile['company_name'] = metadata['company_name']
                if metadata.get('job_role') and not profile['job_role']:
                    profile['job_role'] = metadata['job_role']
                if metadata.get('address') and not profile['address']:
                    profile['address'] = metadata['address']
            
            return profile
        except:
            return {
                "total_documents": 0,
                "financial_data": [],
                "person_name": "",
                "salary": "",
                "company_name": "",
                "job_role": "",
                "address": ""
            }
    
    def search_similar_schemes(self, user_id: str, query: str, n_results: int = 5):
        """Search for similar financial data based on query"""
        collection = self.get_user_collection(user_id)
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except:
            return None

# Global instance
vector_db = VectorDBService()
