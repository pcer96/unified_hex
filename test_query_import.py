#!/usr/bin/env python3

# Test script to verify Query import handling

print("Testing Query import handling...")

try:
    from unified_hex_harvest.utils.data_queries import DataQueries
    print("✅ DataQueries import successful")
    
    # Test the _get_query method
    try:
        query_class = DataQueries._get_query()
        print(f"✅ Query class retrieved: {query_class}")
    except NameError as e:
        print(f"⚠️  Query not available (expected outside Hex): {e}")
    
except Exception as e:
    print(f"❌ Import failed: {e}")

print("\nThis test shows that the package can be imported even when bsp_query_builder is not available.")
print("In Hex, Query will be available through the global namespace.")
