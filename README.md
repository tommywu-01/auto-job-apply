# 🤖 Auto Job Apply - AI-Powered Job Application Automation

An intelligent, fully automated job application system that uses AI vision and adaptive selectors to apply to jobs across LinkedIn, Greenhouse, Lever, and Workday with zero human intervention.

## ✨ Features

- 🔍 **AI Vision Analysis** - Automatically identifies form fields using screenshot analysis
- 🧠 **Adaptive Selectors** - Smart element detection that works across different ATS platforms
- 📄 **Resume Auto-Upload** - Intelligent resume matching and upload
- 🎯 **Multi-Platform Support** - LinkedIn Easy Apply, Greenhouse, Lever, Workday
- 📝 **Dynamic Form Filling** - Automatically answers custom questions using AI
- 📊 **Application Tracking** - Logs and screenshots for every application
- 🔒 **Human-Like Behavior** - Random delays and realistic interaction patterns

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/tommywu/auto-job-apply.git
cd auto-job-apply
pip install -r requirements.txt

# Configure your profile
cp config/profile.example.yaml config/profile.yaml
# Edit config/profile.yaml with your information

# Run automated application
python3 auto_apply_all.py --target-jobs 5
```

## 📁 Project Structure

```
auto-job-apply/
├── auto_apply_all.py              # Main automation script
├── linkedin_easy_apply_fixed.py   # LinkedIn Easy Apply automation
├── greenhouse_auto_apply_fixed.py # Greenhouse/Lever automation
├── workday_auto_apply_fixed.py    # Workday automation
├── ai_form_filler.py              # AI-powered form filling
├── page_analyzer.py               # Page structure analyzer
├── adaptive_selector.py           # Smart element selector
├── resume_uploader.py             # Intelligent resume upload
├── config/
│   ├── profile.yaml               # Your personal information
│   ├── answers.json               # Common Q&A database
│   └── job_targets.json           # Target companies and positions
├── logs/                          # Application logs
├── screenshots/                   # Debug screenshots
└── test_reports/                  # Test results
```

## 🔧 Configuration

### Personal Information (`config/profile.yaml`)

```yaml
personal_info:
  first_name: "Your Name"
  last_name: "Your Last"
  email: "your.email@example.com"
  phone: "123-456-7890"
  linkedin: "https://linkedin.com/in/yourprofile"

education:
  - school: "Your University"
    degree: "M.S./B.A."
    field: "Your Major"
    year: "2025"

experience:
  - title: "Your Title"
    company: "Your Company"
    description: "Your achievements..."
```

### Target Jobs (`config/job_targets.json`)

```json
{
  "targets": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "platform": "linkedin/greenhouse/workday",
      "url": "https://..."
    }
  ]
}
```

## 🎮 Usage

### Apply to Target Jobs

```bash
# Apply to all configured targets
python3 auto_apply_all.py

# Apply with specific settings
python3 auto_apply_all.py --max-jobs 10 --headless
```

### Platform-Specific

```bash
# LinkedIn Easy Apply
python3 linkedin_easy_apply_fixed.py \
  --keywords "Creative Technologist" \
  --location "New York" \
  --max-jobs 5

# Greenhouse/Lever
python3 greenhouse_auto_apply_fixed.py \
  --url "https://jobs.lever.co/company/job-id"

# Workday
python3 workday_auto_apply_fixed.py \
  --company "Disney" \
  --email "your@email.com" \
  --password "your-password"
```

## 🧪 Testing

```bash
# Run all tests
python3 test_system.py

# Test specific platform
python3 test_linkedin.py
python3 test_greenhouse.py
```

## 📊 Monitoring

- **Logs**: Check `logs/` directory for detailed application logs
- **Screenshots**: Check `screenshots/` for visual debugging
- **Reports**: Check `test_reports/` for test results

## ⚠️ Important Notes

1. **Rate Limiting**: Built-in delays to avoid being flagged as bot
2. **Privacy**: Never commit credentials to git
3. **Legal**: Use responsibly and in accordance with platform ToS
4. **Monitoring**: Always review applications before final submission

## 🤝 Contributing

This is a personal project for job search automation. Feel free to fork and customize for your needs.

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with Selenium WebDriver
- AI vision powered by Gemini/Claude
- Inspired by the need for efficient job searching

---

**⚡ Pro Tip**: Start with `--max-jobs 1` to test the flow, then scale up once confirmed working!
