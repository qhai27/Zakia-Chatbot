#!/usr/bin/env python3
"""
Complete Training Script for LZNK Chatbot
This script trains the NLP model with FAQ data and tests its performance
"""

import sys
from database import DatabaseManager
from nlp_processor import EnhancedNLPProcessor
import json

class ChatbotTrainer:
    def __init__(self):
        self.db = DatabaseManager()
        self.nlp = EnhancedNLPProcessor()
        self.test_results = []
        
    def load_faq_data(self):
        """Load FAQ data from database"""
        print("📚 Loading FAQ data from database...")
        
        if not self.db.connect():
            print("❌ Failed to connect to database")
            return []
        
        faqs = self.db.get_faqs()
        print(f"✅ Loaded {len(faqs)} FAQs from database")
        
        return faqs
    
    def train_model(self, faqs):
        """Train the NLP model"""
        print("\n🎓 Training NLP model...")
        self.nlp.train_from_faqs(faqs)
        
        # Save training data
        self.nlp.save_training_data('training_data.json')
        print("✅ Model trained and saved!")
    
    def add_more_training_data(self):
        """Add additional training variations"""
        print("\n📝 Adding training variations...")
        
        # Add common question variations
        variations = [
            {
                "question": "Macam mana nak bayar zakat?",
                "answer": "Anda boleh membayar zakat melalui portal rasmi LZNK, kaunter zakat, atau wakil amil yang dilantik.",
                "category": "Pembayaran"
            },
            {
                "question": "Zakat tu apa?",
                "answer": "Zakat ialah kewajipan agama yang dikenakan ke atas umat Islam untuk menunaikan sebahagian harta kepada golongan yang layak menerimanya.",
                "category": "Umum"
            },
            {
                "question": "Bila kena bayar zakat?",
                "answer": "Zakat boleh dibayar bila-bila masa, namun paling digalakkan pada akhir tahun haul atau bulan Ramadan.",
                "category": "Pembayaran"
            },
            {
                "question": "Kat mana pejabat LZNK?",
                "answer": "Pejabat utama LZNK terletak di Alor Setar, Kedah. LZNK juga mempunyai cawangan di seluruh negeri Kedah.",
                "category": "LZNK"
            },
            {
                "question": "Berapa nisab zakat emas?",
                "answer": "Nisab zakat emas ialah 85 gram atau nilai setara dengan 85 gram emas semasa.",
                "category": "Nisab"
            }
        ]
        
        # Insert variations into database
        for var in variations:
            self.db.create_faq(
                question=var['question'],
                answer=var['answer'],
                category=var['category']
            )
        
        print(f"✅ Added {len(variations)} training variations")
    
    def test_natural_language_understanding(self, faqs):
        """Test the model with various natural language inputs"""
        print("\n🧪 Testing Natural Language Understanding...\n")
        
        test_cases = [
            # Formal questions
            "Apa itu zakat?",
            "Bagaimana cara membayar zakat?",
            "Berapakah nisab zakat emas?",
            
            # Informal/casual questions
            "zakat tu apa?",
            "mcm mana nk bayar zakat?",
            "brp nisab emas?",
            
            # With typos
            "ap itu zakat?",
            "bgaimana cara byr zakat?",
            "sipa yg wajib bayar?",
            
            # Different phrasings
            "Boleh terangkan tentang zakat?",
            "Cara nak bayar zakat kat mana?",
            "Berapa gram nisab untuk emas?",
            
            # Questions about LZNK
            "LZNK ni apa?",
            "Pejabat LZNK kat mana?",
            "Apa perkhidmatan LZNK?",
            
            # Mixed language
            "how to bayar zakat?",
            "lznk office where?",
            
            # Very casual
            "nk bayar zakat",
            "nisab brape",
            "lznk dekat mane"
        ]
        
        self.test_results = []
        
        for i, test_input in enumerate(test_cases, 1):
            response = self.nlp.generate_response(test_input, faqs)
            
            self.test_results.append({
                'input': test_input,
                'matched': response.get('matched_question'),
                'confidence': response.get('confidence', 0),
                'confidence_level': response.get('confidence_level', 'none')
            })
            
            print(f"Test {i}: {test_input}")
            print(f"  ├─ Matched: {response.get('matched_question', 'No match')}")
            print(f"  ├─ Confidence: {response.get('confidence', 0):.2f} ({response.get('confidence_level', 'none')})")
            print(f"  └─ Answer: {response['reply'][:80]}...")
            print()
    
    def generate_performance_report(self):
        """Generate performance statistics"""
        print("\n📊 Performance Report")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        high_confidence = sum(1 for r in self.test_results if r['confidence'] >= 0.7)
        medium_confidence = sum(1 for r in self.test_results if 0.5 <= r['confidence'] < 0.7)
        low_confidence = sum(1 for r in self.test_results if 0.35 <= r['confidence'] < 0.5)
        no_match = sum(1 for r in self.test_results if r['confidence'] < 0.35)
        
        print(f"Total Tests: {total_tests}")
        print(f"High Confidence (≥0.7): {high_confidence} ({high_confidence/total_tests*100:.1f}%)")
        print(f"Medium Confidence (0.5-0.7): {medium_confidence} ({medium_confidence/total_tests*100:.1f}%)")
        print(f"Low Confidence (0.35-0.5): {low_confidence} ({low_confidence/total_tests*100:.1f}%)")
        print(f"No Match (<0.35): {no_match} ({no_match/total_tests*100:.1f}%)")
        
        avg_confidence = sum(r['confidence'] for r in self.test_results) / total_tests
        print(f"\nAverage Confidence: {avg_confidence:.3f}")
        print("=" * 60)
    
    def save_test_report(self, filename='test_report.json'):
        """Save test results to file"""
        report = {
            'total_tests': len(self.test_results),
            'results': self.test_results,
            'summary': {
                'high_confidence': sum(1 for r in self.test_results if r['confidence'] >= 0.7),
                'medium_confidence': sum(1 for r in self.test_results if 0.5 <= r['confidence'] < 0.7),
                'low_confidence': sum(1 for r in self.test_results if 0.35 <= r['confidence'] < 0.5),
                'no_match': sum(1 for r in self.test_results if r['confidence'] < 0.35),
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Test report saved to {filename}")
    
    def run_complete_training(self):
        """Run the complete training pipeline"""
        print("=" * 60)
        print("🚀 LZNK Chatbot Training Pipeline")
        print("=" * 60)
        
        # Step 1: Load FAQ data
        faqs = self.load_faq_data()
        if not faqs:
            print("❌ No FAQ data available. Please run init_db.py first.")
            return False
        
        # Step 2: Add training variations
        self.add_more_training_data()
        
        # Step 3: Reload FAQs with new data
        faqs = self.load_faq_data()
        
        # Step 4: Train the model
        self.train_model(faqs)
        
        # Step 5: Test natural language understanding
        self.test_natural_language_understanding(faqs)
        
        # Step 6: Generate report
        self.generate_performance_report()
        
        # Step 7: Save report
        self.save_test_report()
        
        print("\n" + "=" * 60)
        print("✅ Training Complete!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("1. Review the test_report.json file")
        print("2. Update app.py to use EnhancedNLPProcessor")
        print("3. Test the chatbot with real users")
        print("4. Collect feedback and retrain as needed")
        
        return True

def main():
    """Main training function"""
    trainer = ChatbotTrainer()
    
    try:
        success = trainer.run_complete_training()
        
        if success:
            print("\n🎉 Training pipeline completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Training pipeline failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()