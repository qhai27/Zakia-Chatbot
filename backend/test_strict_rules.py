"""
Test script for STRICT ZAKAT MODE implementation
Tests all strict rules enforcement
"""

import sys
sys.path.insert(0, 'D:\\Zakia Chatbot\\backend')

from nlp_processor import NLPProcessor

def test_zakat_classification():
    """Test ZAKAT PENDAPATAN classification"""
    print("=" * 60)
    print("TEST 1: ZAKAT TYPE CLASSIFICATION")
    print("=" * 60)
    
    nlp = NLPProcessor(enable_gemini=False)
    
    test_cases = [
        ("Berapa zakat pendapatan saya jika gaji RM5000 sebulan?", "ZAKAT_PENDAPATAN"),
        ("Saya dapat income RM60000 setahun, berapa zakat?", "ZAKAT_PENDAPATAN"),
        ("Apa nisab zakat emas?", "ZAKAT_EMAS"),
        ("Saya ada 100 gram emas, kena bayar zakat berapa?", "ZAKAT_EMAS"),
        ("Bagaimana kira zakat perniagaan?", "ZAKAT_PERNIAGAAN"),
        ("Zakat fitrah tahun ini berapa?", "ZAKAT_FITRAH"),
        ("Siapa saja yang berhak terima zakat (asnaf)?", "ASNAF"),
    ]
    
    for question, expected_type in test_cases:
        zakat_type = nlp.classify_zakat_type(question)
        status = "✅ PASS" if zakat_type == expected_type else "❌ FAIL"
        print(f"\n{status}")
        print(f"   Q: {question}")
        print(f"   Expected: {expected_type}")
        print(f"   Got: {zakat_type}")

def test_zakat_relevance():
    """Test is_zakat_related check"""
    print("\n" + "=" * 60)
    print("TEST 2: ZAKAT RELEVANCE CHECK")
    print("=" * 60)
    
    nlp = NLPProcessor(enable_gemini=False)
    
    test_cases = [
        ("Berapa zakat pendapatan?", True),
        ("Apa itu nisab?", True),
        ("Hubungi LZNK bagaimana?", True),
        ("Saya nak bayar zakat", True),
        ("Hi, ini siapa?", False),  # Greeting, not question
        ("Apa itu Amanah Hartanah?", False),  # Different institution
        ("Cuaca hari ni macam mana?", False),  # Not related
        ("Siapa pemimpin Malaysia?", False),  # Politics
    ]
    
    for question, expected_related in test_cases:
        is_related = nlp.is_zakat_related(question)
        status = "✅ PASS" if is_related == expected_related else "❌ FAIL"
        print(f"\n{status}")
        print(f"   Q: {question}")
        print(f"   Expected: {expected_related}")
        print(f"   Got: {is_related}")

def test_entity_extraction():
    """Test entity extraction"""
    print("\n" + "=" * 60)
    print("TEST 3: ENTITY EXTRACTION")
    print("=" * 60)
    
    nlp = NLPProcessor(enable_gemini=False)
    
    test_cases = [
        ("Saya nak bayar zakat pendapatan", {"action": "PAYMENT"}),
        ("Bagaimana kira zakat emas?", {"action": "CALCULATION"}),
        ("Apa itu nisab?", {"action": "DEFINITION"}),
        ("Hubungi LZNK bagaimana?", {"action": "CONTACT"}),
    ]
    
    for question, expected_entities in test_cases:
        entities = nlp.extract_entities(question)
        print(f"\nQ: {question}")
        print(f"   Entities extracted:")
        for key, value in entities.items():
            if value and value != 'UNKNOWN' and value is not None:
                print(f"      {key}: {value}")
        if expected_entities:
            for key, expected_val in expected_entities.items():
                actual = entities.get(key)
                if expected_val == actual:
                    print(f"   ✅ {key}: {expected_val}")
                else:
                    print(f"   ❌ {key}: expected {expected_val}, got {actual}")

def test_answer_relevance():
    """Test answer relevance validation"""
    print("\n" + "=" * 60)
    print("TEST 4: ANSWER RELEVANCE VALIDATION")
    print("=" * 60)
    
    nlp = NLPProcessor(enable_gemini=False)
    
    test_cases = [
        {
            "question": "Berapa zakat pendapatan?",
            "answer": "Zakat pendapatan ialah 2.5% dari pendapatan bersih",
            "zakat_type": "ZAKAT_PENDAPATAN",
            "expected": True,
            "reason": "Matching type and content"
        },
        {
            "question": "Berapa zakat pendapatan?",
            "answer": "Zakat emas adalah 2.5% dari nilai emas. Nisab emas adalah 85 gram.",
            "zakat_type": "ZAKAT_PENDAPATAN",
            "expected": False,
            "reason": "Answer is about EMAS, not PENDAPATAN"
        },
        {
            "question": "Apa itu nisab?",
            "answer": "Nisab adalah jumlah harta minimum yang wajib dikenakan zakat",
            "zakat_type": "UNKNOWN",
            "expected": True,
            "reason": "Generic definition, no type conflict"
        },
    ]
    
    for test in test_cases:
        is_valid = nlp.validate_answer_relevance(
            test["question"],
            test["answer"],
            zakat_type=test["zakat_type"]
        )
        status = "✅ PASS" if is_valid == test["expected"] else "❌ FAIL"
        print(f"\n{status} - {test['reason']}")
        print(f"   Q: {test['question']}")
        print(f"   A: {test['answer'][:60]}...")
        print(f"   Type: {test['zakat_type']}")
        print(f"   Expected: {test['expected']}, Got: {is_valid}")

def test_intent_analysis():
    """Test full intent analysis"""
    print("\n" + "=" * 60)
    print("TEST 5: FULL INTENT ANALYSIS")
    print("=" * 60)
    
    nlp = NLPProcessor(enable_gemini=False)
    
    test_cases = [
        "Saya dapat gaji RM5000 sebulan, berapa zakat?",
        "Apa itu haul?",
        "Hubungi LZNK mana?",
        "Assalamualaikum",
        "Terima kasih!",
    ]
    
    for question in test_cases:
        intent = nlp.analyze_user_intent(question)
        print(f"\nQ: {question}")
        print(f"   Intent details:")
        print(f"      Is Question: {intent.get('is_question')}")
        print(f"      Is Greeting: {intent.get('is_greeting')}")
        print(f"      Is Thanks: {intent.get('is_thanks')}")
        print(f"      Is Goodbye: {intent.get('is_goodbye')}")
        print(f"      Is Zakat Related: {intent.get('is_zakat_related')}")
        print(f"      Zakat Type: {intent.get('zakat_type')}")
        print(f"      Language: {intent.get('language')}")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "STRICT ZAKAT MODE - IMPLEMENTATION TEST" + " " * 8 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        test_zakat_classification()
        test_zakat_relevance()
        test_entity_extraction()
        test_answer_relevance()
        test_intent_analysis()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
