#!/usr/bin/env python3

# Test script to isolate the NameError issue

print("Testing minimal imports...")

try:
    from unified_hex_harvest.core.config import ExperimentConfig
    print("✅ Config import successful")
except Exception as e:
    print(f"❌ Config import failed: {e}")

try:
    from unified_hex_harvest.utils.data_queries import DataQueries
    print("✅ DataQueries import successful")
except Exception as e:
    print(f"❌ DataQueries import failed: {e}")

try:
    from unified_hex_harvest.core.metrics import MetricDefinitions
    print("✅ MetricDefinitions import successful")
except Exception as e:
    print(f"❌ MetricDefinitions import failed: {e}")

try:
    from unified_hex_harvest.core.experiment_analyzer import ExperimentAnalyzer
    print("✅ ExperimentAnalyzer import successful")
except Exception as e:
    print(f"❌ ExperimentAnalyzer import failed: {e}")

print("\nTesting initialization...")

try:
    config = ExperimentConfig('test', '2025-01-01', '2025-01-31', ['control', 'treatment'])
    print("✅ Config creation successful")
except Exception as e:
    print(f"❌ Config creation failed: {e}")

try:
    data_queries = DataQueries()
    print("✅ DataQueries creation successful")
except Exception as e:
    print(f"❌ DataQueries creation failed: {e}")

try:
    metrics = MetricDefinitions('2025-01-01', '2025-01-31')
    print("✅ MetricDefinitions creation successful")
except Exception as e:
    print(f"❌ MetricDefinitions creation failed: {e}")

try:
    analyzer = ExperimentAnalyzer(config)
    print("✅ ExperimentAnalyzer creation successful")
except Exception as e:
    print(f"❌ ExperimentAnalyzer creation failed: {e}")
