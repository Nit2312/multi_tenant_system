"""
System Evaluation Script
This script evaluates the RAG system's performance by testing various query types
and analyzing response quality, accuracy, and grounding in source documents.
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
import statistics


class SystemEvaluator:
    """Evaluates the RAG system's performance"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.results = []
        
    def test_queries(self) -> List[Dict[str, Any]]:
        """Define test queries across different categories"""
        return [
            # Finance queries
            {
                "query": "What is the margin of safety principle?",
                "category": "finance",
                "expected_topics": ["margin of safety", "benjamin graham", "value investing", "intrinsic value"],
                "complexity": "basic"
            },
            {
                "query": "Explain Warren Buffett's investment philosophy",
                "category": "finance",
                "expected_topics": ["warren buffett", "value investing", "long term", "business quality"],
                "complexity": "intermediate"
            },
            {
                "query": "How should I diversify my portfolio?",
                "category": "finance",
                "expected_topics": ["diversification", "risk", "portfolio", "assets"],
                "complexity": "intermediate"
            },
            {
                "query": "What is compound interest and why is it important?",
                "category": "finance",
                "expected_topics": ["compound interest", "compounding", "growth", "time"],
                "complexity": "basic"
            },
            {
                "query": "Compare value investing vs growth investing approaches",
                "category": "finance",
                "expected_topics": ["value investing", "growth", "compare", "strategy"],
                "complexity": "advanced"
            },
            # Marketing queries
            {
                "query": "What are effective marketing strategies?",
                "category": "marketing",
                "expected_topics": ["marketing", "strategy", "customer", "brand"],
                "complexity": "intermediate"
            },
            {
                "query": "How do I build a strong brand?",
                "category": "marketing",
                "expected_topics": ["brand", "branding", "identity", "customer"],
                "complexity": "intermediate"
            },
            # Edge cases
            {
                "query": "Tell me about stocks",
                "category": "finance",
                "expected_topics": ["stock", "equity", "market", "share"],
                "complexity": "basic"
            },
            {
                "query": "What should I do to become rich?",
                "category": "finance",
                "expected_topics": ["wealth", "investing", "financial", "money"],
                "complexity": "intermediate"
            },
            {
                "query": "Which books should I read about investing?",
                "category": "finance",
                "expected_topics": ["book", "read", "investing", "learn"],
                "complexity": "basic"
            }
        ]
    
    def initialize_system(self) -> bool:
        """Initialize the RAG system"""
        try:
            response = requests.post(f"{self.base_url}/api/initialize", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ System initialized: {data.get('message', '')}")
                return data.get('success', False)
            else:
                print(f"✗ Failed to initialize system: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error initializing system: {e}")
            return False
    
    def send_query(self, query: str) -> Dict[str, Any]:
        """Send a query to the system and get response"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": query},
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                data['response_time'] = elapsed_time
                return data
            else:
                return {
                    "error": f"HTTP {response.status_code}",
                    "response_time": elapsed_time
                }
        except Exception as e:
            return {
                "error": str(e),
                "response_time": 0
            }
    
    def evaluate_response(self, query_data: Dict[str, Any], response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single response"""
        evaluation = {
            "query": query_data["query"],
            "category": query_data["category"],
            "complexity": query_data["complexity"],
            "response_time": response_data.get("response_time", 0),
            "success": "error" not in response_data,
            "scores": {}
        }
        
        if "error" in response_data:
            evaluation["error"] = response_data["error"]
            evaluation["scores"]["overall"] = 0
            return evaluation
        
        response_text = response_data.get("response", "").lower()
        sources = response_data.get("sources", [])
        metrics = response_data.get("retrieval_metrics", {})
        
        # 1. Source Retrieval Score (0-1)
        source_score = min(metrics.get("retrieved", 0) / 5, 1.0)  # Normalize to max 5
        evaluation["scores"]["source_retrieval"] = round(source_score, 2)
        
        # 2. Source Citation Score (0-1)
        citation_score = metrics.get("precision_at_k", 0)
        evaluation["scores"]["source_citation"] = round(citation_score, 2)
        
        # 3. Relevance Score (0-1) - Check if expected topics are mentioned
        expected_topics = query_data.get("expected_topics", [])
        topics_found = sum(1 for topic in expected_topics if topic.lower() in response_text)
        relevance_score = topics_found / len(expected_topics) if expected_topics else 0.5
        evaluation["scores"]["relevance"] = round(relevance_score, 2)
        
        # 4. Response Quality Score (0-1)
        response_length = len(response_data.get("response", ""))
        # Good responses are typically 200-800 characters
        if response_length < 100:
            quality_score = 0.3
        elif response_length < 200:
            quality_score = 0.6
        elif response_length < 800:
            quality_score = 1.0
        else:
            quality_score = 0.8  # Penalize overly long responses
        evaluation["scores"]["response_quality"] = round(quality_score, 2)
        
        # 5. Grounding Score (0-1) - Check if response references sources
        grounding_indicators = [
            "according to", "based on", "the document", "the book",
            "the author", "as mentioned", "states that", "explains that"
        ]
        grounding_count = sum(1 for indicator in grounding_indicators if indicator in response_text)
        grounding_score = min(grounding_count / 3, 1.0)  # Expect at least 3 indicators
        evaluation["scores"]["grounding"] = round(grounding_score, 2)
        
        # 6. Conversational Tone Score (0-1)
        # Check for mentor-like tone
        conversational_indicators = [
            "you", "your", "should", "can", "will", "focus on",
            "remember", "important", "consider", "think about"
        ]
        tone_count = sum(1 for indicator in conversational_indicators if indicator in response_text)
        tone_score = min(tone_count / 5, 1.0)
        evaluation["scores"]["conversational_tone"] = round(tone_score, 2)
        
        # Calculate overall score (weighted average)
        weights = {
            "source_retrieval": 0.20,
            "source_citation": 0.15,
            "relevance": 0.25,
            "response_quality": 0.15,
            "grounding": 0.15,
            "conversational_tone": 0.10
        }
        
        overall_score = sum(
            evaluation["scores"][key] * weights[key]
            for key in weights.keys()
        )
        evaluation["scores"]["overall"] = round(overall_score, 2)
        
        # Store metrics
        evaluation["metrics"] = metrics
        evaluation["response_length"] = response_length
        evaluation["sources_count"] = len(sources)
        
        return evaluation
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Run complete evaluation"""
        print("=" * 80)
        print("Starting System Evaluation")
        print("=" * 80)
        print()
        
        # Initialize system
        if not self.initialize_system():
            return {"error": "Failed to initialize system"}
        
        print()
        test_queries = self.test_queries()
        
        print(f"Running {len(test_queries)} test queries...")
        print()
        
        # Run all queries
        for i, query_data in enumerate(test_queries, 1):
            print(f"[{i}/{len(test_queries)}] Testing: {query_data['query'][:60]}...")
            
            response_data = self.send_query(query_data["query"])
            evaluation = self.evaluate_response(query_data, response_data)
            self.results.append(evaluation)
            
            # Print result
            if evaluation["success"]:
                print(f"    ✓ Overall Score: {evaluation['scores']['overall']:.2f}")
                print(f"    Response Time: {evaluation['response_time']:.2f}s")
            else:
                print(f"    ✗ Error: {evaluation.get('error', 'Unknown error')}")
            print()
            
            # Brief delay to avoid overwhelming the system
            time.sleep(0.5)
        
        # Calculate statistics
        summary = self.generate_summary()
        return summary
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate evaluation summary"""
        successful_results = [r for r in self.results if r["success"]]
        
        if not successful_results:
            return {
                "error": "No successful queries",
                "total_queries": len(self.results),
                "successful_queries": 0
            }
        
        # Calculate averages
        overall_scores = [r["scores"]["overall"] for r in successful_results]
        response_times = [r["response_time"] for r in successful_results]
        
        # Calculate scores by category
        score_by_metric = {}
        for metric in ["source_retrieval", "source_citation", "relevance", 
                       "response_quality", "grounding", "conversational_tone"]:
            scores = [r["scores"][metric] for r in successful_results]
            score_by_metric[metric] = {
                "mean": round(statistics.mean(scores), 2),
                "median": round(statistics.median(scores), 2),
                "min": round(min(scores), 2),
                "max": round(max(scores), 2)
            }
        
        # Categorize by complexity
        complexity_scores = {}
        for complexity in ["basic", "intermediate", "advanced"]:
            complexity_results = [r for r in successful_results if r["complexity"] == complexity]
            if complexity_results:
                scores = [r["scores"]["overall"] for r in complexity_results]
                complexity_scores[complexity] = round(statistics.mean(scores), 2)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(self.results),
            "successful_queries": len(successful_results),
            "failed_queries": len(self.results) - len(successful_results),
            "overall_score": {
                "mean": round(statistics.mean(overall_scores), 2),
                "median": round(statistics.median(overall_scores), 2),
                "min": round(min(overall_scores), 2),
                "max": round(max(overall_scores), 2),
                "stdev": round(statistics.stdev(overall_scores), 2) if len(overall_scores) > 1 else 0
            },
            "performance": {
                "mean_response_time": round(statistics.mean(response_times), 2),
                "median_response_time": round(statistics.median(response_times), 2),
                "min_response_time": round(min(response_times), 2),
                "max_response_time": round(max(response_times), 2)
            },
            "scores_by_metric": score_by_metric,
            "scores_by_complexity": complexity_scores,
            "detailed_results": self.results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary"""
        print("=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print()
        
        if "error" in summary:
            print(f"Error: {summary['error']}")
            return
        
        # Overall Statistics
        print("Overall Statistics:")
        print(f"  Total Queries: {summary['total_queries']}")
        print(f"  Successful: {summary['successful_queries']}")
        print(f"  Failed: {summary['failed_queries']}")
        print(f"  Success Rate: {summary['successful_queries'] / summary['total_queries'] * 100:.1f}%")
        print()
        
        # Overall Score
        print("Overall Score:")
        print(f"  Mean: {summary['overall_score']['mean']:.2f}")
        print(f"  Median: {summary['overall_score']['median']:.2f}")
        print(f"  Range: {summary['overall_score']['min']:.2f} - {summary['overall_score']['max']:.2f}")
        print(f"  Std Dev: {summary['overall_score']['stdev']:.2f}")
        print()
        
        # Performance
        print("Performance:")
        print(f"  Mean Response Time: {summary['performance']['mean_response_time']:.2f}s")
        print(f"  Median Response Time: {summary['performance']['median_response_time']:.2f}s")
        print(f"  Range: {summary['performance']['min_response_time']:.2f}s - {summary['performance']['max_response_time']:.2f}s")
        print()
        
        # Scores by Metric
        print("Scores by Metric:")
        for metric, scores in summary['scores_by_metric'].items():
            metric_name = metric.replace('_', ' ').title()
            print(f"  {metric_name}:")
            print(f"    Mean: {scores['mean']:.2f}, Median: {scores['median']:.2f}, Range: {scores['min']:.2f}-{scores['max']:.2f}")
        print()
        
        # Scores by Complexity
        if summary['scores_by_complexity']:
            print("Scores by Complexity:")
            for complexity, score in summary['scores_by_complexity'].items():
                print(f"  {complexity.title()}: {score:.2f}")
            print()
        
        # Grade
        mean_score = summary['overall_score']['mean']
        if mean_score >= 0.9:
            grade = "A (Excellent)"
        elif mean_score >= 0.8:
            grade = "B (Good)"
        elif mean_score >= 0.7:
            grade = "C (Satisfactory)"
        elif mean_score >= 0.6:
            grade = "D (Needs Improvement)"
        else:
            grade = "F (Poor)"
        
        print(f"Overall Grade: {grade}")
        print()
        
        # Recommendations
        print("Recommendations:")
        scores = summary['scores_by_metric']
        if scores['source_retrieval']['mean'] < 0.7:
            print("  - Improve document retrieval relevance")
        if scores['source_citation']['mean'] < 0.7:
            print("  - Enhance source citation in responses")
        if scores['relevance']['mean'] < 0.7:
            print("  - Improve topic coverage in responses")
        if scores['grounding']['mean'] < 0.7:
            print("  - Better ground responses in source documents")
        if scores['conversational_tone']['mean'] < 0.7:
            print("  - Improve conversational tone")
        if all(metric['mean'] >= 0.7 for metric in scores.values()):
            print("  - System is performing well! Keep monitoring.")
        print()
    
    def save_results(self, filename: str = "evaluation_results.json"):
        """Save detailed results to JSON file"""
        summary = self.generate_summary()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Detailed results saved to: {filename}")


def main():
    """Main evaluation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate RAG System Performance")
    parser.add_argument(
        "--url",
        default="http://localhost:5001",
        help="Base URL of the system (default: http://localhost:5001)"
    )
    parser.add_argument(
        "--output",
        default="evaluation_results.json",
        help="Output file for detailed results (default: evaluation_results.json)"
    )
    
    args = parser.parse_args()
    
    evaluator = SystemEvaluator(base_url=args.url)
    
    try:
        summary = evaluator.run_evaluation()
        evaluator.print_summary(summary)
        evaluator.save_results(args.output)
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
    except Exception as e:
        print(f"\n\nEvaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
