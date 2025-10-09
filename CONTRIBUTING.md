# Contributing to Harvest Experiment Analysis Library

## 🚀 Getting Started

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/unified_hex_harvest.git
cd unified_hex_harvest
```

### 2. Install for Development
```bash
pip install -e .
pip install -r requirements.txt
```

### 3. Set Up Local Secrets
```bash
cp local_secrets.py local_secrets_actual.py
# Edit local_secrets_actual.py with your actual credentials
```

## 🔄 Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Add new metrics in `core/metrics.py`
   - Add new queries in `utils/data_queries.py`
   - Update configuration in `core/config.py`

3. **Test your changes**:
   ```bash
   # Test locally
   python examples/simple_experiment.py
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add new metric: YourMetricName"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

### Code Standards

- Use **descriptive variable names**
- Add **docstrings** to all functions and classes
- Follow **PEP 8** style guidelines
- Test your changes before submitting

## 📦 Adding New Metrics

### 1. Add Query Function
In `utils/data_queries.py`:
```python
@staticmethod
def get_your_new_metric(start_date: str, end_date: str) -> Query:
    """Get your new metric query."""
    return (
        Query()
        .select(...)
        .from_("your_table")
        .where(f"date >= '{start_date}' AND date <= '{end_date}'")
    )
```

### 2. Add Metric Definition
In `core/metrics.py`:
```python
def get_your_new_metric(self) -> Metric:
    """Get your new metric."""
    return Metric(
        name='YourMetricName',
        metric=[CustomCountMetric(
            target_query=self._data_queries.get_your_new_metric(
                self.start_date, self.end_date
            ), 
            estimator='cumulated'
        )]
    )
```

### 3. Add to Metric Map
In `core/metrics.py`, add to the `get_metric_by_name` method:
```python
metric_map = {
    # ... existing metrics ...
    'YourMetricName': self.get_your_new_metric(),
}
```

## 🧪 Testing

### Local Testing
```bash
# Test with simple experiment
python examples/simple_experiment.py

# Test with advanced experiment
python examples/advanced_experiment.py
```

### Hex Testing
1. Create a test Hex notebook
2. Use the template with your changes
3. Verify all metrics work correctly

## 📋 Release Process

### Version Bumping
Update version in:
- `setup.py`
- `__init__.py`

### Release Steps
1. Update version numbers
2. Update `CHANGELOG.md`
3. Create a release tag
4. GitHub Actions will handle the rest

## 🤝 Team Collaboration

### Code Reviews
- All changes require a pull request
- At least one team member must approve
- Test the changes in Hex before merging

### Communication
- Use GitHub Issues for bugs and feature requests
- Use Pull Request comments for code discussions
- Tag team members when you need their input

## 🐛 Bug Reports

When reporting bugs, include:
1. **Hex notebook code** that reproduces the issue
2. **Error message** (full traceback)
3. **Expected behavior** vs actual behavior
4. **Environment details** (Hex version, Python version)

## 💡 Feature Requests

When requesting features:
1. **Describe the use case** - why do you need this?
2. **Provide examples** - how would it be used?
3. **Consider alternatives** - is there another way to achieve this?

## 📚 Documentation

- Update `README.md` for major changes
- Add docstrings for all new functions
- Update examples when adding new features
- Keep the template up to date
