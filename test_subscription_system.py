#!/usr/bin/env python3
"""
Comprehensive test for the subscription system.
"""

def test_template_elements():
    """Test that all required elements are present in the template."""
    template_path = "/home/lee/code/20-questions2/templates/shared/subscribe.jinja2"
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Template file not found")
        return False
    
    required_elements = [
        ('class="subscription-toggle"', 'Subscription toggle checkbox'),
        ('class="money-amount"', 'Money amount display'),
        ('class="subscription-period"', 'Subscription period display'),
        ('class="discount-chip"', 'Discount chip element'),
        ('setupSubscriptionToggle', 'Setup subscription toggle function'),
        ('$(".subscription-toggle").change', 'jQuery change handler'),
        ('updatePricing', 'Update pricing function'),
        ('$(".discount-chip").show()', 'Show discount chip'),
        ('$(".discount-chip").hide()', 'Hide discount chip'),
    ]
    
    print("Testing template elements:")
    print("=" * 60)
    
    all_found = True
    for element, description in required_elements:
        found = element in content
        status = "✅" if found else "❌"
        print(f"{status} {description}")
        if not found:
            all_found = False
    
    return all_found

def test_modal_files():
    """Test that the modal files exist and have correct content."""
    files_to_check = [
        ("/home/lee/code/20-questions2/static/js/subscription-modal.js", [
            "Subscription Required",
            "$19.00",
            "per month",
            "Unlimited AI text generation",
            "AI Text Editor with advanced editing tools",
            "AI Voices & Speech Understanding",
            "linear-gradient(135deg, #FFB6C1 0%, #FFA07A 50%, #FF6347 100%)"
        ]),
        ("/home/lee/code/20-questions2/static/js/checkout-dialog.js", [
            "CheckoutDialog",
            "initStripe",
            "createModal",
            "bindEvents"
        ])
    ]
    
    print("\nTesting modal files:")
    print("=" * 60)
    
    all_files_ok = True
    for file_path, required_content in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            file_ok = True
            for item in required_content:
                if item not in content:
                    print(f"❌ {file_path}: Missing '{item}'")
                    file_ok = False
                    all_files_ok = False
            
            if file_ok:
                print(f"✅ {file_path}: All required content found")
                
        except FileNotFoundError:
            print(f"❌ {file_path}: File not found")
            all_files_ok = False
    
    return all_files_ok

def test_feature_consistency():
    """Test that features are consistent between modal and subscribe page."""
    modal_path = "/home/lee/code/20-questions2/static/js/subscription-modal.js"
    template_path = "/home/lee/code/20-questions2/templates/shared/subscribe.jinja2"
    
    print("\nTesting feature consistency:")
    print("=" * 60)
    
    # Key features that should be mentioned
    key_features = [
        "AI text",
        "AI Text Editor",
        "AI Voices",
        "Speech",
        "code generation",
        "prompt optimization",
        "privacy"
    ]
    
    try:
        with open(modal_path, 'r') as f:
            modal_content = f.read()
        with open(template_path, 'r') as f:
            template_content = f.read()
    except FileNotFoundError:
        print("❌ Could not read files for feature consistency test")
        return False
    
    consistency_ok = True
    for feature in key_features:
        in_modal = feature.lower() in modal_content.lower()
        in_template = feature.lower() in template_content.lower()
        
        if in_modal and in_template:
            print(f"✅ {feature}: Present in both modal and template")
        elif in_modal:
            print(f"⚠️  {feature}: Only in modal")
        elif in_template:
            print(f"⚠️  {feature}: Only in template")
        else:
            print(f"❌ {feature}: Missing from both")
            consistency_ok = False
    
    return consistency_ok

def main():
    """Run all tests."""
    print("🧪 Testing Subscription System")
    print("=" * 60)
    
    template_ok = test_template_elements()
    modal_ok = test_modal_files()
    consistency_ok = test_feature_consistency()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if template_ok:
        print("✅ Template elements: PASS")
    else:
        print("❌ Template elements: FAIL")
    
    if modal_ok:
        print("✅ Modal files: PASS")
    else:
        print("❌ Modal files: FAIL")
    
    if consistency_ok:
        print("✅ Feature consistency: PASS")
    else:
        print("❌ Feature consistency: FAIL")
    
    overall_pass = template_ok and modal_ok and consistency_ok
    
    if overall_pass:
        print("\n🎉 ALL TESTS PASSED!")
        print("The subscription system should now work correctly.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please review the failing tests above.")
    
    return overall_pass

if __name__ == "__main__":
    main()
