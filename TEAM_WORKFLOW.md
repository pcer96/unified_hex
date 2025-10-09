# Team Workflow Guide

## 🏗️ **Repository Setup**

### 1. Create GitHub Repository
```bash
# Create a new repository on GitHub
# Name: unified_hex_harvest
# Description: Centralized experiment analysis library for Hex notebooks
# Make it private (recommended for internal use)
```

### 2. Push Your Code
```bash
git init
git add .
git commit -m "Initial commit: Centralized experiment analysis library"
git branch -M main
git remote add origin https://github.com/your-org/unified_hex_harvest.git
git push -u origin main
```

## 👥 **Team Onboarding**

### For New Team Members

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/unified_hex_harvest.git
   cd unified_hex_harvest
   ```

2. **Install the library**:
   ```bash
   ./install.sh
   ```

3. **Set up local secrets** (for development):
   ```bash
   cp local_secrets.py local_secrets_actual.py
   # Fill in your actual credentials
   ```

4. **Test the setup**:
   ```bash
   python examples/simple_experiment.py
   ```

## 🔄 **Daily Workflow**

### For New Experiments

1. **Create a new Hex notebook**
2. **Copy the template**:
   ```python
   # Copy hex_notebook_template.py content
   ```
3. **Modify experiment parameters**:
   ```python
   experiment_name = 'your_new_experiment'
   start_date = '2025-01-01'
   end_date = '2025-01-31'
   experiment_segments = ['control', 'treatment']
   ```
4. **Run the analysis**

### For Library Updates

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/new-metric
   ```

2. **Make your changes**:
   - Add new metrics in `core/metrics.py`
   - Add new queries in `utils/data_queries.py`
   - Update documentation

3. **Test your changes**:
   ```bash
   python examples/simple_experiment.py
   ```

4. **Create a Pull Request**:
   - Describe what you changed
   - Tag team members for review
   - Test in Hex before merging

5. **Merge and deploy**:
   - After approval, merge to main
   - All team members get updates automatically

## 📦 **Hex Integration**

### Installing in Hex

#### Option 1: Direct Git Install (Recommended)
```python
# In your Hex notebook
! pip install git+https://github.com/your-org/unified_hex_harvest.git
```

#### Option 2: Local Development
```python
# For testing changes locally
! pip install -e /path/to/unified_hex_harvest
```

### Using in Hex Notebooks

```python
# Standard import
from unified_hex_harvest import ExperimentAnalyzer, create_experiment_config, setup_credentials

# Setup credentials (uses Hex secrets automatically)
setup_credentials(use_hex_secrets=True)

# Configure experiment
config = create_experiment_config(
    experiment_name='my_experiment',
    start_date='2025-01-01',
    end_date='2025-01-31',
    experiment_segments=['control', 'treatment']
)

# Run analysis
analyzer = ExperimentAnalyzer(config)
analyzer.run_full_analysis()
```

## 🔧 **Maintenance Workflow**

### Weekly Maintenance

1. **Review open issues** on GitHub
2. **Check for dependency updates**
3. **Test the library** with recent experiments
4. **Update documentation** if needed

### Monthly Maintenance

1. **Review and merge** pending pull requests
2. **Update version numbers** if needed
3. **Create release tags** for major updates
4. **Team retrospective** on library usage

### Quarterly Maintenance

1. **Major feature planning**
2. **Dependency updates**
3. **Performance optimization**
4. **Documentation overhaul**

## 🚀 **Deployment Strategy**

### Development Branch
- `develop` branch for ongoing work
- All new features go here first
- Team members can test from this branch

### Production Branch
- `main` branch for stable releases
- Only tested, reviewed code goes here
- This is what the team uses in production

### Release Process
1. **Feature complete** on develop branch
2. **Testing** in Hex notebooks
3. **Code review** and approval
4. **Merge to main**
5. **Create release tag**
6. **Team notification** of new version

## 📊 **Version Management**

### Semantic Versioning
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Version Updates
```python
# In setup.py and __init__.py
__version__ = "1.2.3"
```

## 🔐 **Security Best Practices**

### Secrets Management
- ✅ **Use Hex secrets** for production
- ✅ **Never commit** actual credentials
- ✅ **Use .gitignore** for local secrets
- ✅ **Rotate credentials** regularly

### Code Security
- ✅ **Private repository** for internal use
- ✅ **Code reviews** for all changes
- ✅ **Dependency scanning** in CI/CD
- ✅ **Regular security updates**

## 📈 **Monitoring and Metrics**

### Usage Tracking
- Monitor which experiments use the library
- Track common configuration patterns
- Identify frequently requested features

### Performance Monitoring
- Query execution times
- Memory usage in Hex
- Error rates and common issues

## 🆘 **Support and Troubleshooting**

### Getting Help
1. **Check the README** first
2. **Search existing issues** on GitHub
3. **Create a new issue** with details
4. **Tag team members** for urgent issues

### Common Issues
- **Import errors**: Check library installation
- **Query errors**: Verify experiment configuration
- **Credential errors**: Check Hex secrets setup

## 🎯 **Success Metrics**

### Team Adoption
- Number of team members using the library
- Number of experiments analyzed with the library
- Reduction in code duplication

### Quality Metrics
- Bug reports per month
- Time to analyze new experiments
- Team satisfaction scores

## 🔮 **Future Roadmap**

### Short Term (1-3 months)
- Statistical significance testing
- Automated report generation
- Performance optimizations

### Medium Term (3-6 months)
- A/B test power analysis
- Integration with experiment tracking
- Custom visualization templates

### Long Term (6+ months)
- Machine learning insights
- Automated experiment recommendations
- Advanced statistical methods
