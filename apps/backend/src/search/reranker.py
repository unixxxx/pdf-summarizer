"""Sentence transformer based reranker for fast, high-quality reranking."""

import logging

from sentence_transformers import SentenceTransformer, util

from .schemas import SearchResult

logger = logging.getLogger(__name__)


class SentenceTransformerReranker:
    """Rerank search results using sentence transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize reranker with sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use.
                       Default is 'all-MiniLM-L6-v2' which is fast and efficient.
        """
        self.model_name = model_name
        self._model = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of the model."""
        if not self._initialized:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._initialized = True
                logger.info(f"Successfully loaded model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {self.model_name}: {e}")
                raise
    
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        max_results: int = 20,
        min_similarity: float = 0.3
    ) -> list[SearchResult]:
        """
        Rerank search results based on semantic similarity to query.
        
        Args:
            query: The search query
            results: List of search results to rerank
            max_results: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Reranked list of search results
        """
        if not results:
            return []
        
        # Initialize model if needed
        self._initialize()
        
        # Limit input to prevent memory issues
        input_results = results[:100]
        
        try:
            # Encode query
            query_embedding = self._model.encode(query, convert_to_tensor=True)
            
            # Prepare texts for encoding
            # Use snippet as the primary text, fallback to filename
            texts = []
            for result in input_results:
                if result.snippet and len(result.snippet) > 20:
                    texts.append(result.snippet)
                else:
                    # Combine filename with any available text
                    text = result.filename
                    if result.title:
                        text = f"{result.title} - {text}"
                    texts.append(text)
            
            # Encode all texts
            text_embeddings = self._model.encode(texts, convert_to_tensor=True)
            
            # Calculate similarities
            similarities = util.cos_sim(query_embedding, text_embeddings)[0]
            
            # Create scored results
            scored_results = []
            for _i, (result, similarity) in enumerate(zip(input_results, similarities, strict=False)):
                sim_score = float(similarity)
                
                # Skip results below minimum similarity
                if sim_score < min_similarity:
                    continue
                
                # Update result with rerank score
                result.rerank_score = sim_score
                
                # Calculate combined score
                # Weight original score and rerank score
                original_weight = 0.4
                rerank_weight = 0.6
                
                original_score = result.relevance_score
                combined_score = (
                    original_weight * original_score +
                    rerank_weight * sim_score
                )
                
                # Update relevance score with combined score
                result.relevance_score = combined_score
                
                # Add explanation
                result.explanation = (
                    f"Reranked with similarity score: {sim_score:.3f} "
                    f"(original: {original_score:.3f})"
                )
                
                scored_results.append((combined_score, result))
            
            # Sort by combined score
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Return top results
            return [result for _, result in scored_results[:max_results]]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Return original results if reranking fails
            return results[:max_results]
    
    def preload_model(self):
        """Preload the model for faster first query."""
        self._initialize()